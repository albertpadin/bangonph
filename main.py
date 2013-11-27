import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import webapp2, jinja2, os, calendar
from webapp2_extras import routes
from models import User, Contact, Location, Post, Distribution, File, Distributor, Subscriber, DropOffCenter, LocationRevision, LocationRevisionChanges, DistributionRevision, Contributor, FBUser
from functions import *
import json as simplejson
import logging
import urllib
import time
import uuid
import datetime
import hashlib
import base64
import facebook
import pusher
import csv
from oauth_models import *
from cStringIO import StringIO

from google.appengine.api import taskqueue
from google.appengine.api import urlfetch
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import files
from google.appengine.api import images
from google.appengine.api import memcache

from settings import SETTINGS, API_RESPONSE, API_RESPONSE_DATA
from settings import SECRET_SETTINGS
from settings import OAUTH_RESP, API_OAUTH_RESP
from settings import DATES

from google.appengine.datastore.datastore_query import Cursor

jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)), autoescape=True)


def get_current_date():
    now = datetime.datetime.now() + datetime.timedelta(hours=8)
    return now.strftime("%m/%d/%Y")


def add_contribution(fb_id, fb_email, fb_username, fb_firstname, fb_middlename, fb_lastname, location_id, location_name):
    contribution = Contributor.get_by_id(str(fb_id))
    if not contribution:
        contribution = Contributor(id=str(fb_id))
        contribution.fb_id = str(fb_id)
        contribution.fb_email = str(fb_email)
        contribution.fb_username = str(fb_username)
        contribution.fb_lastname = str(fb_lastname)
        contribution.fb_firstname = str(fb_firstname)
        contribution.fb_middlename = str(fb_middlename)
        contribution.locations = []
        contribution.locations_pretty = []
    if location_id not in contribution.locations:
        contribution.locations.append(location_id)
        contribution.locations_pretty.append(location_name)
    contribution.contributions += 1
    contribution.put()
    return


def sanitize(value):
    return value.strip().lower().replace(' ','-').replace("'","").replace('"','').replace(",","").replace('.','').replace('@','').replace('!','').replace('$','').replace('*','').replace('&','and').replace('(','').replace(')','').replace('+','plus').replace('=','').replace(':','').replace(';','').replace('<','').replace('>','').replace('/','').replace('?','').replace('~','').replace('`','').replace("#","")


def with_commas(value):
    return "{:,}".format(value)


def two_decimal(value):
    return "{:10.2f}".format(value)


def no_commas(values):
    tag_string = ""
    for value in values:
        tag_string += value + " "
    return tag_string.strip()


def prettify(ugly):
    try:
        return ugly.replace("-", " ").title()
    except:
        return ""


def to_date(date):
    date = date + datetime.timedelta(hours=8)
    return date.strftime("%B %d, %Y %I:%M%p")

def nl_to_br(text):
    return text.replace('<','&lt;').replace('>','&gt;').replace('&','&amp;').replace('\n','<br />')

def to_dash(text):
    return text.replace(" ", "-")

def to_title(text):
    return text.title()

def slugify(text):
    text = str(text)
    return text.replace(' ','').replace('"',"").replace("'","").lower()

jinja_environment.filters['nl_to_br'] = nl_to_br
jinja_environment.filters['slugify'] = slugify
jinja_environment.filters['two_decimal'] = two_decimal
jinja_environment.filters['no_commas'] = no_commas
jinja_environment.filters['prettify'] = prettify
jinja_environment.filters['with_commas'] = with_commas
jinja_environment.filters['to_date'] = to_date
jinja_environment.filters['to_dash'] = to_dash
jinja_environment.filters['to_title'] = to_title


def login_required(fn):
    '''So we can decorate any RequestHandler with #@login_required'''
    def wrapper(self, *args):
        if not self.user:
            self.redirect(self.uri_for('www-login', referred=self.request.path))
        else:
            return fn(self, *args)
    return wrapper

def admin_required(fn):
    '''So we can decorate any RequestHandler with @admin_required'''
    def wrapper(self, *args):
        if not self.user:
            self.redirect(self.uri_for('www-login'))
        elif self.user.admin:
            return fn(self, *args)
        else:
            self.redirect(self.uri_for('www-front'))
    return wrapper


def hash_password(email, password):
    i = email + password + SECRET_SETTINGS["password_salt"]
    return base64.b64encode(hashlib.sha1(i).digest())


"""Request Handlers Start Here"""

class BaseHandler(webapp2.RequestHandler):
    def __init__(self, request=None, response=None):
        self.now = datetime.datetime.now()
        self.tv = {}
        self.settings = SETTINGS.copy()
        self.initialize(request, response)
        self.has_pass = False
        self.tv["version"] = os.environ['CURRENT_VERSION_ID']
        self.local = False
        if "127.0.0.1" in self.request.uri or "localhost" in self.request.uri:
            self.local = True
        # misc
        self.tv["current_url"] = self.request.uri
        self.tv["fb_login_url"] = facebook.generate_login_url(self.request.path, self.uri_for('www-fblogin'))

        if "?" in self.request.uri:
            self.tv["current_base_url"] = self.request.uri[0:(self.request.uri.find('?'))]
        else:
            self.tv["current_base_url"] = self.request.uri

        try:
            self.tv["safe_current_base_url"] = urllib.quote(self.tv["current_base_url"])
        except:
            logging.exception("safe url error")

        self.tv["request_method"] = self.request.method

        self.session = self.get_session()
        self.user = self.get_current_user()
        self.public_user = self.get_public_current_user()
        self.public_org_user = self.get_public_current_user_orgs()


    def render(self, template_path=None, force=False, cache=0):
        self.tv["current_timestamp"] = time.mktime(self.now.timetuple())
        self.settings["current_year"] = self.now.year
        self.tv["settings"] = self.settings

        if self.request.get('error'):
            self.tv["error"] = self.request.get("error").strip()
        if self.request.get('success'):
            self.tv["success"] = self.request.get("success").strip()
        if self.request.get('warning'):
            self.tv["warning"] = self.request.get("warning").strip()

        if self.user:
            self.tv["user"] = self.user.to_object()

        if self.request.get('json') or not template_path:
            self.response.out.write(simplejson.dumps(self.tv))
            return

        template = jinja_environment.get_template(template_path)
        output = template.render(self.tv)
        if cache:
            try:
                memcache.set(str(self.tv['version']) + ':path:' + self.tv['current_url'], output, cache)
            except:
                logging.exception('memcache error...')
        self.response.out.write(output)


    def get_session(self):
        from gaesessions import get_current_session
        return get_current_session()


    def get_current_user(self):
        if self.session.has_key("user"):
            user = User.get_by_id(self.session["user"])
            return user
        else:
            return None

    def get_public_current_user(self):
        if self.session.has_key("user"):
            user = FBUser.get_by_id(self.session["user"])
            return user
        else:
            return None

    def get_public_current_user_orgs(self):
        if self.session.has_key("user"):
            user = FBUser.get_by_id(self.session["user"])
            return user
        else:
            return None

    def login(self, user):
        self.session["user"] = user.key.id()
        return

    def login_fb(self, fb_content, access_token):
        self.logout()
        user = User.query(User.fb_id == fb_content["id"]).get()
        if not user:
            email = fb_content["email"]
            if email:
                user = User.query(User.email == email).get()

            if user:
                # Merge User

                user.fb_id = fb_content["id"]
                try:
                    user.fb_username = fb_content["username"]
                except:
                    logging.exception("no username?")
                user.first_name = fb_content["first_name"]
                try:
                    user.last_name = fb_content["last_name"]
                except:
                    logging.exception("no last_name?")
                try:
                    user.middle_name = fb_content["middle_name"]
                except:
                    logging.exception('no middle name?')

                user.name = user.first_name
                if user.middle_name:
                    user.name += " " + user.middle_name

                if user.last_name:
                    user.name += " " + user.last_name

                try:
                    user.fb_access_token = access_token
                except:
                    logging.exception('no access token')
            else:
                user = User()
                user.fb_id = fb_content["id"]
                try:
                    user.fb_username = fb_content["username"]
                except:
                    logging.exception("no username?")
                user.email = fb_content["email"]
                user.first_name = fb_content["first_name"]
                try:
                    user.last_name = fb_content["last_name"]
                except:
                    logging.exception("no last_name?")
                try:
                    user.middle_name = fb_content["middle_name"]
                except:
                    logging.exception('no middle name?')

                user.name = user.first_name
                if user.middle_name:
                    user.name += " " + user.middle_name

                if user.last_name:
                    user.name += " " + user.last_name

                try:
                    user.fb_access_token = access_token
                except:
                    logging.exception('no access token')

            user.put()
        self.login(user)
        return

    def public_login_fb(self, fb_content, access_token, state_url):
        self.logout()
        user = FBUser.get_by_id(str(fb_content["id"]))
        if not user:
            user = FBUser(id=str(fb_content["id"]))
            user.fb_id = fb_content["id"]
            try:
                user.fb_email = fb_content["email"]
            except:
                logging.exception('no email')
            try:
                user.fb_username = fb_content["username"]
            except:
                logging.exception("no username?")
            user.fb_firstname = fb_content["first_name"]
            try:
                user.fb_lastname = fb_content["last_name"]
            except:
                logging.exception("no last_name?")
            try:
                user.fb_middlename = fb_content["middle_name"]
            except:
                logging.exception('no middle name?')

            user.fb_name = user.fb_firstname
            if user.fb_middlename:
                user.fb_name += " " + user.fb_middlename

            if user.fb_lastname:
                user.fb_name += " " + user.fb_lastname

            try:
                user.fb_access_token = access_token
            except:
                logging.exception('no access token')
            user.put()
        self.login(user)


    def logout(self):
        if self.session.is_active():
            self.session.terminate()
            return


    def iptolocation(self):
        country = self.request.headers.get('X-AppEngine-Country')
        logging.info("COUNTRY: " + str(country))
        if country == "GB":
            country = "UK"
        if country == "ZZ":
            country = ""
        if country is None:
            country = ""
        return country

class Logout(BaseHandler):
    def get(self):
        if self.user:
            self.logout()
        self.redirect(self.uri_for('www-front', referred="logout"))

class PublicLogout(BaseHandler):
    def get(self):
        if self.public_user:
            id = self.public_user.name
            if id:
                self.logout()
                self.redirect("/locations/" + str(id))
            else:
                self.logout()
                self.redirect("/")
        else:
            if self.public_org_user:
                self.logout()
                self.redirect("/orgs")
            else:
                self.logout()
                self.redirect("/")

class LoginPage(BaseHandler):
    def get(self):
        if self.request.get("id") and self.request.get("redirect"):
            self.tv["id"] = self.request.get("id")
            self.tv["redirect"] = self.request.get("redirect")
            self.render('frontend/remote-login.html')
        else:
            self.redirect(self.uri_for('www-front'))

    def post(self):
        if self.request.get("id") and self.request.get("redirect"):
            client_id = self.request.get("id")
            redirect = self.request.get("redirect")
            if self.request.get("email") and self.request.get("password"):
                email = self.request.get("email")
                password = self.request.get("password")
                user = User.get_by_id(email)

                if not user:
                    self.redirect('/login?id=' + client_id + '&redirect=' + redirect)
                    return

                logging.info("asdasdasd")
                if user.password == hash_password(email, password):
                    from oauth import AuthorizationProvider as provider
                    self.provider = provider()
                    response = self.provider.get_authorization_code(client_id, email, redirect)
                    if response.status_code == 200:
                        self.redirect(response.headers['Location'])
                    else:
                        pass
                else:
                    pass
        else:
            temp = {}
            body = self.request.body
            if body:
                details = simplejson.loads(body)

                if details["email"] and details["password"]:
                    user = User.get_by_id(details["email"])

                    if not user:
                        if details["email"] == "admin@sym.ph" and details["password"] == "1234567890asd":
                            user = User(id=details["email"])
                            user.email = details["email"]
                            user.name = "symph admin"
                            user.password = hash_password(details["email"], details["password"])
                            user.put()
                        else:
                            temp["success"] = False
                            temp["message"] = "User not found. Please try another email or register."
                            self.response.out.write(simplejson.dumps(temp))
                            return

                    if user.password == hash_password(details["email"], details["password"]):
                        self.login(user)
                        temp["success"] = True
                        temp["message"] = "User authenticated!"
                        self.response.out.write(simplejson.dumps(temp))
                    else:
                        temp["success"] = False
                        temp["message"] = "Wrong password. Please try again."
                        self.response.out.write(simplejson.dumps(temp))


class PublicFrontPage(BaseHandler):
    def get(self):
        output = memcache.get(str(self.tv['version']) + ':path:' + self.tv['current_url'])
        if output:
            self.response.write(output)
            return

        self.tv["current_page"] = "PUBLIC_FRONT"
        featured_locations = []
        locations = Location.query().fetch(300)
        for location in locations:
            if location.featured:
                featured_locations.append(location)
                locations.remove(location)

        self.tv['featured_locations'] = []
        self.tv['locations'] = []

        update_count = memcache.get('update_count')
        if not update_count:
            try:
                update_count = len(LocationRevisionChanges.query(LocationRevisionChanges.created >= (datetime.datetime.now() - datetime.timedelta(hours=8))).fetch(500, keys_only=True))
                memcache.set('update_count', update_count, 300)
            except:
                update_count = 0
                logging.exception("error in retrieving changes count")

        self.tv['update_count'] = update_count

        for location in locations:
            self.tv['locations'].append(location.to_object(show_relief=True))

        for featured_location in featured_locations:
            self.tv['featured_locations'].append(featured_location.to_object(show_relief=True))

        user_changes = LocationRevisionChanges.query().order(-LocationRevisionChanges.created).fetch(25)
        if user_changes:
            self.tv["revisions"] = user_changes

        try:
            self.tv['contributors'] = Contributor.query().order(-Contributor.contributions).fetch(10)
        except:
            logging.exception("contributors")
            self.tv['contributors'] = []

        self.render('frontend/public-front.html', cache=30)


class PublicUpdatesPage(BaseHandler):
    def get(self):
        self.tv["current_page"] = "PUBLIC_UPDATES"
        self.tv['updates'] = []

        updates = LocationRevisionChanges.query().order(-LocationRevisionChanges.created).fetch(100)
        if updates:
            self.tv['updates'] = updates
        self.tv['update_count'] = len(updates)

        self.render('frontend/updates-stream.html')


class LocationSamplePage(BaseHandler):
    def get(self):
        self.tv["current_page"] = "LOCATIONSAMPLE"
        self.render('frontend/locationsample.html')

class PublicFBLoginPage(BaseHandler):
    def get(self):
        if self.request.get('code') and self.request.get('state'):
            state = self.request.get('state')
            code = self.request.get('code')
            access_token = facebook.code_to_access_token(code, self.uri_for('www-publicfblogin'))
            if not access_token:
                # Assume expiration, just redirect to login page
                self.redirect(self.uri_for('www-locations', referred="publicfblogin", error="We were not able to connect with Facebook. Please try again."))
                return

            url = "https://graph.facebook.com/me?access_token=" + access_token

            result = urlfetch.fetch(url)
            if result.status_code == 200:
                state_url = str(state).split("/")[2]
                self.public_login_fb(simplejson.loads(result.content), access_token, state_url)
                self.redirect(str(state))
                return

        else:
            self.redirect(facebook.generate_login_url(self.request.get('goto'), self.uri_for('www-publicfblogin')))

class PublicLocationEditPage(BaseHandler):
    def get(self, location_id=None):
        if self.public_user:
            if not location_id:
                logging.error('No location ID')
                self.redirect('/')
                return

            location = Location.get_by_id(location_id)
            if not location:
                logging.error('No location found')
                self.redirect('/')
                return

            self.tv['efforts'] = Distribution.query(Distribution.destinations == location.key, Distribution.date_of_distribution >= datetime.datetime.now()).order(Distribution.date_of_distribution)

            self.tv['location'] = location
            self.tv['page_title'] = location.name
            self.tv["location_id"] = location.key.id()

            # location revision
            self.tv["login_user"] = self.public_user.fb_name

            self.render('frontend/public-location-edit.html')
        else:
            path = self.request.path.split("/")[0] + "/" + self.request.path.split("/")[1]
            # self.response.out.write("You are not allowed to visit this site. Click <a href='"+ path +"'>here</a> to go back.")
            path_facebook = facebook.generate_login_url(path, self.uri_for('www-publicfblogin'))
            self.redirect(path_facebook)

    def post(self, *args, **kwargs):
        if self.request.get("status") == "status":
            location_revision = LocationRevision()
            temp = {}
            datas_death = []

            temp["death_count"] = self.request.get("death_count")
            temp["updated"] = str(datetime.datetime.now())
            datas_death.append(temp)
            location_revision.death = datas_death

            datas_affected = []

            temp["affected_count"] = self.request.get("affected_count")
            temp["updated"] = str(datetime.datetime.now())
            datas_affected.append(temp)
            location_revision.affected = datas_affected

            datas_missing = []

            temp["missing_person"] = self.request.get("missing_person")
            temp["updated"] = str(datetime.datetime.now())
            datas_missing.append(temp)
            location_revision.missing_person = datas_missing

            datas_status = []

            temp["communication"] = self.request.get("status_communication")
            temp["water"] = self.request.get("status_water")
            temp["power"] = self.request.get("status_power")
            temp["medicines"] = self.request.get("status_medicines")
            temp["food"] = self.request.get("status_food")
            temp["cloths"] = self.request.get("status_cloths")
            temp["shelter"] = self.request.get("status_shelter")
            temp["updated"] = str(datetime.datetime.now())
            datas_status.append(temp)
            location_revision.status = datas_status

            datas_levels = []
            if self.request.get('levels_food'):
                temp["food"] = int(self.request.get("levels_food"))
            else:
                temp["food"] = 0
            if self.request.get('levels_hygiene'):
                temp["hygiene"] = int(self.request.get("levels_hygiene"))
            else:
                temp["hygiene"] = 0
            if self.request.get('levels_medicine'):
                temp["medicine"] = int(self.request.get("levels_medicine"))
            else:
                temp["medicine"] = 0
            if self.request.get('levels_medical_mission'):
                temp["medical_mission"] = int(self.request.get("levels_medical_mission"))
            else:
                temp["medical_mission"] = 0
            if self.request.get('levels_shelter'):
                temp["shelter"] = int(self.request.get("levels_shelter"))
            else:
                temp["shelter"] = 0
            temp["updated"] = str(datetime.datetime.now())
            datas_levels.append(temp)
            location_revision.levels = datas_levels

            location_revision.put()

            user_changes = LocationRevisionChanges()
            user_changes.fb_email = self.public_user.fb_email
            user_changes.fb_id = self.public_user.fb_id
            user_changes.fb_access_token = self.public_user.fb_access_token
            user_changes.fb_username = self.public_user.fb_username
            user_changes.fb_lastname = self.public_user.fb_lastname
            user_changes.fb_firstname = self.public_user.fb_firstname
            user_changes.fb_middlename = self.public_user.fb_middlename
            user_changes.fb_name = self.public_user.fb_name
            user_changes.name = self.request.get("page_title")
            user_changes.revision_type = "Updated Location Status"

            location = Location.get_by_id(self.request.get("page_title"))
            if location:
                status = {
                    "power": self.request.get("status_power"),
                    "water": self.request.get("status_water"),
                    "medicines": self.request.get("status_medicines"),
                    "cloths": self.request.get("status_cloths"),
                    "communication": self.request.get("status_communication"),
                    "food": self.request.get("status_food"),
                    "shelter": self.request.get("status_shelter")
                }
                levels = {
                    "food": temp["food"],
                    "hygiene": temp["hygiene"],
                    "medicine": temp["medicine"],
                    "medical_mission": temp["medical_mission"],
                    "shelter": temp["shelter"]
                }

                datas_changes = []
                if location.status_board != self.request.get("status_board"):
                    datas_changes.append("Status Board")

                try:
                    if location.death_count != int(self.request.get("death_count")):
                        datas_changes.append("Death Count: " + str(location.death_count) + " >> " + str(self.request.get("death_count")))
                except:
                    logging.exception("passing...")
                try:
                    if location.affected_count != int(self.request.get("affected_count")):
                        datas_changes.append("Affected Count: " + str(location.affected_count) + " >> " + str(self.request.get("affected_count")))
                except:
                    logging.exception("passing...")
                try:
                    if location.missing_person != int(self.request.get("missing_person")):
                        datas_changes.append("Missing Count: " + str(location.missing_person) + " >> " + str(self.request.get("missing_person")))
                except:
                    logging.exception("passing...")
                if location.death_count_text != self.request.get("death_count_text"):
                    datas_changes.append("Deaths: " + str(location.death_count_text) + " >> " + str(self.request.get("death_count_text")))
                if location.affected_count_text != self.request.get("affected_count_text"):
                    datas_changes.append("Affected: " + str(location.affected_count_text) + " >> " + str(self.request.get("affected_count_text")))
                if location.missing_person_text != self.request.get("missing_person_text"):
                    datas_changes.append("Missing: " + str(location.missing_person_text) + " >> " + str(self.request.get("missing_person_text")))
                if location.status:
                    if status["power"] != location.status["power"]:
                        datas_changes.append("Power: " + location.status["power"] + " >> " + status["power"])
                    if status["water"] != location.status["water"]:
                        datas_changes.append("Water: " + location.status["water"] + " >> " + status["water"])
                    if status["medicines"] != location.status["medicines"]:
                        datas_changes.append("Medicines: " + location.status["medicines"] + " >> " + status["medicines"])
                    if status["cloths"] != location.status["cloths"]:
                        datas_changes.append("Clothing: " + location.status["cloths"] + " >> " + status["cloths"])
                    if status["communication"] != location.status["communication"]:
                        datas_changes.append("Communication: " + location.status["communication"] + " >> " + status["communication"])
                    if status["food"] != location.status["food"]:
                        datas_changes.append("Food: " + location.status["food"] + " >> " + status["food"])
                date = get_current_date()
                if location.current_levels:
                    if levels["food"] != location.current_levels["food"]:
                        datas_changes.append("Food & Water: " + str(location.current_levels["food"]) + " >> " + str(levels["food"]))
                    if levels["hygiene"] != location.current_levels["hygiene"]:
                        datas_changes.append("Hygiene: " + str(location.current_levels["hygiene"]) + " >> " + str(levels["hygiene"]))
                    if levels["medicine"] != location.current_levels["medicine"]:
                        datas_changes.append("Medicine: " + str(location.current_levels["medicine"]) + " >> " + str(levels["medicine"]))
                    if levels["medical_mission"] != location.current_levels["medical_mission"]:
                        datas_changes.append("Medical Mission: " + str(location.current_levels["medical_mission"]) + " >> " + str(levels["medical_mission"]))
                    if levels["shelter"] != location.current_levels["shelter"]:
                        datas_changes.append("Shelter: " + str(location.current_levels["shelter"]) + " >> " + str(levels["shelter"]))

                if self.request.get("source"):
                    datas_changes.append("Source/s: " + self.request.get('source'))

                user_changes.status = datas_changes
                user_changes.put()

                try:
                    location.death_count = int(self.request.get("death_count"))
                except:
                    logging.exception("passing...")
                location.death_count_text = self.request.get("death_count_text")
                try:
                    location.affected_count = int(self.request.get("affected_count"))
                except:
                    logging.exception("passing...")
                location.affected_count_text = self.request.get("affected_count_text")
                try:
                    location.missing_person = int(self.request.get("missing_person"))
                except:
                    logging.exception("passing...")
                location.missing_person_text = self.request.get("missing_person_text")
                location.status_board = self.request.get("status_board")
                location.status = status
                location.current_levels = levels
                location.put()

                p = pusher.Pusher(
                  app_id='59383',
                  key='e0a2a1c8316b9baddc9b',
                  secret='474177f7aea8c983a7d1'
                )
                user_name = ""
                if user_changes.fb_firstname:
                    user_name += user_changes.fb_firstname
                if user_changes.fb_middlename:
                    user_name += " " + user_changes.fb_middlename
                if user_changes.fb_lastname:
                    user_name += " " + user_changes.fb_lastname

                p['feeds'].trigger('new_revision', {
                    "changes": "; ".join(datas_changes),
                    "location": location.key.id(),
                    "fb_id": user_changes.fb_id,
                    "fb_name": user_name,
                    "revision_type": 'Updated Location Status',
                    "created": to_date(user_changes.created)
                    })

                memcache.incr('update_count')
                params = {
                    "location_id": location.key.id()
                }
                taskqueue.add(url='/admin/tasks/compute_relief_status', params=params, method='POST')

                add_contribution(user_changes.fb_id, user_changes.fb_email, user_changes.fb_username, user_changes.fb_firstname, user_changes.fb_middlename, user_changes.fb_lastname, location.key.id(), location.name)

            self.redirect("/locations/" + self.request.get("page_title") + "/edit?success=Successfully+updated.")

        if self.request.get("status") == "reliefs":
            if self.request.get('relief_name'):
                distribution_revision = DistributionRevision()
                distribution_revision.fb_email = self.public_user.fb_email
                distribution_revision.fb_id = self.public_user.fb_id
                distribution_revision.fb_access_token = self.public_user.fb_access_token
                distribution_revision.fb_username = self.public_user.fb_username
                distribution_revision.fb_lastname = self.public_user.fb_lastname
                distribution_revision.fb_firstname = self.public_user.fb_firstname
                distribution_revision.fb_middlename = self.public_user.fb_middlename
                distribution_revision.fb_name = self.public_user.fb_name
                distribution_revision.name = self.request.get("page_title")
                distribution_revision.relief_name = self.request.get("relief_name")
                distribution_revision.destination = self.request.get("destination")
                distribution_revision.num_of_packs = int(self.request.get("packs"))
                distribution_revision.description = self.request.get("description")
                distribution_revision.contacts = self.request.get("contacts")
                distribution_revision.needs = self.request.get("needs")
                distribution_revision.date = self.request.get("date")
                distribution_revision.tag = self.request.get("tag")
                distribution_revision.status = self.request.get("status_")
                distribution_revision.put()

                user_changes = LocationRevisionChanges()
                user_changes.fb_email = self.public_user.fb_email
                user_changes.fb_id = self.public_user.fb_id
                user_changes.fb_access_token = self.public_user.fb_access_token
                user_changes.fb_username = self.public_user.fb_username
                user_changes.fb_lastname = self.public_user.fb_lastname
                user_changes.fb_firstname = self.public_user.fb_firstname
                user_changes.fb_middlename = self.public_user.fb_middlename
                user_changes.fb_name = self.public_user.fb_name
                user_changes.name = self.request.get("page_title")
                user_changes.revision_type = "Added a New Relief Effort"
                datas_changes = []
                if self.request.get("relief_name"):
                    datas_changes.append("Relief Effort: " + distribution_revision.name)
                if self.request.get("destination"):
                    datas_changes.append("Destination: " + distribution_revision.destination)
                if self.request.get("packs"):
                    datas_changes.append("Packs: " + str(distribution_revision.num_of_packs))
                if self.request.get("description"):
                    datas_changes.append("Description: " + distribution_revision.description)
                if self.request.get("contacts"):
                    datas_changes.append("Contacts: " + distribution_revision.contacts)
                if self.request.get("needs"):
                    datas_changes.append("Needs: " + distribution_revision.needs)
                if self.request.get("date"):
                    datas_changes.append("Date: " + distribution_revision.date)
                if self.request.get("source"):
                    datas_changes.append("Source: " + self.request.get('source'))
                if self.request.get("tag"):
                    datas_changes.append("Tag: " + str(distribution_revision.tag))
                if self.request.get("status_"):
                    datas_changes.append("Status: " + self.request.get("status_"))
                user_changes.status = datas_changes
                user_changes.put()

                p = pusher.Pusher(
                  app_id='59383',
                  key='e0a2a1c8316b9baddc9b',
                  secret='474177f7aea8c983a7d1'
                )
                user_name = ""
                if user_changes.fb_firstname:
                    user_name += user_changes.fb_firstname
                if user_changes.fb_middlename:
                    user_name += " " + user_changes.fb_middlename
                if user_changes.fb_lastname:
                    user_name += " " + user_changes.fb_lastname

                p['feeds'].trigger('new_revision', {
                    "changes": "; ".join(datas_changes),
                    "location": distribution_revision.name,
                    "fb_id": user_changes.fb_id,
                    "fb_name": user_name,
                    "revision_type": 'Added a New Relief Effort',
                    "created": to_date(user_changes.created)
                    })

                memcache.incr('update_count')

                params = {
                    "location_id": distribution_revision.name
                }
                taskqueue.add(url='/admin/tasks/compute_relief_status', params=params, method='POST')

                add_contribution(user_changes.fb_id, user_changes.fb_email, user_changes.fb_username, user_changes.fb_firstname, user_changes.fb_middlename, user_changes.fb_lastname, self.request.get("page_title"), self.request.get("page_title_pretty"))

                self.redirect("/locations/" + self.request.get("page_title") + "/edit?success=Successfully+updated.")
            else:
                self.redirect("/locations/" + self.request.get("page_title") + "/edit?error=Please%20fill%20all%20required%20information.")

class PublicLocationPage(BaseHandler):
    def get(self, location_id=None):
        if not location_id:
            logging.error('No location ID')
            self.redirect('/')
            return

        location = Location.get_by_id(location_id)
        if not location:
            logging.error('No location found')
            self.redirect('/')
            return

        self.tv['efforts'] = Distribution.query(Distribution.destinations == location.key, Distribution.date_of_distribution >= datetime.datetime.now()).order(Distribution.date_of_distribution)

        self.tv['location'] = location.to_object(show_relief=True)
        self.tv['page_title'] = location.name
        self.tv['location_id'] = location.key.id()
        path_redirect = self.request.path + "/edit"
        self.tv["fb_login_url"] = facebook.generate_login_url(path_redirect, self.uri_for('www-publicfblogin'))

        user_changes = LocationRevisionChanges.query(LocationRevisionChanges.name == location.key.id()).order(-LocationRevisionChanges.created).fetch(100)
        if user_changes:
            self.tv["status_changes"] = user_changes

        distribution_changes = DistributionRevision.query(DistributionRevision.name == location.key.id()).order(-DistributionRevision.created).fetch(100)
        if distribution_changes:
            self.tv["distribution_changes"] = distribution_changes

        if self.public_user:
            self.tv["fb_id"] = self.public_user.fb_id
            self.tv["fb_name"] = self.public_user.fb_name

        self.render('frontend/public-location.html')

    def post(self, location_id=None):
        if self.request.get("d_id"):
            distribution = DistributionRevision.get_by_id(int(self.request.get("d_id")))
            if distribution:
                distribution.relief_name = self.request.get("name")
                distribution.destination = self.request.get("destination")
                distribution.num_of_packs = int(self.request.get("packs"))
                distribution.description = self.request.get("description")
                distribution.contacts = self.request.get("contacts")
                distribution.needs = self.request.get("needs")
                distribution.date = self.request.get("date")
                distribution.tag = self.request.get("tag")
                distribution.status = self.request.get("status")
                distribution.put()

                user_changes = LocationRevisionChanges()
                user_changes.fb_email = self.public_user.fb_email
                user_changes.fb_id = self.public_user.fb_id
                user_changes.fb_access_token = self.public_user.fb_access_token
                user_changes.fb_username = self.public_user.fb_username
                user_changes.fb_lastname = self.public_user.fb_lastname
                user_changes.fb_firstname = self.public_user.fb_firstname
                user_changes.fb_middlename = self.public_user.fb_middlename
                user_changes.fb_name = self.public_user.fb_name
                user_changes.name = self.public_user.name
                user_changes.revision_type = "Edit Relief Effort"
                datas_changes = []
                if self.request.get("name"):
                    datas_changes.append("Relief Effort: " + self.request.get("name"))
                if self.request.get("destination"):
                    datas_changes.append("Destination: " + self.request.get("destination"))
                if self.request.get("packs"):
                    datas_changes.append("Packs: " + str(self.request.get("packs")))
                if self.request.get("description"):
                    datas_changes.append("Description: " + self.request.get("description"))
                if self.request.get("contacts"):
                    datas_changes.append("Contacts: " + self.request.get("contacts"))
                if self.request.get("needs"):
                    datas_changes.append("Needs: " + self.request.get("needs"))
                if self.request.get("date"):
                    datas_changes.append("Date: " + self.request.get("date"))
                if self.request.get("tag"):
                    datas_changes.append("Tag: " + str(self.request.get("tag")))
                if self.request.get("status"):
                    datas_changes.append("Status: " + str(self.request.get("status")))
                user_changes.status = datas_changes
                user_changes.put()

                updated = distribution.updated + datetime.timedelta(hours=8)
                self.response.out.write(simplejson.dumps({"updated": str(updated.strftime("%B %d, %Y %I:%M%p"))}))
        else:
            subscriber = Subscriber(id=self.request.get("email"))
            subscriber.email = self.request.get("email")

            if self.request.get("subscribe_location"):
                loc = Location.get_by_id(location_id)
                if loc:
                    subscriber.location = loc.key
                else:
                    logging.critical("No location selected!..")

            if self.request.get("subscribe_all"):
                subscriber.all_updates = True

            subscriber.put()
            self.redirect("/locations/"+location_id)

class OrgsHandler(BaseHandler):
    def get(self):
        self.tv["current_page"] = "ORGS"

        self.tv["main_org"] = True

        path_redirect = self.request.path + "/new-org"
        self.tv["fb_login_url"] = facebook.generate_login_url(path_redirect, self.uri_for('www-publicfblogin'))

        user_changes = LocationRevisionChanges.query().order(-LocationRevisionChanges.created).fetch(25)
        if user_changes:
            self.tv["status_changes"] = user_changes

        distributors = Distributor.query(Distributor.name != None).fetch(500)
        if distributors:
            self.tv["distributors"] = distributors

        self.render('frontend/public-orgs.html')

class OrgsNewHandler(BaseHandler):
    def get(self):
        if self.request.get("success"):
            self.tv["success"] = True

        if self.public_org_user:
            self.tv["current_page"] = "ORGS"
            self.tv["new_org"] = True

            user_changes = LocationRevisionChanges.query().order(-LocationRevisionChanges.created).fetch(100)
            if user_changes:
                self.tv["status_changes"] = user_changes

            self.render('frontend/public-orgs.html')
        else:
            path_facebook = facebook.generate_login_url(self.request.path, self.uri_for('www-publicfblogin'))
            self.redirect(path_facebook)

    def post(self):
        distributor_id = sanitize(self.request.get("org_name"))
        temp_distributor_id = distributor_id
        while True:
            count = 1
            if Distributor.query(Distributor.handle == temp_distributor_id).get(keys_only=True):
                temp_distributor_id = distributor_id + str(count)
                count += 1
            else:
                distributor = Distributor()
                break
        distributor.handle = temp_distributor_id
        distributor.logo = self.request.get("image_url")
        distributor.name = self.request.get("org_name")
        distributor.contact_num = self.request.get("contact_num")
        distributor.email = self.request.get("email")
        if "http://" in self.request.get("website") or "https://" in self.request.get("website"):
            distributor.website = self.request.get("website")
        else:
            distributor.website = "http://" + self.request.get("website")

        if "http://" in self.request.get("facebook") or "https://" in self.request.get("facebook"):
            distributor.facebook = self.request.get("facebook")
        else:
            distributor.facebook = "http://" + self.request.get("facebook")
        distributor.contact_details = self.request.get("contact_details")
        distributor.put()

        user_changes = LocationRevisionChanges()
        if self.public_org_user:
            user_changes.fb_email = self.public_org_user.fb_email
            user_changes.fb_id = self.public_org_user.fb_id
            user_changes.fb_username = self.public_org_user.fb_username
            user_changes.fb_lastname = self.public_org_user.fb_lastname
            user_changes.fb_firstname = self.public_org_user.fb_firstname
            user_changes.fb_middlename = self.public_org_user.fb_middlename
            user_changes.fb_name = self.public_org_user.fb_name
        elif self.public_user:
            user_changes.fb_email = self.public_user.fb_email
            user_changes.fb_id = self.public_user.fb_id
            user_changes.fb_username = self.public_user.fb_username
            user_changes.fb_lastname = self.public_user.fb_lastname
            user_changes.fb_firstname = self.public_user.fb_firstname
            user_changes.fb_middlename = self.public_user.fb_middlename
            user_changes.fb_name = self.public_user.fb_name
        user_changes.revision_type = "Orgs"
        datas_changes = []
        if self.request.get("org_name"):
            datas_changes.append("Org Name: " + self.request.get("org_name"))
        if self.request.get("contact_num"):
            datas_changes.append("Contact Number: " + self.request.get("contact_num"))
        if self.request.get("contact_details"):
            datas_changes.append("Contact Details: " + self.request.get("contact_details"))
        if self.request.get("email"):
            datas_changes.append("Email: " + self.request.get("email"))
        if self.request.get("website"):
            datas_changes.append("Website: " + self.request.get("website"))
        if self.request.get("facebook"):
            datas_changes.append("Facebook: " + self.request.get("facebook"))
        user_changes.status = datas_changes
        user_changes.put()

        self.redirect(self.request.path + "?success=Successfully-added.")

class OrgsViewHandler(BaseHandler):
    def get(self, *args, **kwargs):
        if kwargs["org"]:
            org_name = kwargs["org"]
            self.tv["view_org"] = True

            self.tv["original_path"] = self.request.path

            if self.public_user:
                self.tv["fb_id"] = self.public_user.fb_id
                self.tv["fb_name"] = self.public_user.fb_name
                self.tv["fb_login_url"] = self.request.path + "/new-relief"
            elif self.public_org_user:
                self.tv["fb_id"] = self.public_org_user.fb_id
                self.tv["fb_name"] = self.public_org_user.fb_name
                self.tv["fb_login_url"] = self.request.path + "/new-relief"
            else:
                path_redirect = self.request.path + "/new-relief"
                self.tv["fb_login_url"] = facebook.generate_login_url(path_redirect, self.uri_for('www-publicfblogin'))

            user_changes = LocationRevisionChanges.query().order(-LocationRevisionChanges.created).fetch(100)
            if user_changes:
                self.tv["status_changes"] = user_changes

            distributor = Distributor.query(Distributor.handle == org_name).get()
            if distributor:
                self.tv["distributor"] = distributor

                distribution_changes = DistributionRevision.query(DistributionRevision.org_id == org_name).order(-DistributionRevision.created).fetch(100)
                if distribution_changes:
                    self.tv["distribution_changes"] = distribution_changes

            self.render('frontend/public-orgs.html')

    def post(self, *args, **kwargs):
        if self.request.get("distributor_id") and self.request.get("image_url"):
            distributor = Distributor.get_by_id(int(self.request.get("distributor_id")))
            if distributor and self.request.get('image_url'):
                distributor.logo = self.request.get("image_url")
                distributor.put()
                self.response.out.write(simplejson.dumps({"image_url": self.request.get("image_url")}))


class OrgsEditHandler(BaseHandler):
    def get(self, *args, **kwargs):
        if kwargs["org"]:
            if not self.public_org_user:
                path_redirect = self.request.path
                self.redirect(facebook.generate_login_url(path_redirect, self.uri_for('www-publicfblogin')))
                return

            org_name = kwargs["org"]
            self.tv['edit_org'] = True

            self.tv["original_path"] = self.request.path

            if self.public_user:
                self.tv["fb_id"] = self.public_user.fb_id
                self.tv["fb_name"] = self.public_user.fb_name
                self.tv["fb_login_url"] = self.request.path + "/edit"
            elif self.public_org_user:
                self.tv["fb_id"] = self.public_org_user.fb_id
                self.tv["fb_name"] = self.public_org_user.fb_name
                self.tv["fb_login_url"] = self.request.path + "/edit"
            else:
                path_redirect = self.request.path + "/edit"
                self.tv["fb_login_url"] = facebook.generate_login_url(path_redirect, self.uri_for('www-publicfblogin'))

            user_changes = LocationRevisionChanges.query().order(-LocationRevisionChanges.created).fetch(100)
            if user_changes:
                self.tv["status_changes"] = user_changes

            distributor = Distributor.query(Distributor.handle == org_name).get()
            if distributor:
                self.tv["org"] = distributor

            self.render('frontend/public-orgs.html')
            return
        self.redirect('/orgs')

    def post(self, *args, **kwargs):
        if kwargs["org"]:
            if not self.public_org_user:
                path_redirect = self.request.path
                self.redirect(facebook.generate_login_url(path_redirect, self.uri_for('www-publicfblogin')))
                return

            org_name = kwargs["org"]

            if self.public_user:
                self.tv["fb_id"] = self.public_user.fb_id
                self.tv["fb_name"] = self.public_user.fb_name
                self.tv["fb_login_url"] = self.request.path + "/edit"
            elif self.public_org_user:
                self.tv["fb_id"] = self.public_org_user.fb_id
                self.tv["fb_name"] = self.public_org_user.fb_name
                self.tv["fb_login_url"] = self.request.path + "/edit"
            else:
                path_redirect = self.request.path + "/edit"
                self.tv["fb_login_url"] = facebook.generate_login_url(path_redirect, self.uri_for('www-publicfblogin'))

            distributor = Distributor.query(Distributor.handle == org_name).get()
            if distributor:
                user_changes = LocationRevisionChanges()
                if self.public_org_user:
                    user_changes.fb_email = self.public_org_user.fb_email
                    user_changes.fb_id = self.public_org_user.fb_id
                    user_changes.fb_username = self.public_org_user.fb_username
                    user_changes.fb_lastname = self.public_org_user.fb_lastname
                    user_changes.fb_firstname = self.public_org_user.fb_firstname
                    user_changes.fb_middlename = self.public_org_user.fb_middlename
                    user_changes.fb_name = self.public_org_user.fb_name
                elif self.public_user:
                    user_changes.fb_email = self.public_user.fb_email
                    user_changes.fb_id = self.public_user.fb_id
                    user_changes.fb_username = self.public_user.fb_username
                    user_changes.fb_lastname = self.public_user.fb_lastname
                    user_changes.fb_firstname = self.public_user.fb_firstname
                    user_changes.fb_middlename = self.public_user.fb_middlename
                    user_changes.fb_name = self.public_user.fb_name
                user_changes.revision_type = "Orgs"
                user_changes.name = distributor.handle
                datas_changes = []

                if self.request.get("org_name"):
                    datas_changes.append("Org Name: " + str(distributor.name) + " >> " + self.request.get("org_name"))
                    distributor.name = self.request.get('org_name')
                if self.request.get("contact_num"):
                    datas_changes.append("Contact Number: " + str(distributor.contact_num) + " >> " + self.request.get("contact_num"))
                    distributor.contact_num = self.request.get('contact_num')
                if self.request.get("contact_details"):
                    datas_changes.append("Contact Details: " + str(distributor.contact_details) + " >> " + self.request.get("contact_details"))
                    distributor.contact_details = self.request.get('contact_details')
                if self.request.get("email"):
                    datas_changes.append("Email: " + str(distributor.email) + " >> " + self.request.get("email"))
                    distributor.email = self.request.get('email')
                if self.request.get("website"):
                    datas_changes.append("Website: " + str(distributor.website) + " >> " + self.request.get("website"))
                    if "http://" in self.request.get("website") or "https://" in self.request.get("website"):
                        distributor.website = self.request.get("website")
                    else:
                        distributor.website = "http://" + self.request.get("website")
                if self.request.get("facebook"):
                    datas_changes.append("Facebook: " + str(distributor.facebook) + " >> " + self.request.get("facebook"))
                    distributor.facebook = self.request.get('facebook')
                if self.request.get('image_url'):
                    datas_changes.append("Image URL: " + str(distributor.logo) + " >> " + self.request.get("image_url"))
                    distributor.logo = self.request.get("image_url")
                user_changes.status = datas_changes
                user_changes.put()
                distributor.put()
                self.redirect(self.request.path + "?success=Changes%20Saved.")
                return
        self.redirect(self.request.path)


class OrgsNewReliefHandler(BaseHandler):
    def get(self, *args, **kwargs):
        if kwargs["org"]:
            org_name = kwargs["org"]
            self.tv["new_relief"] = True

            self.tv["path"] = self.request.path.replace("/new-relief","")

            if self.public_user:
                user_changes = LocationRevisionChanges.query().order(-LocationRevisionChanges.created).fetch(100)
                if user_changes:
                    self.tv["status_changes"] = user_changes

                distributor = Distributor.query(Distributor.handle == org_name).get()
                if distributor:
                    self.tv["distributor"] = distributor

                locations = Location.query().fetch(300)
                if locations:
                    self.tv["locations"] = locations

                self.render('frontend/public-orgs.html')
            elif self.public_org_user:
                user_changes = LocationRevisionChanges.query().order(-LocationRevisionChanges.created).fetch(100)
                if user_changes:
                    self.tv["status_changes"] = user_changes

                distributor = Distributor.query(Distributor.handle == org_name).get()
                if distributor:
                    self.tv["distributor"] = distributor

                locations = Location.query().fetch(300)
                if locations:
                    self.tv["locations"] = locations

                self.render('frontend/public-orgs.html')
            else:
                path_redirect = self.request.path
                self.redirect(facebook.generate_login_url(path_redirect, self.uri_for('www-publicfblogin')))

    def post(self, *args, **kwargs):
        org_name = kwargs["org"]
        distribution_revision = DistributionRevision()
        if self.public_org_user:
            distribution_revision.fb_email = self.public_org_user.fb_email
            distribution_revision.fb_id = self.public_org_user.fb_id
            distribution_revision.fb_access_token = self.public_org_user.fb_access_token
            distribution_revision.fb_username = self.public_org_user.fb_username
            distribution_revision.fb_lastname = self.public_org_user.fb_lastname
            distribution_revision.fb_firstname = self.public_org_user.fb_firstname
            distribution_revision.fb_middlename = self.public_org_user.fb_middlename
            distribution_revision.fb_name = self.public_org_user.fb_name
        elif self.public_user:
            distribution_revision.fb_email = self.public_user.fb_email
            distribution_revision.fb_id = self.public_user.fb_id
            distribution_revision.fb_access_token = self.public_user.fb_access_token
            distribution_revision.fb_username = self.public_user.fb_username
            distribution_revision.fb_lastname = self.public_user.fb_lastname
            distribution_revision.fb_firstname = self.public_user.fb_firstname
            distribution_revision.fb_middlename = self.public_user.fb_middlename
            distribution_revision.fb_name = self.public_user.fb_name
        distribution_revision.name = self.request.get("location") # location name
        distribution_revision.relief_name = self.request.get("relief_name")
        distribution_revision.destination = self.request.get("destination")
        distribution_revision.num_of_packs = int(self.request.get("packs"))
        distribution_revision.description = self.request.get("description")
        distribution_revision.contacts = self.request.get("contacts")
        distribution_revision.needs = self.request.get("needs")
        distribution_revision.date = self.request.get("date")
        distribution_revision.tag = self.request.get("tag")
        distribution_revision.status = self.request.get("status")
        distribution_revision.org_id = org_name
        distribution_revision.put()

        user_changes = LocationRevisionChanges()
        if self.public_org_user:
            user_changes.fb_email = self.public_org_user.fb_email
            user_changes.fb_id = self.public_org_user.fb_id
            user_changes.fb_access_token = self.public_org_user.fb_access_token
            user_changes.fb_username = self.public_org_user.fb_username
            user_changes.fb_lastname = self.public_org_user.fb_lastname
            user_changes.fb_firstname = self.public_org_user.fb_firstname
            user_changes.fb_middlename = self.public_org_user.fb_middlename
            user_changes.fb_name = self.public_org_user.fb_name
        elif self.public_user:
            user_changes.fb_email = self.public_user.fb_email
            user_changes.fb_id = self.public_user.fb_id
            user_changes.fb_access_token = self.public_user.fb_access_token
            user_changes.fb_username = self.public_user.fb_username
            user_changes.fb_lastname = self.public_user.fb_lastname
            user_changes.fb_firstname = self.public_user.fb_firstname
            user_changes.fb_middlename = self.public_user.fb_middlename
            user_changes.fb_name = self.public_user.fb_name
        user_changes.name = self.request.get("location")
        user_changes.revision_type = "Added a New Relief Effort"
        datas_changes = []
        if self.request.get("relief_name"):
            datas_changes.append("Relief Effort: " + distribution_revision.name)
        if self.request.get("destination"):
            datas_changes.append("Destination: " + distribution_revision.destination)
        if self.request.get("packs"):
            datas_changes.append("Packs: " + str(distribution_revision.num_of_packs))
        if self.request.get("description"):
            datas_changes.append("Description: " + distribution_revision.description)
        if self.request.get("contacts"):
            datas_changes.append("Contacts: " + distribution_revision.contacts)
        if self.request.get("needs"):
            datas_changes.append("Needs: " + distribution_revision.needs)
        if self.request.get("date"):
            datas_changes.append("Date: " + distribution_revision.date)
        if self.request.get("tag"):
            datas_changes.append("Tag: " + str(distribution_revision.tag))
        if self.request.get("status"):
            datas_changes.append("Status: " + self.request.get("status"))
        user_changes.status = datas_changes
        user_changes.put()

        self.redirect("/orgs/" + org_name + "?success=Successfully-added.")

class ReliefOperationsPage(BaseHandler):
    def get(self):
        self.tv["current_page"] = "RELIEF_OPERATIONS"
        self.render('frontend/reliefoperations.html')

class PublicPostPage(BaseHandler):
    def get(self, page=None):
        if not page:
            self.render('frontend/public-posts.html')
            return

        self.tv["current_page"] = "PUBLIC_POST"
        post = Post.get_by_id(int(page))
        if not post:
            self.redirect('/')
            return
        self.tv['post'] = post.to_object()
        self.tv['og_description'] = ""
        if post.location:
            self.tv['og_description'] += post.location + '. '
        if post.message:
            self.tv['og_description'] += post.message + '. '
        if post.phone:
            self.tv['og_description'] += post.phone

        self.render('frontend/public-post.html')

class RegisterPage(BaseHandler):
    def get(self):
        if self.user:
            self.redirect(self.uri_for('www-dashboard', referred="register"))
            return

        self.tv["current_page"] = "REGISTER"
        self.render('frontend/register.html')


    def post(self):
        temp = {}
        body = self.request.body
        if body:
            details = simplejson.loads(body)

            user = User.get_by_id(details["email"])
            if user:
                temp["success"] = False
                temp["message"] = "User already exists. Please log in"
                self.response.out.write(simplejson.dumps(temp))
                return

            user = User(id=details["email"])
            user.password = hash_password(details["email"], details["password"])
            user.email = details["email"]
            user.name = details["name"]
            user.put()
            self.login(user)

            temp["success"] = True
            temp["message"] = "Successfully registered!"
            self.response.out.write(simplejson.dumps(temp))

class FBLoginPage(BaseHandler):
    def get(self):
        if not self.settings["enable_fb_login"]:
            self.redirect(self.uri_for("www-login"))
            return

        if self.user:
            self.redirect(self.uri_for('www-dashboard', referred="fblogin"))
            return

        if self.request.get('code') and self.request.get('state'):
            state = self.request.get('state')
            code = self.request.get('code')
            access_token = facebook.code_to_access_token(code, self.uri_for('www-fblogin'))
            if not access_token:
                # Assume expiration, just redirect to login page
                self.redirect(self.uri_for('www-login', referred="fblogin", error="We were not able to connect with Facebook. Please try again."))
                return

            url = "https://graph.facebook.com/me?access_token=" + access_token

            result = urlfetch.fetch(url)
            if result.status_code == 200:
                self.login_fb(simplejson.loads(result.content), access_token)
                self.redirect(str(state))
                return

        else:
            self.redirect(facebook.generate_login_url(self.request.get('goto'), self.uri_for('www-fblogin')))

class CosmoPage(BaseHandler):
    def get(self):
        self.render("frontend/cosmo.html")

class FrontPage(BaseHandler):
    def get(self):
        self.render('frontend/front.html')

class DashboardPage(BaseHandler):
    @login_required
    def get(self):
        self.render('frontend/dashboard.html')

class UserHandler(BaseHandler):
    @login_required
    def get(self):
        edit_id = self.request.get("id_edit")
        if edit_id:
            user = User.get_by_id(edit_id)
            if user:
                temp = {}
                temp["id"] = edit_id
                temp["name"] = user.name
                temp["email"] = user.email
                temp["contacts"] = user.contacts
                temp["permissions"] = user.permissions
                self.response.out.write(simplejson.dumps(temp))
            return

        delete_id = self.request.get("id_delete")
        if delete_id:
            user = User.get_by_id(delete_id)
            if user:
                user.key.delete()
                self.response.out.write(simplejson.dumps({"success": True, "message": "Successfully deleted."}))
            return

        self.response.out.write(simplejson.dumps(get_all_user(self.user.email)))

    def post(self):
        if self.request.get("id"):
            user = User.get_by_id(self.request.get("id"))
            if user:
                user.email = self.request.get("email")
                user.name = self.request.get("name")
                user.contacts = self.request.get("contacts")
                user.permissions = self.request.get("permissions")
                user.put()
        else:
            data = {
                "name": self.request.get("name"),
                "email": self.request.get("email"),
                "password": hash_password(self.request.get("email"), self.request.get("password")),
                "contacts": self.request.get("contacts"),
                "permissions": self.request.get("permissions")
            }

            add_user(data)

class ContactHandler(BaseHandler):
    @login_required
    def get(self):
        edit_id = self.request.get("id_edit")
        if edit_id:
            contact = Contact.get_by_id(int(edit_id))
            if contact:
                temp = {}
                temp["id"] = contact.key.id()
                temp["name"] = contact.name
                temp["contacts"] = contact.contacts
                temp["email"] = contact.email
                temp["facebook"] = contact.facebook
                temp["twitter"] = contact.twitter
                self.response.out.write(simplejson.dumps(temp))
            return

        delete_id = self.request.get("id_delete")
        if delete_id:
            contact = Contact.get_by_id(int(delete_id))
            if contact:
                contact.key.delete()
                self.response.out.write(simplejson.dumps({"success": True, "message": "Successfully deleted."}))
            return

        contacts = Contact.query().order(-Contact.created).fetch(300)
        datas = []
        if contacts:
            for contact in contacts:
                temp = {}
                temp["id"] = contact.key.id()
                temp["name"] = contact.name
                temp["contacts"] = contact.contacts
                temp["email"] = contact.email
                temp["facebook"] = contact.facebook
                temp["twitter"] = contact.twitter
                datas.append(temp)
        self.response.out.write(simplejson.dumps(datas))

    def post(self):
        if self.request.get("id"):
            contact = Contact.get_by_id(int(self.request.get("id")))
            if contact:
                contacts = ""

                if self.request.get("contacts"):
                    if ", " in self.request.get("contacts"):
                        contacts = self.request.get("contacts").split(", ")
                    else:
                        contacts = [self.request.get("contacts")]

                contact.name = self.request.get("name")
                contact.contacts = contacts
                contact.email = self.request.get("email")
                contact.facebook = self.request.get("facebook")
                contact.twitter = self.request.get("twitter")
                contact.put()
        else:
            contacts = ""

            if self.request.get("contacts"):
                if ", " in self.request.get("contacts"):
                    contacts = self.request.get("contacts").split(", ")
                else:
                    contacts = [self.request.get("contacts")]


            data = {
                "name": self.request.get("name"),
                "email": self.request.get("email"),
                "twitter": self.request.get("twitter"),
                "facebook": self.request.get("facebook"),
                "contacts": contacts,
            }

            add_contact(data)

class LocationHandler(BaseHandler):
    @login_required
    def get(self):
        deleteimage = self.request.get('deleteimage')
        if deleteimage:
            location = Location.get_by_id(self.request.get("locid"))
            if location:
                if location.images:
                    location.images.pop(int(deleteimage))
                location.put()

            return

        delete_id = self.request.get("id_delete")
        if delete_id:
            location = Location.get_by_id(delete_id)
            if location:
                location.key.delete()
            return

        id_edit = self.request.get("id_edit")
        if id_edit:
            location = Location.get_by_id(id_edit)
            if location:
                temp = {}
                temp["id"] = location.key.id()
                temp["name"] = location.name
                temp["relief_aid_status"] = location.relief_aid_status
                temp["latlong"] = location.latlong
                temp["featured_photo"] = location.featured_photo
                temp["death_count"] = location.death_count
                temp["death_count_text"] = location.death_count_text
                temp["affected_count"] = location.affected_count
                temp["affected_count_text"] = location.affected_count_text
                temp["status_board"] = location.status_board
                temp["needs"] = location.needs
                temp["status"] = location.status
                temp["hash_tag"] = location.hash_tag
                temp["featured"] = location.featured
                temp["images"] = location.images
                temp["missing_person"] = location.missing_person
                temp["missing_person_text"] = location.missing_person_text
                self.response.out.write(simplejson.dumps(temp))
            return

        locations = Location.query().order(-Location.name).fetch(300)
        datas = []
        if locations:
            for location in locations:
                temp = {}
                temp["id"] = location.key.id()
                temp["name"] = location.name
                temp["relief_aid_status"] = location.relief_aid_status
                temp["latlong"] = location.latlong
                temp["featured_photo"] = location.featured_photo
                temp["death_count"] = location.death_count
                temp["death_count_text"] = location.death_count_text
                temp["affected_count"] = location.affected_count
                temp["affected_count_text"] = location.affected_count_text
                temp["status_board"] = location.status_board
                temp["needs"] = location.needs
                temp["status"] = location.status
                temp["images"] = location.images
                temp["hash_tag"] = location.hash_tag
                temp["featured"] = location.featured
                temp["missing_person"] = location.missing_person
                temp["missing_person_text"] = location.missing_person_text
                datas.append(temp)
        self.response.out.write(simplejson.dumps(datas))

    def post(self):
        if self.request.get("id"):
            location = Location.get_by_id(self.request.get("id"))
            if location:
                needs = {
                    "food": self.request.get("food"),
                    "water": self.request.get("water"),
                    "medicines": self.request.get("medicines"),
                    "social_workers": self.request.get("social_workers"),
                    "medical_workers": self.request.get("medical_workers"),
                    "shelter": self.request.get("shelter"),
                    "formula": self.request.get("formula"),
                    "toiletries": self.request.get("toiletries"),
                    "flashlights": self.request.get("flashlights"),
                    "cloths": self.request.get("cloths"),
                    "miscellaneous" : self.request.get("miscellaneous")
                }

                status = {
                    "power": self.request.get("power"),
                    "communication": self.request.get("communication"),
                    "water": self.request.get("status_water"),
                    "medicines": self.request.get("status_medicines"),
                    "cloths": self.request.get("status_clothes"),
                    "food": self.request.get("status_foods"),
                    "shelter": self.request.get("status_shelter")
                }

                urls = self.request.get("image_urls")
                titles = self.request.get("image_titles")
                captions = self.request.get("image_captions")
                new_urls = simplejson.loads(urls)
                new_titles = simplejson.loads(titles)
                new_captions = simplejson.loads(captions)

                if location.images:
                    cnt = len(new_urls)
                    for i in range(0, cnt):
                        if new_urls[i]["srcid"] != "":
                            for loc_image in location.images:
                                if new_urls[i]["srcid"] == loc_image["src"]:
                                    loc_image["src"] = new_urls[i]["src"]
                                    loc_image["image_title"] = new_titles[i]["image_title"]
                                    loc_image["image_caption"] = new_captions[i]["image_caption"]
                        else:
                            location.images.append({"src": new_urls[i]["src"], "image_title": new_titles[i]["image_title"], "image_caption": new_captions[i]["image_caption"]})
                else:
                    images_datas = []
                    cnt = len(new_urls)
                    image_data = []
                    for i in range(0, cnt):
                        if new_urls[i]["src"] != "" or new_titles[i]["image_title"] != "" or new_captions[i]["image_caption"] != "":
                            images = {}
                            images["src"] = new_urls[i]["src"]
                            images["image_title"] = new_titles[i]["image_title"]
                            images["image_caption"] = new_captions[i]["image_caption"]
                            image_data.append(images)
                    location.images = image_data

                location.name = self.request.get("name")
                location.relief_aid_status = self.request.get("relief_aid_status")
                location.latlong = self.request.get("latlong")
                location.featured_photo = self.request.get("featured_photo")
                location.death_count = int(self.request.get("death_count"))
                location.death_count_text = self.request.get("death_count_text")
                location.affected_count = int(self.request.get("affected_count"))
                location.affected_count_text = self.request.get("affected_count_text")
                location.missing_person = int(self.request.get("missing_person"))
                location.missing_person_text = self.request.get("missing_person_text")
                location.status_board = self.request.get("status_board")
                location.needs = needs
                location.status = status
                location.hash_tag = self.request.get("hash_tag").split(" ")
                featured_yes_no = ""
                if self.request.get("featured"):
                    if self.request.get("featured") == "True":
                        featured_yes_no = True
                    else:
                        featured_yes_no = False
                location.featured = featured_yes_no
                location.put()

                params = {
                    "location_id": location.key.id()
                }
                taskqueue.add(url='/admin/tasks/compute_relief_status', params=params, method='POST')

        else:
            urls = self.request.get("image_urls")
            titles = self.request.get("image_titles")
            captions = self.request.get("image_captions")
            new_urls = simplejson.loads(urls)
            new_titles = simplejson.loads(titles)
            new_captions = simplejson.loads(captions)

            images_datas = []
            cnt = len(new_urls)
            image_data = []
            for i in range(0, cnt):
                if new_urls[i]["src"] != "" or new_titles[i]["image_title"] != "" or new_captions[i]["image_caption"] != "":
                    images = {}
                    images["src"] = new_urls[i]["src"]
                    images["image_title"] = new_titles[i]["image_title"]
                    images["image_caption"] = new_captions[i]["image_caption"]
                    image_data.append(images)

            needs = {
               "food": self.request.get("food"),
                "water": self.request.get("water"),
                "medicines": self.request.get("medicines"),
                "social_workers": self.request.get("social_workers"),
                "medical_workers": self.request.get("medical_workers"),
                "shelter": self.request.get("shelter"),
                "formula": self.request.get("formula"),
                "toiletries": self.request.get("toiletries"),
                "flashlights": self.request.get("flashlights"),
                "cloths": self.request.get("cloths"),
                "miscellaneous" : self.request.get("miscellaneous")
            }

            status = {
                "power": self.request.get("power"),
                "communication": self.request.get("communication"),
                "water": self.request.get("status_water"),
                "medicines": self.request.get("status_medicines"),
                "cloths": self.request.get("status_clothes"),
                "food": self.request.get("status_foods"),
                "shelter": self.request.get("status_shelter")
            }

            hash_tag = self.request.get("hash_tag").split(" ")

            featured_yes_no = ""
            if self.request.get("featured"):
                if self.request.get("featured") == "True":
                    featured_yes_no = True
                else:
                    featured_yes_no = False

            data = {
                "name": self.request.get("name"),
                "relief_aid_status": self.request.get("relief_aid_status"),
                "needs": needs, # json format
                "centers": self.request.get_all("centers"),
                "latlong": self.request.get("latlong"),
                "featured_photo": self.request.get("featured_photo"),
                "death_count": self.request.get("death_count"),
                "death_count_text": self.request.get("death_count_text"),
                "affected_count": self.request.get("affected_count"),
                "affected_count_text": self.request.get("affected_count_text"),
                "status_board": self.request.get("status_board"),
                "status": status,
                "images": image_data, # json format
                "hash_tag" : hash_tag,
                "featured" : featured_yes_no,
                "missing_person": int(self.request.get("missing_person")),
                "missing_person_text": self.request.get("missing_person_text")
            }
            add_location(data)

class DistributionHandler(BaseHandler):
    @login_required
    def get(self):
        id_delete = self.request.get("id_delete")
        if id_delete:
            distribution = Distribution.get_by_id(int(id_delete))
            if distribution:
                distribution.key.delete()
            return

        distributions = Distribution.query().order(-Distribution.created).fetch(300)
        datas = []
        if distributions:
            for distribution in distributions:
                temp = {}
                temp["id"] = distribution.key.id()
                temp["date_of_distribution"] = str(distribution.date_of_distribution.strftime("%m/%d/%Y"))
                temp["contact"] = distribution.contact
                temp["destinations"] = distribution.destinations.id()
                temp["supply_goal"] = distribution.supply_goal
                temp["actual_supply"] = distribution.actual_supply
                temp["images"] = distribution.images
                temp["status"] = distribution.status
                temp["info"] = distribution.info
                temp["featured_photo"] = distribution.featured_photo
                temp["description"] = distribution.description
                datas.append(temp)
        self.response.out.write(simplejson.dumps(datas))

    def post(self):
        if self.request.get("id"):
            distribution = Distribution.get_by_id(int(self.request.get("id")))
            if distribution:
                supply_goal = {
                    "food" : {
                        "food" : self.request.get("chk_supply_goal_food"),
                        "description" : self.request.get("chk_supply_goal_food_description")
                    },
                    "water" :
                    {
                        "water" : self.request.get("chk_supply_goal_water"),
                        "description" : self.request.get("chk_supply_goal_wate_descriptionr")
                    },
                    "medicines" : {
                        "medicines" : self.request.get("chk_supply_goal_medicines"),
                        "description" : self.request.get("chk_supply_goal_medicines_description")
                    },

                    "social_workers" : {
                        "social_workers" : self.request.get("chk_supply_goal_social_workers"),
                        "description" : self.request.get("chk_supply_goal_social_workers_description")
                    },

                    "medical_workers" : {
                        "medical_workers" : self.request.get("chk_supply_goal_medical_workers"),
                        "description" : self.request.get("chk_supply_goal_medical_workers_description")
                    },

                    "shelter" : {
                        "shelter" : self.request.get("chk_supply_goal_shelter"),
                        "description" : self.request.get("chk_supply_goal_shelter_description")
                    },

                    "formula" : {
                        "formula" : self.request.get("chk_supply_goal_formula"),
                        "description" : self.request.get("chk_supply_goal_formula_description")
                    },

                    "toiletries" : {
                        "toiletries" : self.request.get("chk_supply_goal_toiletries"),
                        "description" : self.request.get("chk_supply_goal_toiletries_description"),
                    },

                    "flashlights" : {
                        "flashlights" : self.request.get("chk_supply_goal_flashlights"),
                        "description" : self.request.get("chk_supply_goal_flashlights_description")
                    }

                }

                actual_supply = {
                    "food" : {
                        "food" : self.request.get("chk_actual_supply_food"),
                        "description" : self.request.get("chk_actual_supply_food_description")
                    },

                    "water" : {
                        "water" : self.request.get("chk_actual_supply_water"),
                        "description" : self.request.get("chk_actual_supply_water_description")
                    },

                    "medicines" : {
                        "medicines" : self.request.get("chk_actual_supply_medicines"),
                        "description" : self.request.get("chk_actual_supply_medicines_description")
                    },

                    "social_workers" : {
                        "social_workers" : self.request.get("chk_actual_supply_social_workers"),
                        "description" : self.request.get("chk_actual_supply_social_workers_description")
                    },

                    "medical_workers" : {
                        "medical_workers" : self.request.get("chk_actual_supply_medical_workers"),
                        "description" : self.request.get("chk_actual_supply_medical_workers_description"),
                    },

                    "shelter" : {
                        "shelter" : self.request.get("chk_actual_supply_shelter"),
                        "description" : self.request.get("chk_actual_supply_shelter_description")
                    },

                    "formula" : {
                        "formula" : self.request.get("chk_actual_supply_formula"),
                        "description" : self.request.get("chk_actual_supply_formula_description")
                    },

                    "toiletries" : {
                        "toiletries" : self.request.get("chk_actual_supply_toiletries"),
                        "description" : self.request.get("chk_actual_supply_toiletries_description")
                    },

                    "flashlights" : {
                        "flashlights" : self.request.get("chk_actual_supply_flashlights"),
                        "description" : self.request.get("chk_actual_supply_flashlights_description")
                    }

                }

                urls = self.request.get("image_urls")
                titles = self.request.get("image_titles")
                captions = self.request.get("image_captions")
                new_urls = simplejson.loads(urls)
                new_titles = simplejson.loads(titles)
                new_captions = simplejson.loads(captions)

                if distribution.images:
                    cnt = len(new_urls)
                    image_data = []
                    for i in range(0, cnt):
                        if new_urls[i]["src"] != "" or new_titles[i]["image_title"] != "" or new_captions[i]["image_caption"] != "":
                            images = {}
                            images["src"] = new_urls[i]["src"]
                            images["image_title"] = new_titles[i]["image_title"]
                            images["image_caption"] = new_captions[i]["image_caption"]
                            distribution.images.append(images)
                else:
                    images_datas = []
                    cnt = len(new_urls)
                    image_data = []
                    for i in range(0, cnt):
                        if new_urls[i]["src"] != "" or new_titles[i]["image_title"] != "" or new_captions[i]["image_caption"] != "":
                            images = {}
                            images["src"] = new_urls[i]["src"]
                            images["image_title"] = new_titles[i]["image_title"]
                            images["image_caption"] = new_captions[i]["image_caption"]
                            image_data.append(images)
                    distribution.images = image_data

                distribution.date_of_distribution = datetime.datetime.strptime(self.request.get("date_of_distribution"), "%Y-%m-%d")
                distribution.contact = self.request.get("contact")
                distribution.destinations = ndb.Key("Location", self.request.get("destinations"))
                distribution.supply_goal =supply_goal
                distribution.actual_supply = actual_supply
                distribution.status = self.request.get("status").strip().upper()
                distribution.info = self.request.get("info")
                distribution.featured_photo = self.request.get("featured_photo")
                distribution.description = self.request.get("description")
                distribution.put()

        else:
            supply_goal = {
                "food" : {
                    "food" : self.request.get("chk_supply_goal_food"),
                    "description" : self.request.get("chk_supply_goal_food_description")
                },
                "water" :
                {
                    "water" : self.request.get("chk_supply_goal_water"),
                    "description" : self.request.get("chk_supply_goal_wate_descriptionr")
                },
                "medicines" : {
                    "medicines" : self.request.get("chk_supply_goal_medicines"),
                    "description" : self.request.get("chk_supply_goal_medicines_description")
                },

                "social_workers" : {
                    "social_workers" : self.request.get("chk_supply_goal_social_workers"),
                    "description" : self.request.get("chk_supply_goal_social_workers_description")
                },

                "medical_workers" : {
                    "medical_workers" : self.request.get("chk_supply_goal_medical_workers"),
                    "description" : self.request.get("chk_supply_goal_medical_workers_description")
                },

                "shelter" : {
                    "shelter" : self.request.get("chk_supply_goal_shelter"),
                    "description" : self.request.get("chk_supply_goal_shelter_description")
                },

                "formula" : {
                    "formula" : self.request.get("chk_supply_goal_formula"),
                    "description" : self.request.get("chk_supply_goal_formula_description")
                },

                "toiletries" : {
                    "toiletries" : self.request.get("chk_supply_goal_toiletries"),
                    "description" : self.request.get("chk_supply_goal_toiletries_description"),
                },

                "flashlights" : {
                    "flashlights" : self.request.get("chk_supply_goal_flashlights"),
                    "description" : self.request.get("chk_supply_goal_flashlights_description")
                }

            }

            actual_supply = {
                "food" : {
                    "food" : self.request.get("chk_actual_supply_food"),
                    "description" : self.request.get("chk_actual_supply_food_description")
                },

                "water" : {
                    "water" : self.request.get("chk_actual_supply_water"),
                    "description" : self.request.get("chk_actual_supply_water_description")
                },

                "medicines" : {
                    "medicines" : self.request.get("chk_actual_supply_medicines"),
                    "description" : self.request.get("chk_actual_supply_medicines_description")
                },

                "social_workers" : {
                    "social_workers" : self.request.get("chk_actual_supply_social_workers"),
                    "description" : self.request.get("chk_actual_supply_social_workers_description")
                },

                "medical_workers" : {
                    "medical_workers" : self.request.get("chk_actual_supply_medical_workers"),
                    "description" : self.request.get("chk_actual_supply_medical_workers_description"),
                },

                "shelter" : {
                    "shelter" : self.request.get("chk_actual_supply_shelter"),
                    "description" : self.request.get("chk_actual_supply_shelter_description")
                },

                "formula" : {
                    "formula" : self.request.get("chk_actual_supply_formula"),
                    "description" : self.request.get("chk_actual_supply_formula_description")
                },

                "toiletries" : {
                    "toiletries" : self.request.get("chk_actual_supply_toiletries"),
                    "description" : self.request.get("chk_actual_supply_toiletries_description")
                },

                "flashlights" : {
                    "flashlights" : self.request.get("chk_actual_supply_flashlights"),
                    "description" : self.request.get("chk_actual_supply_flashlights_description")
                }

            }

            urls = self.request.get("image_urls")
            titles = self.request.get("image_titles")
            captions = self.request.get("image_captions")
            new_urls = simplejson.loads(urls)
            new_titles = simplejson.loads(titles)
            new_captions = simplejson.loads(captions)

            images_datas = []
            cnt = len(new_urls)
            image_data = []
            for i in range(0, cnt):
                if new_urls[i]["src"] != "" or new_titles[i]["image_title"] != "" or new_captions[i]["image_caption"] != "":
                    images = {}
                    images["src"] = new_urls[i]["src"]
                    images["image_title"] = new_titles[i]["image_title"]
                    images["image_caption"] = new_captions[i]["image_caption"]
                    image_data.append(images)

            data = {
                "date_of_distribution": datetime.datetime.strptime(self.request.get("date_of_distribution"), "%Y-%m-%d"), #1992-10-20
                "contact": self.request.get("contact"),
                "destinations": self.request.get("destinations"),
                "supply_goal": supply_goal,
                "actual_supply": actual_supply,
                "images" : image_data,
                "status" : self.request.get("status").strip().upper(),
                "info": self.request.get("info"),
                "featured_photo": self.request.get("featured_photo"),
                "description": self.request.get("description")
            }

            add_distribution(data)

class DistributionFetchHandler(BaseHandler):
    @login_required
    def get(self):
        datas_contacts = []
        temp_type = {}
        contacts = Contact.query().fetch(300)
        if contacts:
            for contact in contacts:
                temp = {}
                temp["id"] = contact.key.id()
                temp["name"] = contact.name
                temp["contacts"] = contact.contacts
                temp["email"] = contact.email
                temp["facebook"] = contact.facebook
                temp["twitter"] = contact.twitter
                datas_contacts.append(temp)
            temp_type["contacts"] = datas_contacts

        datas_locations = []
        locations = Location.query().fetch(300)
        if locations:
            for location in locations:
                temp = {}
                temp["id"] = location.key.id()
                temp["name"] = location.name
                temp["latlong"] = location.latlong
                temp["featured_photo"] = location.featured_photo
                temp["death_count"] = location.death_count
                temp["affected_count"] = location.affected_count
                temp["status_board"] = location.status_board
                temp["needs"] = location.needs
                temp["status"] = location.status
                datas_locations.append(temp)
            temp_type["locations"] = datas_locations
        self.response.out.write(simplejson.dumps(temp_type))

class DistributionFetch2Handler(BaseHandler):
    @login_required
    def get(self):
        datas_contacts = []
        temp_type = {}
        contacts = Contact.query().fetch(300)
        if contacts:
            for contact in contacts:
                temp = {}
                temp["id"] = contact.key.id()
                temp["name"] = contact.name
                temp["contacts"] = contact.contacts
                temp["email"] = contact.email
                temp["facebook"] = contact.facebook
                temp["twitter"] = contact.twitter
                datas_contacts.append(temp)
            temp_type["contacts"] = datas_contacts

        datas_distribution = []
        distribution = Distribution.get_by_id(int(self.request.get("id")))
        if distribution:
            temp = {}
            temp["id"] = distribution.key.id()
            temp["date_of_distribution"] = str(distribution.date_of_distribution.strftime("%Y-%m-%d")) # 2004-01-14
            temp["contact"] = distribution.contact
            temp["destinations"] = distribution.destinations.urlsafe()
            temp["supply_goal"] = distribution.supply_goal
            temp["actual_supply"] = distribution.actual_supply
            temp["images"] = distribution.images
            temp["status"] = distribution.status
            temp["info"] = distribution.info
            temp["featured_photo"] = distribution.featured_photo
            temp["description"] = distribution.description
            datas_distribution.append(temp)
            temp_type["distribution"] = datas_distribution

        datas_locations = []
        locations = Location.query().fetch(300)
        if locations:
            for location in locations:
                temp = {}
                temp["id"] = location.key.id()
                temp["name"] = location.name
                temp["latlong"] = location.latlong
                temp["featured_photo"] = location.featured_photo
                temp["death_count"] = location.death_count
                temp["affected_count"] = location.affected_count
                temp["status_board"] = location.status_board
                temp["needs"] = location.needs
                temp["status"] = location.status
                datas_locations.append(temp)
            temp_type["locations"] = datas_locations
        self.response.out.write(simplejson.dumps(temp_type))

class DistributorHandler(BaseHandler):
    @login_required
    def get(self):
        id_delete = self.request.get("id_delete")
        if id_delete:
            distributor = Distributor.get_by_id(int(id_delete))
            if distributor:
                distributor.key.delete()
            return

        if self.request.get("id_edit"):
            distributor = Distributor.get_by_id(int(self.request.get("id_edit")))
            temp = {}
            temp["id"] = distributor.key.id()
            temp["name"] = distributor.name
            temp["contact_num"] = distributor.contact_num
            temp["email"] = distributor.email
            temp["website"] = distributor.website
            temp["facebook"] = distributor.facebook
            temp["contact_details"] = distributor.contact_details

            self.response.out.write(simplejson.dumps(temp))
            return

        distributors = Distributor.query().order(-Distributor.created).fetch(300)
        datas = []
        if distributors:
            for distributor in distributors:
                temp = {}
                temp["id"] = distributor.key.id()
                temp["name"] = distributor.name
                temp["contact_num"] = distributor.contact_num
                temp["email"] = distributor.email
                temp["website"] = distributor.website
                temp["facebook"] = distributor.facebook
                temp["contact_details"] = distributor.contact_details

                datas.append(temp)
        self.response.out.write(simplejson.dumps(datas))

    def post(self):
        if self.request.get('id'):
            distributor = Distributor.get_by_id(int(self.request.get("id")))
            distributor.name = self.request.get("name").lower()
            distributor.contact_num = self.request.get("contact_num")
            distributor.email = self.request.get("email")
            if "http://" in self.request.get("website") or "https://" in self.request.get("website"):
                distributor.website = self.request.get("website")
            else:
                distributor.website = "http://" + self.request.get("website")

            if "http://" in self.request.get("facebook") or "https://" in self.request.get("facebook"):
                distributor.facebook = self.request.get("facebook")
            else:
                distributor.facebook = "http://" + self.request.get("facebook")
            distributor.contact_details = self.request.get("contact_details")
            distributor.put()
        else:
            distributor = Distributor()
            distributor.name = self.request.get("name").lower()
            distributor.contact_num = self.request.get("contact_num")
            distributor.email = self.request.get("email")
            distributor.website = self.request.get("website")
            if "http://" in self.request.get("facebook") or "https://" in self.request.get("facebook"):
                distributor.facebook = self.request.get("facebook")
            else:
                distributor.facebook = "http://" + self.request.get("facebook")
            distributor.contact_details = self.request.get("contact_details")
            distributor.put()

class CentersHandler(BaseHandler):
    @login_required
    def get(self):
        if self.request.get("id_delete"):
            drop = DropOffCenter.get_by_id(self.request.get("id_delete"))
            if drop:
                drop.key.delete()
            return

        if self.request.get("id_edit"):
            drop = DropOffCenter.get_by_id(self.request.get("id_edit"))
            if drop:
                temp = {}
                temp["id"] = drop.key.id()
                temp["name"] = drop.name
                temp["drop_off_locations"] = drop.drop_off_locations
                temp["distributor"] = drop.distributor
                temp["address"] = drop.address
                temp["latlong"] = drop.latlong
                temp["destinations"] = drop.destinations
                temp["schedule"] = drop.schedule
                temp["twitter"] = drop.twitter
                temp["facebook"] = drop.facebook
                temp["contacts"] = drop.contacts
                temp["email"] = drop.email
                self.response.out.write(simplejson.dumps(temp))
                return

        dropOffCenters = DropOffCenter.query().order(-DropOffCenter.created).fetch(300)
        datas = []
        if dropOffCenters:
            for drop in dropOffCenters:
                temp = {}
                temp["id"] = drop.key.id()
                temp["name"] = drop.name
                temp["drop_off_locations"] = drop.drop_off_locations
                temp["distributor"] = drop.distributor
                temp["address"] = drop.address
                temp["latlong"] = drop.latlong
                temp["destinations"] = drop.destinations
                temp["schedule"] = drop.schedule
                temp["twitter"] = drop.twitter
                temp["facebook"] = drop.facebook
                temp["contacts"] = drop.contacts
                temp["email"] = drop.email
                datas.append(temp)
        self.response.out.write(simplejson.dumps(datas))

    def post(self):
        if self.request.get("id"):
            drop = DropOffCenter.get_by_id(self.request.get('id'))
            if drop:
                drop.name = self.request.get("name")
                drop.drop_off_locations = self.request.get("drop_off_locations").split(", ")
                drop.distributor = self.request.get("distributors").split(", ")
                drop.address = self.request.get("address")
                drop.latlong = self.request.get("latlong")
                drop.destinations = self.request.get("destinations").split(", ")
                drop.schedule = self.request.get("schedule")
                drop.twitter = self.request.get("twitter")
                drop.facebook = self.request.get("facebook")
                drop.contacts = self.request.get("contacts").split(", ")
                drop.email = self.request.get("email")
                drop.put()
        else:
            data = {
                "name" : self.request.get("name"),
                "drop_off_locations": self.request.get("drop_off_locations"),
                "distributor": self.request.get("distributors"),
                "address": self.request.get("address"),
                "latlong": self.request.get("latlong"),
                "destinations": self.request.get("destinations"),
                "schedule": self.request.get("schedule"),
                "twitter": self.request.get("twitter"),
                "facebook": self.request.get("facebook"),
                "contacts": self.request.get("contacts"),
                "email": self.request.get("email"),
            }

            add_drop_off_centers(data)

class SubscriberPage(BaseHandler):
    @login_required
    def get(self):
        pass
    def post(self):
        distribution = distribution.key
        if distribution:
            data = {
                'name': self.request.get('name'),
                'email': self.request.get('email'),
                'fb_id': self.request.get('fb_id'),
                'distributor': distribution.key
            }
            add_subcriber(data)

class PostsHandler(BaseHandler):
    @login_required
    def get(self):
        if self.request.get("id_delete"):
            post = Post.get_by_id(int(self.request.get("id_delete")))
            if post:
                post.key.delete()
            return

        if self.request.get("id_edit"):
            temp_type = {}
            data_post = []
            post = Post.get_by_id(int(self.request.get("id_edit")))
            if post:
                temp = {}
                temp["id"] = post.key.id()
                temp["name"] = post.name
                temp["phone"] = post.phone
                temp["email"] = post.email
                temp["facebook"] = post.facebook
                temp["twitter"] = post.twitter
                temp["message"] = post.message
                temp["post_type"] = post.post_type
                temp["expiry"] = str(post.expiry.strftime("%m/%d/%Y"))
                temp["location"] = post.location
                temp["status"] = post.status
                data_post.append(temp)
                temp_type["post"] = data_post

            datas_locations = []
            locations = Location.query().fetch(300)
            if locations:
                for location in locations:
                    temp = {}
                    temp["id"] = location.key.id()
                    temp["name"] = location.name
                    temp["latlong"] = location.latlong
                    temp["featured_photo"] = location.featured_photo
                    temp["death_count"] = location.death_count
                    temp["affected_count"] = location.affected_count
                    temp["status_board"] = location.status_board
                    temp["needs"] = location.needs
                    temp["status"] = location.status
                    datas_locations.append(temp)
                temp_type["locations"] = datas_locations
            self.response.out.write(simplejson.dumps(temp_type))
            return

        posts = Post.query().order(-Post.created).fetch(300)
        datas = []
        if posts:
            for post in posts:
                temp = {}
                temp["id"] = post.key.id()
                temp["name"] = post.name
                temp["phone"] = post.phone
                temp["email"] = post.email
                temp["facebook"] = post.facebook
                temp["twitter"] = post.twitter
                temp["message"] = post.message
                temp["post_type"] = post.post_type
                temp["expiry"] = str(post.expiry.strftime("%m/%d/%Y"))
                temp["location"] = post.location
                temp["status"] = post.status
                datas.append(temp)
        self.response.out.write(simplejson.dumps(datas))

    def post(self):
        post_type = []
        if self.request.get("need_transpo"):
            post_type.append(self.request.get("need_transpo"))
        if self.request.get("need_people"):
            post_type.append(self.request.get("need_people"))
        if self.request.get("need_goods"):
            post_type.append(self.request.get("need_goods"))
        if self.request.get("need_needs"):
            post_type.append(self.request.get("need_needs"))
        if self.request.get("have_transpo"):
            post_type.append(self.request.get("have_transpo"))
        if self.request.get("have_people"):
            post_type.append(self.request.get("have_people"))
        if self.request.get("have_goods"):
            post_type.append(self.request.get("have_goods"))
        if self.request.get("have_needs"):
            post_type.append(self.request.get("have_needs"))

        data = {
            "name": self.request.get("name"),
            "email": self.request.get("email"),
            "twitter": self.request.get("twitter"),
            "facebook": self.request.get("facebook"),
            "phone": self.request.get("phone"),
            "message": self.request.get("message"),
            "post_type": post_type,
            "expiry": datetime.datetime.strptime(self.request.get("expiry"), "%Y-%m-%d"), #1992-10-20
            "location": self.request.get("location"),
            "status": "ACTIVE"
        }

        add_post(data)


# for testing purposes only
class sampler(BaseHandler):
    def get(self):

        self.response.out.write(self.request.uri)

class ErrorHandler(BaseHandler):
    def get(self, page):
        logging.critical("This route is not handled.")

# API Handlers


def oauthed_required(fn):
    '''So we can decorate any RequestHandler with #@login_required'''
    def wrapper(self, *args):
        resp = API_OAUTH_RESP.copy()
        if not self.request.get('access_token'):
            resp["response"] = "missing_params"
            resp["code"] = 406
            resp["type"] = "APIAuthException"
            resp["message"] = "The request has missing parameters: access_token"
        else:
            access_token = self.request.get('access_token')
            if not self.current_user:
                resp["response"] = "unauthorized"
                resp["code"] = 401
                resp["type"] = "APIAuthException"
                resp["message"] = "This request is unauthorized"
            else:
                user_token = UserToken.get_by_id(access_token)
                if user_token.expires < datetime.datetime.now():
                    resp["response"] = "expired"
                    resp["code"] = 401
                    resp["type"] = "APIAuthException"
                    resp["message"] = "Authentication has expired"
                else:
                    return fn(self, *args)
        self.render(resp)
    return wrapper


class APIBaseHandler(webapp2.RequestHandler):
    def __init__(self, request=None, response=None):
        self.initialize(request, response)

    @property # to get current user: self.current_user
    def current_user(self):
        access_token = self.request.get('access_token') if self.request.get('access_token') else None
        if access_token:
            user_token = UserToken.get_by_id(access_token)
            if user_token:
                return user_token.user.get()

        return False

    @property
    def params(self):
        params = {}
        for arg in self.request.arguments():
            values = self.request.get_all(arg)
            if len(values) > 1:
                params[arg] = values
            else:
                params[arg] = values[0]
        return params

    @property
    def base_uri(self):
        if "?" in self.request.uri:
            base_uri = self.request.uri[0:(self.request.uri.find('?'))]
        else:
            base_uri = self.request.uri

        return base_uri

    def render(self, response_body):
        self.response.headers["Content-Type"] = "application/json"

        self.response.out.write(simplejson.dumps(response_body))


class GetUserToken(APIBaseHandler):
    @oauthed_required
    def get(self):
        logging.info(self.current_user)

    def post(self):
        resp = OAUTH_RESP.copy()
        if self.request.get('token_code') and self.request.get('secret_key') and self.request.get('client_id'):
            token_code = self.request.get('token_code')
            secret_key = self.request.get('secret_key')
            client_id = self.request.get('client_id')

            user_token = UserToken.query(UserToken.code == token_code).get()
            if user_token:
                client = user_token.client.get()
                if client:
                    if client.secret_key == secret_key and client.client_id == client_id:
                        if user_token.expires > datetime.datetime.now():
                            # success, reply with access_token!
                            resp["success"]["access_token"] = str(user_token.token)
                            resp["success"]["expires_in"] = int(calendar.timegm(user_token.expires.timetuple()))
                            resp["success"]["token_code"] = str(token_code)
                        else:
                            #  expired oauth
                            resp["response"] = "token_expired"
                            resp["code"] = 401
                    else:
                        #  invalid client
                        resp["response"] = "invalid_client"
                        resp["code"] = 404
                else:
                    # invalid client
                    resp["response"] = "invalid_client"
                    resp["code"] = 404
            else:
                #invalid token_code
                resp["response"] = "invalid_code"
                resp["code"] = 404
        else:
            # missing params
            resp["response"] = "missing_params"
            resp["code"] = 406

        self.render(resp)


class APIUsersHandler(APIBaseHandler):
    @oauthed_required
    def get(self, instance_id=None):
        resp = API_RESPONSE.copy()
        resp["method"] = "get"
        failed = False
        users_json = []
        if not instance_id:
            if self.request.get("cursor"):
                try:
                    curs = Cursor(urlsafe=self.request.get("cursor"))
                except Exception, e:
                    resp['response'] = "invalid_cursor"
                    resp['code'] = 406
                    resp['property'] = "cursor"
                    resp['description'] = "Invalid cursor"
                    failed = True
                else:
                    if curs:
                        users, next_cursor, more = User.query().fetch_page(25, start_cursor=curs)
                    else:
                        users, next_cursor, more = User.query().fetch_page(25)
            else:
                users, next_cursor, more = User.query().fetch_page(25)

            if not failed:
                for user in users:
                    users_json.append(user.to_object())

                data = {}
                data["users"] = users_json
                if more:
                    data["next_page"] = "http://api.bangonph.com/v1/users?cursor=" + str(next_cursor.urlsafe())
                else:
                    data["next_page"] = False

                resp["description"] = "List of users"
                resp["property"] = "posts"
                resp["data"] = data
        else:
            user = User.get_by_id(instance_id)
            if user:
                resp["description"] = "Instance data"
                resp["property"] = "user"
                resp["data"] = user.to_object()
            else:
                # instance dont exist
                resp['response'] = "invalid_instance"
                resp['code'] = 404
                resp['property'] = "instance_id"
                resp['description'] = "Instance id missing or not valid"

        self.render(resp)

    def post(self, instance_id=None):
        pass

    def delete(self, instance_id=None):
        pass

class APILocationsHandler(APIBaseHandler):
    def get(self, instance_id=None):
        resp = API_RESPONSE.copy()
        resp["method"] = "get"
        failed = False
        locations_json = []
        if not instance_id:
            if self.request.get("cursor"):
                try:
                    curs = Cursor(urlsafe=self.request.get("cursor"))
                except Exception, e:
                    resp['response'] = "invalid_cursor"
                    resp['code'] = 406
                    resp['property'] = "cursor"
                    resp['description'] = "Invalid cursor"
                    failed = True
                else:
                    if curs:
                        locations, next_cursor, more = Location.query().fetch_page(25, start_cursor=curs)
                    else:
                        locations, next_cursor, more = Location.query().fetch_page(25)
            else:
                locations, next_cursor, more = Location.query().fetch_page(25)

            if not failed:
                if self.request.get('show_relief'):
                    for location in locations:
                        locations_json.append(location.to_object(show_relief=True))
                else:
                    for location in locations:
                        locations_json.append(location.to_object())

                data = {}
                data["locations"] = locations_json
                if more:
                    data["next_page"] = "http://api.bangonph.com/v1/locations?cursor=" + str(next_cursor.urlsafe())
                else:
                    data["next_page"] = False

                resp["description"] = "List of locations"
                resp["property"] = "posts"
                resp["data"] = data
        else:
            location = Location.get_by_id(instance_id)
            if location:
                resp["description"] = "Instance data"
                resp["property"] = "posts"
                if self.request.get('show_relief'):
                    resp["data"] = location.to_object(show_relief=True)
                else:
                    resp["data"] = location.to_object()
            else:
                # instance dont exist
                resp['response'] = "invalid_instance"
                resp['code'] = 404
                resp['property'] = "instance_id"
                resp['description'] = "Instance id missing or not valid"

        self.render(resp)

    @oauthed_required
    def post(self, instance_id=None):
        needs = {
           "food": self.request.get("food"),
            "water": self.request.get("water"),
            "medicines": self.request.get("medicines"),
            "social_workers": self.request.get("social_workers"),
            "medical_workers": self.request.get("medical_workers"),
            "shelter": self.request.get("shelter"),
            "formula": self.request.get("formula"),
            "toiletries": self.request.get("toiletries"),
            "flashlights": self.request.get("flashlights"),
            "cloths": self.request.get("cloths"),
        }

        status = {
            "power": self.request.get("power"),
            "communication": self.request.get("communication"),
            "water": self.request.get("status_water"),
            "medicines": self.request.get("status_medicines"),
            "cloths": self.request.get("status_clothes"),
            "food": self.request.get("status_foods"),
            "shelter": self.request.get("status_shelter")
        }

        hash_tag = self.request.get("hash_tag").split(" ")

        data = {
            "name": self.request.get("name"),
            "needs": needs, # json format
            "centers": self.request.get_all("centers"),
            "latlong": self.request.get("latlong"),
            "featured_photo": self.request.get("featured_photo"),
            "death_count": self.request.get("death_count"),
            "affected_count": self.request.get("affected_count"),
            "status_board": self.request.get("status_board"),
            "status": status, # json format
            "hash_tag": hash_tag,
            "images": self.request.get("images")
        }
        # self.params["needs"] = needs
        # self.params["status"] = status
        # self.params["hash_tag"] = hash_tag

        if not instance_id:
            resp["method"] = "create"
            location = add_location(data)
            if location:
                resp["description"] = "Successfully created the instance"
                resp["data"] = location.to_object()
            else:
                # dindt create
                resp['response'] = "cannot_create"
                resp['code'] = 500
                resp['property'] = "add_location"
                resp['description'] = "Server cannot create the instance"
        else:
            resp["method"] = "edit"
            exist = Location.get_by_id(instance_id)
            if exist:
                location = add_location(data, instance_id)
                if location:
                    resp["description"] = "Successfully edited the instance"
                    resp["data"] = location.to_object()
                else:
                    # didnt edi but imposible
                    resp['response'] = "cannot_edit"
                    resp['code'] = 500
                    resp['property'] = "add_location"
                    resp['description'] = "Server cannot create the instance"
            else:
                #instance dont exist
                resp['response'] = "invalid_instance"
                resp['code'] = 404
                resp['property'] = "instance_id"
                resp['description'] = "Instance id missing or not valid"

        self.render(resp)

    @oauthed_required
    def delete(self, instance_id=None):
        resp = API_RESPONSE.copy()
        resp["method"] = "delete"
        if instance_id:
            location = Location.get_by_id(instance_id)
            if location:
                location.key.delete()
                resp["description"] = "Successfully deleted the instance"
            else:
                resp['response'] = "invalid_instance"
                resp['code'] = 404
                resp['property'] = "delete_subscriber"
                resp['description'] = "Instance id not valid"
        else:
            # missing params
            resp['response'] = "missing_params"
            resp['code'] = 406
            resp['property'] = "params"
            resp['description'] = "The request has missing parameters"

        self.render(resp)


class APILContactsHandler(APIBaseHandler):
    def get(self, instance_id=None):
        pass

    def post(self, instance_id=None):
        pass

    def delete(self, instance_id=None):
        pass


class APIOrganizationsHandler(APIBaseHandler):
    def get(self, instance_id=None):
        resp = API_RESPONSE.copy()
        resp["method"] = "get"
        failed = False
        distributors_json = []
        if not instance_id:
            if self.request.get("cursor"):
                try:
                    curs = Cursor(urlsafe=self.request.get("cursor"))
                except Exception, e:
                    resp['response'] = "invalid_cursor"
                    resp['code'] = 406
                    resp['property'] = "cursor"
                    resp['description'] = "Invalid cursor"
                    failed = True
                else:
                    if curs:
                        distributors, next_cursor, more = Distributor.query().fetch_page(25, start_cursor=curs)
                    else:
                        distributors, next_cursor, more = Distributor.query().fetch_page(25)
            else:
                distributors, next_cursor, more = Distributor.query().fetch_page(25)

            if not failed:
                for distributor in distributors:
                    distributors_json.append(distributor.to_object())

                data = {}
                data["organizations"] = distributors_json
                if more:
                    data["next_page"] = "http://api.bangonph.com/v1/distributors?cursor=" + str(next_cursor.urlsafe())
                else:
                    data["next_page"] = False

                resp["description"] = "List of organizations"
                resp["property"] = "posts"
                resp["data"] = data
        else:
            distributers = Distributor.get_by_id(long(instance_id))
            if distributers:
                resp["description"] = "Instance data"
                resp["property"] = "distributers"
                resp["data"] = distributers.to_object()
            else:
                # instance dont exist
                resp['response'] = "invalid_instance"
                resp['code'] = 404
                resp['property'] = "instance_id"
                resp['description'] = "Instance id missing or not valid"

        self.render(resp)

    @oauthed_required
    def post(self, instance_id=None):
        resp = API_RESPONSE.copy()
        data = {
            "email": self.request.get("email"),
            "name": self.request.get("name"),
            "contact_num": self.request.get("contact_num"),
            "website": self.request.get("website"),
            "facebook": self.request.get("facebook")
        }

        if not instance_id:
            resp["method"] = "create"
            distributor = add_distributor(data)
            if distributor:
                resp["description"] = "Successfully edited the instance"
                resp["data"] = distributor.to_object()
            else:
                # foolsafe, failsafe, watever!
                resp['response'] = "cannot_create"
                resp['code'] = 500
                resp['property'] = "add_distributor"
                resp['description'] = "Server cannot create the instance"
        else:
            resp["method"] = "edit"
            exist = Distributor.get_by_id(long(instance_id))
            if exist:
                distributor = add_distributor(data, instance_id)
                if distributor:
                    resp["description"] = "Successfully edited the instance"
                    resp["data"] = distributor.to_object()
                else:
                    # didnt edi but imposible
                    resp['response'] = "cannot_edit"
                    resp['code'] = 500
                    resp['property'] = "add_distributor"
                    resp['description'] = "Server cannot edit the instance"
            else:
                # instance dont exist but imposible
                resp['response'] = "invalid_instance"
                resp['code'] = 404
                resp['property'] = "instance_id"
                resp['description'] = "Instance id missing or not valid"

        self.render(resp)


    @oauthed_required
    def delete(self, instance_id=None):
        resp = API_RESPONSE.copy()
        resp["method"] = "delete"
        if instance_id:
            distributor = Distributor.get_by_id(long(instance_id))
            if distributor:
                distributor.key.delete()
                resp["description"] = "Successfully deleted the instance"
            else:
                resp['response'] = "invalid_instance"
                resp['code'] = 404
                resp['property'] = "delete_subscriber"
                resp['description'] = "Instance id not valid"
        else:
            # missing params
            resp['response'] = "missing_params"
            resp['code'] = 406
            resp['property'] = "params"
            resp['description'] = "The request has missing parameters"

        self.render(resp)


class APIPostsHandler(APIBaseHandler):
    def get(self, instance_id=None):
        resp = API_RESPONSE.copy()
        resp["method"] = "get"
        failed = False
        posts_json = []
        if not instance_id:
            if self.request.get("cursor"):
                try:
                    curs = Cursor(urlsafe=self.request.get("cursor"))
                except Exception, e:
                    resp['response'] = "invalid_cursor"
                    resp['code'] = 406
                    resp['property'] = "cursor"
                    resp['description'] = "Invalid cursor"
                    failed = True

                if curs:
                    # posts, next_cursor, more = Post.query(Post.expiry >= (datetime.datetime.now() - datetime.timedelta(hours=30))).fetch_page(25, start_cursor=curs)
                    posts, next_cursor, more = Post.query().order(-Post.created).fetch_page(100, start_cursor=curs)
                else:
                    # posts, next_cursor, more = Post.query(Post.expiry >= (datetime.datetime.now() - datetime.timedelta(hours=30))).fetch_page(25)
                    posts, next_cursor, more = Post.query().order(-Post.created).fetch_page(100)
            else:
                if self.request.get_all("filter_post_type"):
                    filter_type = self.request.get_all("filter_post_type")[0].upper()
                    date_now = datetime.datetime.now() - datetime.timedelta(hours=30)

                    posts, next_cursor, more = Post.query(Post.post_type.IN([filter_type]), Post.expiry >= date_now).order(-Post.expiry).fetch_page(100)
                else:
                    date_now = datetime.datetime.now() - datetime.timedelta(hours=30)
                    posts, next_cursor, more = Post.query(Post.expiry >= date_now).order(-Post.expiry).fetch_page(100)

            if not failed:
                for post in posts:
                    posts_json.append(post.to_object())

                data = {}
                data["posts"] = posts_json
                if more:
                    data["next_page"] = "http://api.bangonph.com/v1/locations?cursor=" + str(next_cursor.urlsafe())
                else:
                    data["next_page"] = False

                resp["description"] = "List of posts"
                resp["property"] = "posts"
                resp["data"] = data
        else:
            post = Post.get_by_id(instance_id)
            if post:
                resp["description"] = "Instance data"
                resp["property"] = "posts"
                resp["data"] = post.to_object()
            else:
                # instance dont exist
                resp['response'] = "invalid_instance"
                resp['code'] = 404
                resp['property'] = "instance_id"
                resp['description'] = "Instance id missing or not valid"

        self.render(resp)

    def post(self, instance_id=None):
        if self.request.get("comment"):
            logging.warning("Honeypot put!")
            return
        resp = API_RESPONSE.copy()
        if self.request.get("expiry"):
            try:
                expiry = datetime.datetime.strptime(self.request.get("expiry"), "%m/%d/%Y") #1992-10-20
            except:
                resp['response'] = "invalid_date_format"
                resp['code'] = 406
                resp['property'] = "expiry"
                resp['description'] = "Use this format (mm/dd/yyyy)"

                return
        else:
            expiry = datetime.datetime.now() + datetime.timedelta(days=7)

        if not self.request.get('name') and not self.request.get('message'):
            return

        data = {
            "name": self.request.get("name"),
            "email": self.request.get("email"),
            "twitter": self.request.get("twitter"),
            "facebook": self.request.get("facebook"),
            "phone": self.request.get("phone"),
            "message": self.request.get("message"),
            "post_type": self.request.get_all("post_type"),
            "expiry": expiry,
            "status": self.request.get("status"),
            "location": self.request.get("location"),
        }
        # use self.params
        if not instance_id:
            resp["method"] = "create"
            post = add_post(data)
            if post:
                resp["description"] = "Successfully created the instance"
                resp["data"] = post.to_object()
            else:
                # foolsafe, failsafe, watever!
                resp['response'] = "cannot_create"
                resp['code'] = 500
                resp['property'] = "add_post"
                resp['description'] = "Server cannot create the instance"

        else:
            resp["method"] = "edit"
            exist = Post.Post.get_by_id(long(instance_id))
            if exist:
                post = add_post(data, instance_id)
                if post:
                    resp["description"] = "Successfully edited the instance"
                    resp["data"] = post.to_object()
                else:
                    # didnt create but imposible
                    resp['response'] = "cannot_edit"
                    resp['code'] = 500
                    resp['property'] = "add_post"
                    resp['description'] = "Server cannot edit the instance"
            else:
                # instance dont exist but imposible
                resp['response'] = "invalid_instance"
                resp['code'] = 404
                resp['property'] = "instance_id"
                resp['description'] = "Instance id missing or not valid"

        self.render(resp)

        p = pusher.Pusher(
          app_id='59383',
          key='e0a2a1c8316b9baddc9b',
          secret='474177f7aea8c983a7d1'
        )
        post_object = post.to_object()
        p['feeds'].trigger('new_post', post_object)

        form_fields = {
          "app_id": "hjaksv987.bangonph.web",
          "message": post.message + " -" + post.phone + " (Preferably before " + post_object["expiry_friendly"] + ")",
          "name": post.name,
          "address": post.location
        }
        form_data = urllib.urlencode(form_fields)


        try:
            logging.debug(urlfetch.fetch(url="http://reliefboard.com/messages/feed", payload=form_data, method=urlfetch.POST, headers={'Content-Type': 'application/x-www-form-urlencoded'}).content)
        except:
            logging.exception("failed...")


    @oauthed_required
    def delete(self, instance_id=None):
        resp = API_RESPONSE.copy()
        resp["method"] = "delete"
        if instance_id:
            post = Post.get_by_id(long(instance_id))
            if post:
                post.key.delete()
                resp["description"] = "Successfully deleted the instance"
            else:
                resp['response'] = "invalid_instance"
                resp['code'] = 404
                resp['property'] = "delete_post"
                resp['description'] = "Instance id not valid"
        else:
            # missing params
            resp['response'] = "missing_params"
            resp['code'] = 406
            resp['property'] = "params"
            resp['description'] = "The request has missing parameters"

        self.render(resp)


class APIPostSandbox(APIBaseHandler):
    def get(self, instance_id=None):
        resp = API_RESPONSE.copy()
        resp["method"] = "get"
        failed = False
        posts_json = []
        if not instance_id:
            if self.request.get("cursor"):
                try:
                    curs = Cursor(urlsafe=self.request.get("cursor"))
                except Exception, e:
                    resp['response'] = "invalid_cursor"
                    resp['code'] = 406
                    resp['property'] = "cursor"
                    resp['description'] = "Invalid cursor"
                    failed = True

                if curs:
                    posts, next_cursor, more = Post.query(Post.expiry >= (datetime.datetime.now() - datetime.timedelta(hours=30))).fetch_page(25, start_cursor=curs)
                else:
                    posts, next_cursor, more = Post.query(Post.expiry >= (datetime.datetime.now() - datetime.timedelta(hours=30))).fetch_page(25)
            else:
                if self.request.get_all("filter_post_type"):
                    filter_type = self.request.get_all("filter_post_type")[0].upper()
                    date_now = datetime.datetime.now() - datetime.timedelta(hours=30)

                    posts, next_cursor, more = Post.query(Post.post_type.IN([filter_type]), Post.expiry >= date_now).order(-Post.expiry).fetch_page(100)
                else:
                    posts, next_cursor, more = Post.query(Post.expiry >= (datetime.datetime.now() - datetime.timedelta(hours=30))).fetch_page(25)

            if not failed:
                for post in posts:
                    posts_json.append(post.to_object())

                data = {}
                data["posts"] = posts_json
                if more:
                    data["next_page"] = "http://api.bangonph.com/v1/locations?cursor=" + str(next_cursor.urlsafe())
                else:
                    data["next_page"] = False

                resp["description"] = "List of posts"
                resp["property"] = "posts"
                resp["data"] = data
        else:
            post = Post.get_by_id(instance_id)
            if post:
                resp["description"] = "Instance data"
                resp["property"] = "posts"
                resp["data"] = post.to_object()
            else:
                # instance dont exist
                resp['response'] = "invalid_instance"
                resp['code'] = 404
                resp['property'] = "instance_id"
                resp['description'] = "Instance id missing or not valid"

        self.render(resp)

    def post(self, instance_id=None):
        resp = API_RESPONSE.copy()
        if instance_id:
            resp["method"] = "edit"
            exist = Post.Post.get_by_id(long(instance_id))
            if exist:
                post = add_mock_post(data, instance_id)
                if post:
                    resp["description"] = "Successfully edited the instance"
                    resp["data"] = post.to_object()
                else:
                    # didnt create but imposible
                    resp['response'] = "cannot_edit"
                    resp['code'] = 500
                    resp['property'] = "add_post"
                    resp['description'] = "Server cannot edit the instance"
            else:
                # instance dont exist but imposible
                resp['response'] = "invalid_instance"
                resp['code'] = 404
                resp['property'] = "instance_id"
                resp['description'] = "Instance id missing or not valid"

            self.render(resp)

    def delete(self, instance_id=None):
        resp = API_RESPONSE.copy()
        resp["method"] = "delete"
        if instance_id:
            post = Post.get_by_id(long(instance_id))
            if post:
                resp["description"] = "Successfully deleted the instance"
            else:
                resp['response'] = "invalid_instance"
                resp['code'] = 404
                resp['property'] = "delete_post"
                resp['description'] = "Instance id not valid"
        else:
            # missing params
            resp['response'] = "missing_params"
            resp['code'] = 406
            resp['property'] = "params"
            resp['description'] = "The request has missing parameters"

        self.render(resp)


class APIDropOffCentersHandler(APIBaseHandler):
    def get(self, instance_id=None):
        resp = API_RESPONSE.copy()
        centers_json = []
        failed = False
        if not instance_id:
            if self.request.get("cursor"):
                try:
                    curs = Cursor(urlsafe=self.request.get("cursor"))
                except Exception, e:
                    resp['response'] = "invalid_cursor"
                    resp['code'] = 406
                    resp['property'] = "cursor"
                    resp['description'] = "Invalid cursor"
                    failed = True
                if curs:
                    centers, next_cursor, more = DropOffCenter.query().fetch_page(25, start_cursor=curs)
                else:
                    centers, next_cursor, more = DropOffCenter.query().fetch_page(25)
            else:
                centers, next_cursor, more = DropOffCenter.query().fetch_page(25)

            if not failed:
                for center in centers:
                    centers_json.append(center.to_object())

                data = {}
                data["dropOffCenters"] = centers_json
                if more:
                    data["next_page"] = "http://api.bangonph.com/v1/locations?cursor=" + str(next_cursor.urlsafe())
                else:
                    data["next_page"] = False

                resp["description"] = "List of drop off centers"
                resp["property"] = "drop-off-centers"
                resp["data"] = data

        else:
            center = DropOffCenter.get_by_id(instance_id)
            if center:
                resp["description"] = "Instance data"
                resp["property"] = "drop-off-centers"
                resp["data"] = center.to_object()
            else:
                # instance dont exist
                resp['response'] = "invalid_instance"
                resp['code'] = 404
                resp['property'] = "instance_id"
                resp['description'] = "Instance id missing or not valid"

        self.render(resp)

    @oauthed_required
    def post(self, instance_id=None):
        resp = API_RESPONSE.copy()
        data = {
            "drop_off_locations" : self.request.get("drop_off_locations").split(" "),
            "distributor" : self.request.get("distributor").split(", "),
            "address" : self.request.get("address"),
            "name" : self.request.get("name"),
            "latlong" : self.request.get("latlong"),
            "destinations" : self.request.get("destinations"),
            "schedule" : self.request.get("schedule"),
            "twitter" : self.request.get("twitter"),
            "facebook" : self.request.get("facebook"),
            "contacts" : self.request.get("contacts"),
            "email" : self.request.get("email"),
            "id" : self.request.get("id")
        }
        if not instance_id:
            resp["method"] = "create"
            centers = add_drop_off_centers(data)
            if centers:
                self.render(centers.to_object())
                resp["description"] = "Successfully created the instance"
                resp["data"] = post.to_object()
            else:
                # foolsafe, failsafe, watever!
                resp['response'] = "cannot_create"
                resp['code'] = 500
                resp['property'] = "add drop off centers"
                resp['description'] = "Server cannot create the instance"
        else:
            resp["method"] = "edit"
            centers = add_drop_off_centers(data, instance_id)
            if centers:
                resp["description"] = "Successfully edited the instance"
                resp["data"] = post.to_object()
            else:
                # instance dont exist but imposible
                resp['response'] = "invalid_instance"
                resp['code'] = 404
                resp['property'] = "instance_id"
                resp['description'] = "Instance id missing or not valid"

        self.render(resp)

    @oauthed_required
    def delete(self, instance_id=None):
        resp = API_RESPONSE.copy()
        resp["method"] = "delete"
        if instance_id:
            center = DropOffCenter.get_by_id(instance_id)
            if center:
                center.key.delete()
                resp["description"] = "Successfully deleted the instance"
            else:
                resp['response'] = "invalid_instance"
                resp['code'] = 404
                resp['property'] = "delete_center"
                resp['description'] = "Instance id not valid"
        else:
            # missing params
            resp['response'] = "missing_params"
            resp['code'] = 406
            resp['property'] = "params"
            resp['description'] = "The request has missing parameters"

        self.render(resp)


class APISubscribersHandler(APIBaseHandler):
    def get(self, instance_id=None):
        subscribers_json = []
        if not instance_id:
            if self.request.get("cursor"):
                curs = Cursor(urlsafe=self.request.get("cursor"))
                if curs:
                    subscribers, next_cursor, more = Subscriber.query().fetch_page(10, start_cursor=curs)
                else:
                    subscribers, next_cursor, more = Subscriber.query().fetch_page(10)
            else:
                subscribers, next_cursor, more = Subscriber.query().fetch_page(10)

            for subscriber in subscribers:
                subscribers_json.append(subscriber.to_object())

            data = {}
            data["subscribers"] = subscribers_json
            if more:
                data["next_page"] = "http://api.bangonph.com/v1/subscribers?cursor=" + str(next_cursor.urlsafe())
            else:
                data["next_page"] = False
            self.render(data)
        else:
            center = Subscriber.get_by_id(long(instance_id))
            if center:
                self.render(center.to_object(self.request.get('expand')))

    @oauthed_required
    def post(self, instance_id=None):
        resp = API_RESPONSE.copy()
        data = API_RESPONSE_DATA.copy()
        if check_all_keys(["name", "email", "distribution"], self.params):
            if instance_id:
                resp["method"] = "edit"
                exist = Subscriber.get_by_id(long(instance_id))
                if exist:
                    # edit instance
                    subscriber = add_subcriber(self.params, instance_id)
                    if subscriber:
                        distribution = subscriber.distribution.get() if subscriber.distribution else None # get the id of the parent
                        resp["description"] = "Successfully edited the instance"
                        resp["data"] = subscriber.to_object(self.request.get("expand"))
                    else:
                        # foolsafe, failsafe, watever!
                        resp['response'] = "cannot_edit"
                        resp['code'] = 500
                        resp['property'] = "add_subcriber"
                        resp['description'] = "Server cannot create the instance"
                else:
                    # instance doesnt exist
                    resp['response'] = "invalid_instance"
                    resp['code'] = 404
                    resp['property'] = "instance_id"
                    resp['description'] = "Instance id missing or not valid"
            else:
                resp["method"] = "create"
                # new instance
                subscriber = add_subcriber(self.params)
                if subscriber:
                    distribution = subscriber.distribution.get() if subscriber.distribution else None # get the id of the parent
                    resp["description"] = "Successfully created the instance"
                    resp["data"] = subscriber.to_object(self.request.get("expand"))
                else:
                    # foolsafe, failsafe, watever!
                    resp['response'] = "cannot_create"
                    resp['code'] = 500
                    resp['property'] = "add_subcriber"
                    resp['description'] = "Server cannot create the instance"

        else:
            resp = API_RESPONSE.copy()
            # missing params
            resp['response'] = "missing_params"
            resp['code'] = 406
            resp['property'] = "params"
            resp['description'] = "The request has missing parameters"

        self.render(resp)

    @oauthed_required
    def delete(self, instance_id=None):
        resp = API_RESPONSE.copy()
        resp["method"] = "delete"
        if instance_id:
            subscriber = Subscriber.get_by_id(long(instance_id))
            if subscriber:
                subscriber.key.delete()
                resp["description"] = "Successfully deleted the instance"
            else:
                resp['response'] = "invalid_instance"
                resp['code'] = 404
                resp['property'] = "delete_subscriber"
                resp['description'] = "Instance id not valid"
        else:
            # missing params
            resp['response'] = "missing_params"
            resp['code'] = 406
            resp['property'] = "params"
            resp['description'] = "The request has missing parameters"

        self.render(resp)

class APIEffortsHandler(APIBaseHandler):
    def get(self, instance_id=None):
        resp = API_RESPONSE.copy()
        resp["method"] = "get"
        failed = False
        efforts_json = []
        if not instance_id:
            if self.request.get("cursor"):
                try:
                    curs = Cursor(urlsafe=self.request.get("cursor"))
                except Exception, e:
                    resp['response'] = "invalid_cursor"
                    resp['code'] = 406
                    resp['property'] = "cursor"
                    resp['description'] = "Invalid cursor"
                    failed = True
                else:
                    if curs:
                        efforts, next_cursor, more = DistributionRevision.query().fetch_page(25, start_cursor=curs)
                    else:
                        efforts, next_cursor, more = DistributionRevision.query().fetch_page(25)
            else:
                if self.request.get("filter_locations"):
                    loc = slugify(self.request.get("filter_locations"))
                    loc_key = Location.get_by_id(loc)
                    efforts, next_cursor, more  = DistributionRevision.query(DistributionRevision.destinations == loc_key.key).fetch_page(25)
                else:
                    efforts, next_cursor, more = DistributionRevision.query().fetch_page(25)

            for effort in efforts:
                efforts_json.append(effort.to_object(self.request.get("expand").lower()))

            if not failed:
                data = {}
                data["efforts"] = efforts_json
                if more:
                    data["next_page"] = "http://api.bangonph.com/v1/efforts?cursor=" + str(next_cursor.urlsafe())
                else:
                    data["next_page"] = False

                resp["description"] = "List of efforts"
                resp["property"] = "efforts"
                resp["data"] = data

        else:
            effort = DistributionRevision.get_by_id(long(instance_id))
            if effort:
                resp["description"] = "Instance data"
                resp["property"] = "posts"
                resp["data"] = effort.to_object()
            else:
                # instance dont exist
                resp['response'] = "invalid_instance"
                resp['code'] = 404
                resp['property'] = "instance_id"
                resp['description'] = "Instance id missing or not valid"

        self.render(resp)

    @oauthed_required
    def post(self, instance_id=None):
        resp = API_RESPONSE.copy()
        # if self.request.get("date_of_distribution"):
        #     try:
        #         date = datetime.datetime.strptime(self.request.get("date_of_distribution"), "%Y-%m-%d"), #1992-10-20
        #     except:
        #         resp['response'] = "invalid_date_format"
        #         resp['code'] = 406
        #         resp['property'] = "date_of_distribution"
        #         resp['description'] = "Use this format (YYYY-mm-dd H:M:S)"
        # else:
        #     date = None
        data = {
            "date_of_distribution": self.request.get("date_of_distribution"),
            "contact": self.request.get("contact"),
            "destinations": self.request.get("destinations"),
            "supply_goal": self.request.get("supply_goal"),
            "actual_supply": self.request.get("actual_supply"),
            "images": self.request.get("images"),
            "fb_email": self.request.get("fb_email"),
            "fb_id": self.request.get("fb_id"),
            "fb_access_token": self.request.get("fb_access_token"),
            "fb_username": self.request.get("fb_username"),
            "fb_lastname": self.request.get("fb_lastname"),
            "fb_firstname": self.request.get("fb_firstname"),
            "fb_middlename": self.request.get("fb_middlename"),
            "fb_name": self.request.get("fb_name"),
            "name": self.request.get("name"),
            "relief_name": self.request.get("relief_name"),
            "num_of_packs": self.request.get("num_of_packs"),
            "description": self.request.get("description"),
            "needs": self.request.get("needs"),
            "tag": self.request.get("tag")
        }

        # self.params["date_of_distribution"] = date

        if not instance_id:
            resp["method"] = "create"
            effort = add_distribution(data)
            if effort:
                resp["description"] = "Successfully created the instance"
                resp["data"] = effort.to_object()
            else:
                # foolsafe, failsafe, watever!
                resp['response'] = "cannot_create"
                resp['code'] = 500
                resp['property'] = "add_distribution"
                resp['description'] = "Server cannot create the instance"

        else:
            resp["method"] = "edit"
            exist = DistributionRevision.get_by_id(long(instance_id))
            if exist:
                effort = add_distribution(data, instance_id)
                if effort:
                    resp["description"] = "Successfully edited the instance"
                    resp["data"] = effort.to_object()
                else:
                    # didnt edi but imposible
                    resp['response'] = "cannot_edit"
                    resp['code'] = 500
                    resp['property'] = "add_distribution"
                    resp['description'] = "Server cannot create the instance"
            else:
                resp['response'] = "invalid_instance"
                resp['code'] = 404
                resp['property'] = "instance_id"
                resp['description'] = "Instance id missing or not valid"

        self.render(resp)

    @oauthed_required
    def delete(self, instance_id=None):
        resp = API_RESPONSE.copy()
        resp["method"] = "delete"
        if instance_id:
            effort = DistributionRevision.get_by_id(long(instance_id))
            if effort:
                subscriber.key.delete()
                resp["description"] = "Successfully deleted the instance"
            else:
                resp['response'] = "invalid_instance"
                resp['code'] = 404
                resp['property'] = "delete_subscriber"
                resp['description'] = "Instance id not valid"
        else:
            # missing params
            resp['response'] = "missing_params"
            resp['code'] = 406
            resp['property'] = "params"
            resp['description'] = "The request has missing parameters"

        self.render(resp)


class APIContactsHandler(APIBaseHandler):
    def get(self, instance_id=None):
        resp = API_RESPONSE.copy()
        resp["method"] = "get"
        failed = False
        contacts_json = []
        if not instance_id:
            if self.request.get("cursor"):
                try:
                    curs = Cursor(urlsafe=self.request.get("cursor"))
                except Exception, e:
                    resp['response'] = "invalid_cursor"
                    resp['code'] = 406
                    resp['property'] = "cursor"
                    resp['description'] = "Invalid cursor"
                    failed = True
                else:
                    if curs:
                        contacts, next_cursor, more = Contact.query().fetch_page(25, start_cursor=curs)
                    else:
                        contacts, next_cursor, more = Contact.query().fetch_page(25)
            else:
                contacts, next_cursor, more = Contact.query().fetch_page(25)

            if not failed:
                for contact in contacts:
                    contacts_json.append(contact.to_object())

                data = {}
                data["locations"] = contacts_json
                if more:
                    data["next_page"] = "http://api.bangonph.com/v1/contacts?cursor=" + str(next_cursor.urlsafe())
                else:
                    data["next_page"] = False

                resp["description"] = "List of contacts"
                resp["property"] = "contacts"
                resp["data"] = data
        else:
            contacts = Contact.get_by_id(instance_id)
            if contacts:
                resp["description"] = "Instance data"
                resp["property"] = "posts"
                resp["data"] = contacts.to_object()
            else:
                # instance dont exist
                resp['response'] = "invalid_instance"
                resp['code'] = 404
                resp['property'] = "instance_id"
                resp['description'] = "Instance id missing or not valid"

        self.render(resp)

    @oauthed_required
    def post(self, instance_id=None):
        resp = API_RESPONSE.copy()
        data = {}
        data["name"] = self.request.get("name")
        data["contacts"] = self.request.get("contacts")
        data["email"] = self.request.get("email")
        data["facebook"] = self.request.get("facebook")
        data["twitter"] = self.request.get("twitter")

        if not instance_id:
            resp["method"] = "create"
            contact = add_contact(data)
            if contact:
                resp["description"] = "Successfully edited the instance"
                resp["data"] = contact.to_object()
            else:
                # foolsafe, failsafe, watever!
                resp['response'] = "cannot_create"
                resp['code'] = 500
                resp['property'] = "add_contact"
                resp['description'] = "Server cannot create the instance"
        else:
            resp["method"] = "edit"
            exist = Contact.get_by_id(int(instance_id))
            if exist:
                contact = add_contact(data, instance_id)
                if contact:
                    resp["description"] = "Successfully edited the instance"
                    resp["data"] = contact.to_object()
                else:
                    resp['response'] = "cannot_edit"
                    resp['code'] = 500
                    resp['property'] = "add_contact"
                    resp['description'] = "Server cannot create the instance"
            else:
                # instance dont exist but imposible
                resp['response'] = "invalid_instance"
                resp['code'] = 404
                resp['property'] = "instance_id"
                resp['description'] = "Instance id missing or not valid"

        self.render(resp)

    @oauthed_required
    def delete(self, instance_id=None):
        resp = API_RESPONSE.copy()
        resp["method"] = "delete"
        if instance_id:
            contact = Contact.get_by_id(long(instance_id))
            if effort:
                subscriber.key.delete()
                resp["description"] = "Successfully deleted the instance"
            else:
                resp['response'] = "invalid_instance"
                resp['code'] = 404
                resp['property'] = "delete_subscriber"
                resp['description'] = "Instance id not valid"
        else:
            # missing params
            resp['response'] = "missing_params"
            resp['code'] = 406
            resp['property'] = "params"
            resp['description'] = "The request has missing parameters"

        self.render(resp)


class APIDistributorsHandler(APIBaseHandler):
    def get(self, instance_id=None):
        resp = API_RESPONSE.copy()
        resp["method"] = "get"
        failed = False
        distributors_json = []
        if not instance_id:
            if self.request.get("cursor"):
                try:
                    curs = Cursor(urlsafe=self.request.get("cursor"))
                except Exception, e:
                    resp['response'] = "invalid_cursor"
                    resp['code'] = 406
                    resp['property'] = "cursor"
                    resp['description'] = "Invalid cursor"
                    failed = True
                else:
                    if curs:
                        distributors, next_cursor, more = Distributor.query().fetch_page(25, start_cursor=curs)
                    else:
                        distributors, next_cursor, more = Distributor.query().fetch_page(25)
            else:
                distributors, next_cursor, more = Distributor.query().fetch_page(25)

            if not failed:
                for distributor in distributors:
                    distributors_json.append(distributor.to_object())

                data = {}
                data["efforts"] = distributors_json
                if more:
                    data["next_page"] = "http://api.bangonph.com/v1/distributors?cursor=" + str(next_cursor.urlsafe())
                else:
                    data["next_page"] = False

                resp["description"] = "List of efforts"
                resp["property"] = "posts"
                resp["data"] = data
        else:
            distributers = Distributor.get_by_id(instance_id)
            if distributers:
                resp["description"] = "Instance data"
                resp["property"] = "distributers"
                resp["data"] = distributers.to_object()
            else:
                # instance dont exist
                resp['response'] = "invalid_instance"
                resp['code'] = 404
                resp['property'] = "instance_id"
                resp['description'] = "Instance id missing or not valid"

        self.render(resp)

    @oauthed_required
    def post(self, instance_id=None):
        resp = API_RESPONSE.copy()
        data = {
            "email": self.request.get("email"),
            "name": self.request.get("name"),
            "contact_num": self.request.get("contact_num"),
            "website": self.request.get("website"),
            "facebook": self.request.get("facebook")
        }

        if not instance_id:
            resp["method"] = "create"
            distributor = add_distributor(data)
            if distributor:
                resp["description"] = "Successfully edited the instance"
                resp["data"] = distributor.to_object()
            else:
                # foolsafe, failsafe, watever!
                resp['response'] = "cannot_create"
                resp['code'] = 500
                resp['property'] = "add_distributor"
                resp['description'] = "Server cannot create the instance"
        else:
            resp["method"] = "edit"
            exist = Distributor.get_by_id(long(instance_id))
            if exist:
                distributor = add_distributor(data, instance_id)
                if distributor:
                    resp["description"] = "Successfully edited the instance"
                    resp["data"] = distributor.to_object()
                else:
                    # didnt edi but imposible
                    resp['response'] = "cannot_edit"
                    resp['code'] = 500
                    resp['property'] = "add_distributor"
                    resp['description'] = "Server cannot edit the instance"
            else:
                # instance dont exist but imposible
                resp['response'] = "invalid_instance"
                resp['code'] = 404
                resp['property'] = "instance_id"
                resp['description'] = "Instance id missing or not valid"

        self.render(resp)


    @oauthed_required
    def delete(self, instance_id=None):
        resp = API_RESPONSE.copy()
        resp["method"] = "delete"
        if instance_id:
            distributor = Distributor.get_by_id(long(instance_id))
            if distributor:
                distributor.key.delete()
                resp["description"] = "Successfully deleted the instance"
            else:
                resp['response'] = "invalid_instance"
                resp['code'] = 404
                resp['property'] = "delete_subscriber"
                resp['description'] = "Instance id not valid"
        else:
            # missing params
            resp['response'] = "missing_params"
            resp['code'] = 406
            resp['property'] = "params"
            resp['description'] = "The request has missing parameters"

        self.render(resp)


class APIMainHandler(APIBaseHandler):
    def get(self):
        resp = API_RESPONSE.copy()
        resp["method"] = "get"
        failed = False
        data = {}
        data["versions"] = [{
            "meta": {
                "href": "http://api.bangonph.com/v1"
            },
            "description": "Version 1"
        }]

        resp["description"] = "List of API Versions"
        resp["property"] = "all"
        resp["data"] = data

        self.render(resp)


class APIV1Handler(APIBaseHandler):
    def get(self):
        resp = API_RESPONSE.copy()
        resp["method"] = "get"
        failed = False
        data = {}
        data["apis"] = [{
            "meta": {
                "href": "http://api.bangonph.com/v1/locations"
                },
            "description": "Affected Locations"
        },{
            "meta": {
                "href": "http://api.bangonph.com/v1/posts"
                },
            "description": "Posts or Messages"
        },{
            "meta": {
                "href": "http://api.bangonph.com/v1/efforts"
                },
            "description": "Relief Efforts"
        },{
            "meta": {
                "href": "http://api.bangonph.com/v1/orgs"
                },
            "description": "Relief Organizations"
        },{
            "meta": {
                "href": "http://api.bangonph.com/v1/drop-off-centers"
                },
            "description": "Drop Off Centers"
        }]

        resp["description"] = "List of API endpoints"
        resp["property"] = "all"
        resp["data"] = data

        self.render(resp)


class APIErrorHandler(APIBaseHandler):
    def get(self, page=None):
        self.redirect('/')


class UploadPage(BaseHandler):
    @login_required
    def get(self):
        self.tv['upload_url'] = blobstore.create_upload_url('/upload/handler')
        self.tv['files'] = File.query().fetch(500)
        self.render('frontend/upload-file.html')


class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        upload_files = self.get_uploads('file')
        title = self.request.get('title').strip()
        title_code = slugify(title)
        blob_info = upload_files[0]
        blob_key = blob_info.key()

        f = File(id=title_code)
        f.title = title
        f.blob_key = blob_key
        try:
            f.img_serving = images.get_serving_url(blob_key)
        except:
            logging.exception("Not an image?")
        f.put()

        self.redirect("/upload?success=File%20Uploaded")


class ReComputeReliefStatus(webapp2.RequestHandler):
    def get(self):
        # Compute Everything
        distributors = Distributor.query(Distributor.name != None)
        d = []
        for distributor in distributors:
            try:
                distributor.handle = sanitize(distributor.name)
                d.append(distributor)
            except:
                logging.exception("something went wrong")
        ndb.put_multi(d)
        self.response.write('done')

        # locations = DistributionRevision.query()
        # date = get_current_date()
        # distributions = []
        # for location in locations:
        #     if location.date <= date:
        #         location.status = 'MISSION ACCOMPLISHED'
        #     else:
        #         location.status = 'UNKNOWN'
        #     distributions.append(location)
        # ndb.put_multi(distributions)


class ComputeReliefStatus(webapp2.RequestHandler):
    def get(self):
        # Compute Everything
        locations = Location.query()
        for location in locations:
            location_id = location.key.id()
            params = {
                "location_id": location_id
            }
            taskqueue.add(url='/admin/tasks/compute_relief_status', params=params, method='POST')

    def post(self):
        if not self.request.get('location_id'):
            logging.error("Location ID not given")
            return

        location = Location.get_by_id(self.request.get('location_id'))
        if not location:
            logging.error("Location not found")
            return

        # Get Relief Efforts
        distributions = DistributionRevision.query(DistributionRevision.name == location.key.id())

        food_total = {}
        hygiene_total = {}
        medicine_total = {}
        medical_mission_total = {}
        shelter_total = {}
        unknown_total = {}

        for distribution in distributions:
            if distribution.tag == "FOOD & WATER":
                if distribution.num_of_packs:
                    if distribution.date not in food_total:
                        food_total[distribution.date] = distribution.num_of_packs
                    else:
                        food_total[distribution.date] += distribution.num_of_packs
            elif distribution.tag == "SHELTER":
                if distribution.num_of_packs:
                    if distribution.date not in shelter_total:
                        shelter_total[distribution.date] = distribution.num_of_packs
                    else:
                        shelter_total[distribution.date] += distribution.num_of_packs
            elif distribution.tag == "MEDICINE":
                if distribution.num_of_packs:
                    if distribution.date not in medicine_total:
                        medicine_total[distribution.date] = distribution.num_of_packs
                    else:
                        medicine_total[distribution.date] += distribution.num_of_packs
            elif distribution.tag == "HYGIENE":
                if distribution.num_of_packs:
                    if distribution.date not in hygiene_total:
                        hygiene_total[distribution.date] = distribution.num_of_packs
                    else:
                        hygiene_total[distribution.date] += distribution.num_of_packs
            elif distribution.tag == "MEDICAL MISSION":
                if distribution.num_of_packs:
                    if distribution.date not in medical_mission_total:
                        medical_mission_total[distribution.date] = distribution.num_of_packs
                    else:
                        medical_mission_total[distribution.date] += distribution.num_of_packs
            else:
                if distribution.num_of_packs:
                    if distribution.date not in unknown_total:
                        unknown_total[distribution.date] = distribution.num_of_packs
                    else:
                        unknown_total[distribution.date] += distribution.num_of_packs

        location.relief_aid_totals = {}
        for date in DATES:
            location.relief_aid_totals[date] = {'food': 0, 'hygiene': 0, 'shelter':0, 'medicine':0, 'medical_mission':0, 'unknown':0}
            try:
                location.relief_aid_totals[date]['food'] = food_total[date]
            except:
                pass
            try:
                location.relief_aid_totals[date]['shelter'] = shelter_total[date]
            except:
                pass
            try:
                location.relief_aid_totals[date]['hygiene'] = hygiene_total[date]
            except:
                pass
            try:
                location.relief_aid_totals[date]['medicine'] = medicine_total[date]
            except:
                pass
            try:
                location.relief_aid_totals[date]['medical_mission'] = medical_mission_total[date]
            except:
                pass
            try:
                location.relief_aid_totals[date]['unknown'] = unknown_total[date]
            except:
                pass
        location.put()


class UploadDistributionRevisionScript(BaseHandler):
    def get(self):
        self.render('frontend/system-overide-uploader.html')

    def post(self):
        if self.request.get('file'):
            stringReader = csv.reader(StringIO(self.request.get('file')))

            for row in stringReader:
                res = add_rev(row)
                if res == "Success":
                    res = "<span style=\"background-color: green; color: white\">" + res + "</span>"
                else:
                    res = "<span style=\"background-color: red; color: white\">" + res + "</span>"
                self.response.out.write(str(row[0]) +", " + str(row[1]) + ", " + str(row[4]) + " ---> " + res + "<br>")

        else:
            self.tv['error'] = "Please select a file first."
            self.render('frontend/system-overide-uploader.html')


app = webapp2.WSGIApplication([
    routes.DomainRoute(r'<:gcdc2013-bangonph\.appspot\.com|www\.bangonph\.com|staging\.gcdc2013-bangonph\.appspot\.com|localhost>', [

        webapp2.Route('/', handler=PublicFrontPage, name="www-front"),
        webapp2.Route('/updates', handler=PublicUpdatesPage, name="www-updates"),
        webapp2.Route('/reliefoperations', handler=ReliefOperationsPage, name="www-reliefoperations"),
        webapp2.Route(r'/locations/<:.*>/edit', handler=PublicLocationEditPage, name="www-locations-edit"),
        webapp2.Route(r'/locations/<:.*>', handler=PublicLocationPage, name="www-locations"),
        webapp2.Route('/posts', handler=PublicPostPage, name="www-public-post"),
        webapp2.Route(r'/posts/<:.*>', handler=PublicPostPage, name="www-public-post"),

        webapp2.Route('/api/posts', handler=APIPostsHandler, name="www-api-posts"),
        webapp2.Route(r'/api/posts/<:.*>', handler=APIPostsHandler, name="www-api-posts"),

        webapp2.Route('/orgs', handler=OrgsHandler, name="www-orgs"),
        webapp2.Route('/orgs/new-org', handler=OrgsNewHandler, name="www-orgs-new"),
        webapp2.Route(r'/orgs/<org>/edit', handler=OrgsEditHandler, name="www-orgs-edit"),
        webapp2.Route(r'/orgs/<org>', handler=OrgsViewHandler, name="www-orgs-view"),
        webapp2.Route(r'/orgs/<org>/new-relief', handler=OrgsNewReliefHandler, name="www-orgs-new-relief"),

        webapp2.Route('/fblogin', handler=PublicFBLoginPage, name="www-publicfblogin"),
        webapp2.Route('/logout', handler=PublicLogout, name="www-public-logout"),

        # richmond:
        webapp2.Route('/s', handler=sampler, name="www-get-authorization-code"),

        webapp2.Route('/admin/tasks/compute_relief_status', handler=ComputeReliefStatus, name="www-compute-relief-status"),
        webapp2.Route('/admin/scripts/recompute_relief', handler=ReComputeReliefStatus, name="www-recompute-relief-status"),
        webapp2.Route('/admin/api/v1/locations', handler=APILocationsHandler, name="admin-api-locations"),

        webapp2.Route(r'/<:.*>', ErrorHandler)
    ]),
    routes.DomainRoute(r'<:admin\.bangonph\.com>', [
        webapp2.Route('/', handler=FrontPage, name="www-front"),
        webapp2.Route('/register', handler=RegisterPage, name="www-register"),
        webapp2.Route('/logout', handler=Logout, name="www-logout"),
        webapp2.Route('/login', handler=LoginPage, name="www-login"),
        webapp2.Route('/fblogin', handler=FBLoginPage, name="www-fblogin"),
        webapp2.Route('/dashboard', handler=DashboardPage, name="www-dashboard"),
        webapp2.Route('/cosmo', handler=CosmoPage, name="www-test"),

        # leonard gwapo:
        webapp2.Route('/locations', handler=LocationHandler, name="www-locations"),
        webapp2.Route('/users', handler=UserHandler, name="www-users"),
        webapp2.Route('/posts', handler=PostsHandler, name="www-post"),
        webapp2.Route('/distributions', handler=DistributionHandler, name="www-distributions"),
        webapp2.Route('/distributions/fetch', handler=DistributionFetchHandler, name="www-distributions-fetch"),
        webapp2.Route('/distributions/fetch/2', handler=DistributionFetch2Handler, name="www-distributions-fetch2"),
        webapp2.Route('/distributors', handler=DistributorHandler, name="www-distributors"),

        webapp2.Route('/contacts', handler=ContactHandler, name="www-contacts"),
        webapp2.Route('/drop-off-centers', handler=CentersHandler, name="www-centers"),


        webapp2.Route('/subscribers', handler=SubscriberPage, name="www-subscribers"),
        webapp2.Route('/upload', handler=UploadPage, name="www-upload"),
        webapp2.Route('/upload/handler', handler=UploadHandler, name="www-upload-handler"),
        webapp2.Route('/distributors', handler=DistributorHandler, name="www-distributors"),
        webapp2.Route('/distributions/fetch', handler=DistributionFetchHandler, name="www-distributions-fetch"),


        webapp2.Route('/system/override/scripts/upload', handler=UploadDistributionRevisionScript, name="www-upload-distribution"),



        # richmond:
        webapp2.Route('/s', handler=sampler, name="www-get-authorization-code"),

        webapp2.Route(r'/<:.*>', ErrorHandler)
    ]),

    routes.DomainRoute(r'<:api\.bangonph\.com>', [
        webapp2.Route('/', handler=APIMainHandler, name="api-locations"),
        webapp2.Route('/v1', handler=APIV1Handler, name="api-locations"),
        webapp2.Route('/v1/locations', handler=APILocationsHandler, name="api-locations"),
        webapp2.Route('/v1/users', handler=APIUsersHandler, name="api-users"),
        webapp2.Route('/v1/contacts', handler=APIContactsHandler, name="api-locations"),
        webapp2.Route('/v1/posts', handler=APIPostsHandler, name="api-locations"),
        webapp2.Route('/v1/drop-off-centers', handler=APIDropOffCentersHandler, name="api-locations"),
        webapp2.Route('/v1/subscribers', handler=APISubscribersHandler, name="api-subscribers"),
        webapp2.Route('/v1/orgs', handler=APIOrganizationsHandler, name="api-locations"),
        webapp2.Route('/v1/efforts', handler=APIEffortsHandler, name="api-locations"),
        webapp2.Route('/v1/distributors', handler=APIDistributorsHandler, name="api-locations"),
        webapp2.Route('/v1/posts/sandbox', handler=APIPostSandbox, name="api-locations"),


        webapp2.Route(r'/v1/distributors/<:.*>', handler=APIDistributorsHandler, name="api-locations"),
        webapp2.Route(r'/v1/posts/sandbox/<:.*>', handler=APIPostSandbox, name="api-locations"),
        webapp2.Route(r'/v1/locations/<:.*>', handler=APILocationsHandler, name="api-locations"),
        webapp2.Route(r'/v1/users/<:.*>', handler=APIUsersHandler, name="api-users"),
        webapp2.Route(r'/v1/contacts/<:.*>', handler=APIContactsHandler, name="api-locations"),
        webapp2.Route(r'/v1/posts/<:.*>', handler=APIPostsHandler, name="api-locations"),
        webapp2.Route(r'/v1/drop-off-centers/<:.*>', handler=APIDropOffCentersHandler, name="api-locations"),
        webapp2.Route(r'/v1/subscribers/<:.*>', handler=APISubscribersHandler, name="api-subscribers"),
        webapp2.Route(r'/v1/orgs/<:.*>', handler=APIOrganizationsHandler, name="api-locations"),
        webapp2.Route(r'/v1/efforts/<:.*>', handler=APIEffortsHandler, name="api-locations"),

        # richmond:
        webapp2.Route('/v1/oauth/authorize', handler=GetUserToken, name="api-get-user-token"),
        webapp2.Route('/s', handler=sampler, name="api-get-authorization-code"),

        webapp2.Route(r'/<:.*>', APIErrorHandler)
    ])
])


