eyeblog-wiki
============

Eyeblog's wiki service looks up the closest Wikipedia article and posts it to your Glass timeline.

In addition to the included code, you need two more things. First, a config file containing the Google Glass Mirror API
credentials. This file should be called "config.py" and should contain two string assignments, like this:
client_id = '6600000000017.apps.googleusercontent.com'
client_secret = 'TdxxxxxxxxxxxxxxxxA5'

In addition, you will need a folder called "security" which is writable by your web server. In my case I did these two commands:
mkdir security
chown www-data security

http://google.com/+RussellNelson


