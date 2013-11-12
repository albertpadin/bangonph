import os
from settings import SETTINGS
from settings import SECRET_SETTINGS
import urllib, logging
from google.appengine.api import urlfetch

settings = SETTINGS.copy()
secret_settings = SECRET_SETTINGS.copy()

def generate_login_url(state, redirect, app_id = settings["fb_id"], scope = settings["fb_permissions"]):
    """https://www.facebook.com/dialog/oauth?
    client_id=YOUR_APP_ID
   &redirect_uri=YOUR_REDIRECT_URI
   &scope=COMMA_SEPARATED_LIST_OF_PERMISSION_NAMES
   &state=SOME_ARBITRARY_BUT_UNIQUE_STRING"""

    if not "http" in redirect:
        #add http
        redirect = "http://" + os.environ["HTTP_HOST"] + redirect

    url = "https://www.facebook.com/dialog/oauth"
    url += "?client_id=" + str(app_id)
    url += "&redirect_uri=" + str(urllib.quote(redirect,''))
    url += "&scope=" + ",".join(scope)
    url += "&state=" + str(urllib.quote(state))

    return url

def code_to_access_token(code, redirect, app_id = settings["fb_id"], app_secret = secret_settings["fb_secret"]):
    """https://graph.facebook.com/oauth/access_token?
    client_id=YOUR_APP_ID
   &redirect_uri=YOUR_REDIRECT_URI
   &client_secret=YOUR_APP_SECRET
   &code=CODE_GENERATED_BY_FACEBOOK"""

    if not "http" in redirect:
        #add http
        redirect = "http://" + os.environ["HTTP_HOST"] + redirect

    url = "https://graph.facebook.com/oauth/access_token"
    url += "?client_id=" + str(app_id)
    url += "&redirect_uri=" + urllib.quote(redirect, '')
    url += "&client_secret=" + str(app_secret)
    url += "&code=" + code

    result = urlfetch.fetch(url)
    if result.status_code == 200:
        return parse_access_code(result.content)
    else:
        logging.critical(str(result.status_code))
        logging.critical(str(result.content))
        return None


def extract(raw_string, start_marker, end_marker):
    start = raw_string.index(start_marker) + len(start_marker)
    end = raw_string.index(end_marker, start)
    return raw_string[start:end]
    

def parse_access_code(response):
    return extract(response, "access_token=","&expires")


def send_notification(user_id, href, template, ref="GENERAL", access_token = secret_settings['fb_app_access_token']):
    href = "fbnotification?redirect=" + "http://" + os.environ["HTTP_HOST"] + href
    url = "https://graph.facebook.com/" + str(user_id) + "/notifications?access_token=" + access_token + "&href=" + urllib.quote(href, '')
    url += "&template=" + urllib.quote(template, '')
    result = urlfetch.fetch(url, method=urlfetch.POST)
    if result.status_code == 200:
        logging.debug("CONTENT: " + result.content)
        return True
    else:
        logging.critical(str(result.status_code))
        logging.critical(str(result.content))
        return False

