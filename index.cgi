#!/usr/bin/python

# Apache License 2.0 incorporated by reference

""" We come in here several ways. First, with nothing. When we get nothing,
we present them with the introductory user interface, which explains what
they're signing up for. If they submit "Sign me up", we send them off to
the redirect page, possibly with approval_prompt=force&

Second, they could come in with a code and state. That's when they've asked
to sign up, and we've gotten their assent.

Third, they could come back in with a userToken, which is a request for
a notify.
"""

debug = True

import uuid
import config
import re
import os
import sys
import json
import urllib2
import urllib
import urlparse
import cgi
import cgitb
import Cookie

cgitb.enable()

# Oauth2 is explained here:
# https://developers.google.com/accounts/docs/OAuth2WebServer
#
# Adding HTTP DELETE to urllib2:
# http://stackoverflow.com/questions/4511598/how-to-make-http-delete-method-using-urllib2
#
# urllib2 and json
# http://stackoverflow.com/questions/3290522/urllib2-and-json
#
# Google APIs
# https://code.google.com/apis/console/
#

C = Cookie.SmartCookie()

def first_visit(security):
    new_security = False
    if not security:
        new_security = True
        security = str(uuid.uuid4())
    C["security"] = security
    open('security/' + security, 'w')

    print "Content-Type: text/html"
    print C
    print

    state = {
        'security_token': security,
        'url': 'https://eyeblog.russnelson.com/wiki/',
        }

    scopes = ['https://www.googleapis.com/auth/glass.timeline',
              'https://www.googleapis.com/auth/glass.location',
              'https://www.googleapis.com/auth/userinfo.profile',
             ]

    url = 'https://accounts.google.com/o/oauth2/auth'

    params = {
        'client_id': config.client_id,
        'response_type': 'code',
        'access_type': 'offline',
        'scope': ' '.join(scopes),
        'redirect_uri': 'https://eyeblog.russnelson.com/wiki/index.cgi',
        'state': urllib.urlencode(state)
    }

    print "<html><head></head><body>"
    print "Hi. Welcome to the eyeblog wiki service! We'll get your location whenever the Glass Mirror API reports it to us, look up the Wikipedia article closest"
    print "to you, fetch the first few lines, and post them to your timeline. Note: it won't repeat the last article it posted."
    print "<!--",new_security,"-->"
    print "<!--",security,"-->"
    print '<form action="%s">' % url
    for k,v in params.items():
        print '<input type="hidden" name="%s" value="%s"/>' % (k,v)
    #print '<input type="checkbox" name="approval_prompt" value="force">'
    print '<input type="submit" value="I want to give permission"/>'
    print '</form>'
    print '</body></html>'

form = cgi.FieldStorage()
security = None
if 'HTTP_COOKIE' in os.environ:
    C.load(os.environ['HTTP_COOKIE'])
    security = C['security'].value
if "state" not in form or "code" not in form:
    first_visit(security)
    sys.exit()

print "Content-Type: text/html\n"
print "<head><title>Wiki Locations</title></head>\n<body>"

if "error" in form:
    error = form["error"].value
    print "Alas, something has gone wrong."
    if error == "access_denied":
        print "You chose not to give this application the privileges it needs to run. If that's not what you intended, go back and accept. Thanks for visiting."
    else:
        print "This is the error that was returned: '%s'" % error
    sys.exit()

for k in form.keys():
    print "<!--",k,"=",form[k].value,"-->"
if "submit" in form:
    data = { 'callbackUrl': 'https://eyeblog.russnelson.com/wiki/notify.cgi',
             'userToken': security,
             'collection': 'locations',
    }
    data_j = json.dumps(data)

    if form["submit"].value == "Start":
        url = """https://www.googleapis.com/mirror/v1/subscriptions?
access_token=%s""".replace('\n', '') % form['access_token'].value
        print "<!--",url, data, data_j,"-->"
        req = urllib2.Request(url, data_j, {'Content-Type': 'application/json'})

    elif form["submit"].value == "Stop":
        url = """https://www.googleapis.com/mirror/v1/subscriptions/locations?
access_token=%s""".replace('\n', '') % form['access_token'].value
        print "<!--",url, data, data_j,"-->"
        req = urllib2.Request(url, data_j, {'Content-Type': 'application/json'})
        req.get_method = lambda: 'DELETE'

    result = urllib2.urlopen(req).read()
    print "<!-- start/stop result",result,"-->"
    print "Done, thanks."
    sys.exit(0)

states = dict(urlparse.parse_qsl(form["state"].value))
if "security_token" not in states or "url" not in states:
    print "Didn't get the security_token and url in states."
    sys.exit()
code = form["code"].value

if debug:
    print "<!--Code:", code,"-->"
    print "<!--Env:", os.environ,"-->"
    print "<!--State:", states,"-->"

if security != states['security_token']:
    print "Security token doesn't match cookie."
    sys.exit()

security = states['security_token']
if debug: print "<!--Security:",security,"-->"
if (states['url'] != 'https://eyeblog.russnelson.com/wiki/' or
    not os.path.exists("security/" + security)):
        print "Security not matched"
        sys.exit()

url = "https://accounts.google.com/o/oauth2/token"
data = {}

data['code'] = code
data['client_id'] = config.client_id
data['redirect_uri'] = 'https://eyeblog.russnelson.com/wiki/index.cgi'
data['grant_type'] = 'authorization_code'

if debug:
    print "<!--url:",url,"-->"
    print "<!--data:",urllib.urlencode(data),"-->"
data['client_secret'] = config.client_secret

result = urllib2.urlopen(url, urllib.urlencode(data)).read()
results = json.loads(result)
if debug: print "<!--results:", results,"-->"

if 'refresh_token' in results:
    open("security/" + security + ".refresh", "w").write(results['refresh_token'])
open("security/" + security, "w").write(result)

print 
print """
Hi. Welcome to the eyeblog wiki service! We'll get your location whenever the Glass Mirror API reports it to us, look up the Wikipedia article closest
to you, fetch the first few lines, and post them to your timeline. Note: it won't repeat the last article it posted.
<a href="http://google.com/+RussellNelson/">Problems?</a><br>
<form action="/wiki/index.cgi">
 <input type="hidden" value="%s" name="access_token">
 <input type="hidden" value="%s" name="security">
 <input type="hidden" value="code" name="code">
 <input type="hidden" value="state" name="state">
 <input type="hidden" value="https://eyeblog.russnelson.com/wiki/notify.cgi" name="callbackUrl">
 <button type="submit" value="Start" name="submit">Start</button>
 <button type="submit" value="Stop" name="submit">Stop</button>
</form>
</body></html>
""" % (results["access_token"], security)

