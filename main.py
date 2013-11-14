import webapp2, jinja2, os, calendar
from webapp2_extras import routes
from models import User, Contact, Location, Post, Distribution, File, Distributor, Subscriber, DropOffCenter
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
from oauth_models import *

from google.appengine.api import urlfetch
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import images

from settings import SETTINGS, API_RESPONSE, API_RESPONSE_DATA
from settings import SECRET_SETTINGS
from settings import OAUTH_RESP, API_OAUTH_RESP

from google.appengine.datastore.datastore_query import Cursor

jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)), autoescape=True)


def with_commas(value):
    return "{:,}".format(value)


jinja_environment.filters['with_commas'] = with_commas


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


    def render(self, template_path=None, force=False):
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
        self.response.out.write(template.render(self.tv))
        logging.debug(self.tv)


    def get_session(self):
        from gaesessions import get_current_session
        return get_current_session()


    def get_current_user(self):
        if self.session.has_key("user"):
            user = User.get_by_id(self.session["user"])
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
        self.tv["current_page"] = "PUBLIC_FRONT"
        self.tv['locations'] = Location.query().fetch(100)
        self.render('frontend/public-front.html')


class LocationSamplePage(BaseHandler):
    def get(self):
        self.tv["current_page"] = "LOCATIONSAMPLE"
        self.render('frontend/locationsample.html')


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

        self.tv['location'] = location.to_object()
        self.tv['page_title'] = location.name

        self.render('frontend/public-location.html')


class ReliefOperationsPage(BaseHandler):
    def get(self):
        self.tv["current_page"] = "RELIEF_OPERATIONS"
        self.render('frontend/reliefoperations.html')


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
        if contacts:
            datas = []
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
                self.response.out.write(simplejson.dumps(temp))
            return

        locations = Location.query().order(-Location.created).fetch(300)
        if locations:
            datas = []
            for location in locations:
                temp = {}
                temp["id"] = location.key.id()
                temp["name"] = location.name
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
                        if new_urls[i]["src"] != "" or new_titles[i]["image_title"] != "" or new_captions[i]["image_caption"] != "":
                            images = {}
                            images["src"] = new_urls[i]["src"]
                            images["image_title"] = new_titles[i]["image_title"]
                            images["image_caption"] = new_captions[i]["image_caption"]
                            location.images.append(images)
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
                location.latlong = self.request.get("latlong")
                location.featured_photo = self.request.get("featured_photo")
                location.death_count = int(self.request.get("death_count"))
                location.death_count_text = self.request.get("death_count_text")
                location.affected_count = int(self.request.get("affected_count"))
                location.affected_count_text = self.request.get("affected_count_text")
                location.status_board = self.request.get("status_board")
                location.needs = needs
                location.status = status
                location.hash_tag = self.request.get("hash_tag").split(" ")
                location.put()

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
            data = {
                "name": self.request.get("name"),
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
                "hash_tag" : hash_tag
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
        if distributions:
            datas = []
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
        if distributors:
            datas = []
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
            distributor.name = self.request.get("name")
            distributor.contact_num = self.request.get("contact_num")
            distributor.email = self.request.get("email")
            distributor.website = self.request.get("website")
            distributor.facebook = self.request.get("facebook")
            distributor.contact_details = self.request.get("contact_details")
            distributor.put()
        else:
            distributor = Distributor()
            distributor.name = self.request.get("name")
            distributor.contact_num = self.request.get("contact_num")
            distributor.email = self.request.get("email")
            distributor.website = self.request.get("website")
            distributor.facebook = self.request.get("facebook")
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
        if dropOffCenters:
            datas = []
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
        posts = Post.query().order(-Post.created).fetch(300)
        if posts:
            datas = []
            for post in posts:
                temp = {}
                temp["id"] = post.key.id()
                temp["name"] = post.name
                temp["phone"] = post.phone
                temp["email"] = post.email
                temp["facebook"] = post.facebook
                temp["twitter"] = post.twitter
                temp["message"] = post.message
                datas.append(temp)
            self.response.out.write(simplejson.dumps(datas))

    def post(self):
        data = {
            "name": self.request.get("name"),
            "email": self.request.get("email"),
            "twitter": self.request.get("twitter"),
            "facebook": self.request.get("facebook"),
            "phone": self.request.get("phone"),
            "message": self.request.get("message"),
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
    def get(self, instance_id=None):
        users_json = []
        if not instance_id:
            if self.request.get("cursor"):
                curs = Cursor(urlsafe=self.request.get("cursor"))
                if curs:
                    users, next_cursor, more = User.query().fetch_page(25, start_cursor=curs)
                else:
                    users, next_cursor, more = User.query().fetch_page(25)
            else:
                users, next_cursor, more = User.query().fetch_page(25)

            for user in users:
                users_json.append(user.to_object())

            data = {}
            data["users"] = users_json
            if more:
                data["next_page"] = "http://api.bangonph.com/v1/users?cursor=" + str(next_cursor.urlsafe())
            else:
                data["next_page"] = False
            self.render(data)
        else:
            user = User.get_by_id(instance_id)
            users_json.append(user.to_object())
            self.render(users_json)

    def post(self, instance_id=None):
        pass

    def delete(self, instance_id=None):
        pass

class APILocationsHandler(APIBaseHandler):
    def get(self, instance_id=None):
        locations_json = []
        if not instance_id:
            if self.request.get("cursor"):
                curs = Cursor(urlsafe=self.request.get("cursor"))
                if curs:
                    locations, next_cursor, more = Location.query().fetch_page(25, start_cursor=curs)
                else:
                    locations, next_cursor, more = Location.query().fetch_page(25)
            else:
                locations, next_cursor, more = Location.query().fetch_page(25)

            for location in locations:
                locations_json.append(location.to_object())

            data = {}
            data["locations"] = locations_json
            if more:
                data["next_page"] = "http://api.bangonph.com/v1/locations?cursor=" + str(next_cursor.urlsafe())
            else:
                data["next_page"] = False
            self.render(data)
        else:
            location = Location.get_by_id(instance_id)
            self.render(location.to_object())


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
        if not instance_id:
            location = add_location(data)
            self.render(location.to_object())
        else:
            location = add_location(data, instance_id)
            self.render(location.to_object())

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
        pass

    def post(self, instance_id=None):
        pass

    def delete(self, instance_id=None):
        pass


class APIPostsHandler(APIBaseHandler):
    def get(self, instance_id=None):
        posts_json = []
        if not instance_id:
            if self.request.get("cursor"):
                curs = Cursor(urlsafe=self.request.get("cursor"))
                if curs:
                    posts, next_cursor, more = Post.query().fetch_page(25, start_cursor=curs)
                else:
                    posts, next_cursor, more = Post.query().fetch_page(25)
            else:
                if self.request.get_all("filter_post_type"):
                    filter_type = self.request.get_all("filter_post_type")[0].upper()
                    date_now = datetime.datetime.now() + datetime.timedelta(hours=8)
                    
                    posts, next_cursor, more = Post.query(Post.post_type.IN([filter_type]), Post.expiry >= date_now).order(-Post.expiry).fetch_page(100)
                else:
                    posts, next_cursor, more = Post.query().fetch_page(25)

            for post in posts:
                posts_json.append(post.to_object())

            data = {}
            data["posts"] = posts_json
            if more:
                data["next_page"] = "http://api.bangonph.com/v1/locations?cursor=" + str(next_cursor.urlsafe())
            else:
                data["next_page"] = False
            self.render(data)
        else:
            post = Post.get_by_id(instance_id)
            if post:
                self.render(post.to_object())

    def post(self, instance_id=None):
        if self.request.get("comment"):
            logging.warning("Honeypot put!")
            return
        resp = API_RESPONSE.copy()
        if self.request.get("expiry"):
            try:
                expiry = datetime.datetime.strptime(self.request.get("expiry"), "%Y-%m-%d %H:%M:%S") #1992-10-20
            except:
                resp['response'] = "date has invalid format"
                resp['code'] = 404
                resp['property'] = "delete_subscriber"
                resp['description'] = "Use this format (YYYY-mm-dd H:M:S)"

                return
        else:
            expiry = None

        logging.critical(expiry)
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
            "location": self.request.get_all("location"),
        }
        if not instance_id:
            post = add_post(data)
            self.render(post.to_object())
        else:
            post = add_post(data, instance_id)
            self.render(post.to_object())

        p = pusher.Pusher(
          app_id='59383',
          key='e0a2a1c8316b9baddc9b',
          secret='474177f7aea8c983a7d1'
        )
        p['feeds'].trigger('new_post', post.to_object())

    def delete(self, instance_id=None):
        resp = API_RESPONSE.copy()
        resp["method"] = "delete"
        if instance_id:
            post = Post.get_by_id(int(instance_id))
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


class APIDropOffCentersHandler(APIBaseHandler):
    def get(self, instance_id=None):
        centers_json = []
        if not instance_id:
            if self.request.get("cursor"):
                curs = Cursor(urlsafe=self.request.get("cursor"))
                if curs:
                    centers, next_cursor, more = DropOffCenter.query().fetch_page(25, start_cursor=curs)
                else:
                    centers, next_cursor, more = DropOffCenter.query().fetch_page(25)
            else:
                centers, next_cursor, more = DropOffCenter.query().fetch_page(25)

            for center in centers:
                centers_json.append(center.to_object())

            data = {}
            data["dropOffCenters"] = centers_json
            if more:
                data["next_page"] = "http://api.bangonph.com/v1/locations?cursor=" + str(next_cursor.urlsafe())
            else:
                data["next_page"] = False
            self.render(data)
        else:
            center = DropOffCenter.get_by_id(instance_id)
            if center:
                self.render(center.to_object())

    @oauthed_required
    def post(self, instance_id=None):
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
            centers = add_drop_off_centers(data)
            self.render(centers.to_object())
        else:
            centers = add_drop_off_centers(data, instance_id)
            self.render(centers.to_object())

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
        if check_all_keys(["name", "email", "fb_id", "distribution"], self.params):
            if not instance_id:
                subscriber = add_subcriber(self.params)
            else:
                subscriber = add_subcriber(self.params, instance_id)
            self.render(subscriber.to_object(self.request.get("expand")))
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
        efforts_json = []
        logging.critical(self.request.get("expand"))
        if not instance_id:
            if self.request.get("cursor"):
                curs = Cursor(urlsafe=self.request.get("cursor"))
                if curs:
                    efforts, next_cursor, more = Distribution.query().fetch_page(25, start_cursor=curs)
                else:
                    efforts, next_cursor, more = Distribution.query().fetch_page(25)
            else:
                if self.request.get("filter_locations"):
                    loc = slugify(self.request.get("filter_locations"))
                    loc_key = Location.get_by_id(loc)
                    efforts, next_cursor, more  = Distribution.query(Distribution.destinations == loc_key.key).fetch_page(25)
                else:
                    efforts, next_cursor, more = Distribution.query().fetch_page(25)

            for effort in efforts:
                efforts_json.append(effort.to_object(self.request.get("expand").lower()))

            data = {}
            data["efforts"] = efforts_json
            if more:
                data["next_page"] = "http://api.bangonph.com/v1/locations?cursor=" + str(next_cursor.urlsafe())
            else:
                data["next_page"] = False
            self.render(data)
        else:
            effort = Distribution.get_by_id(instance_id)
            if effort:
                self.render(effort.to_object())

    def post(self, instance_id=None):
        if self.request.get("date_of_distribution"):
            date = datetime.datetime.strptime(self.request.get("date_of_distribution"), "%Y-%m-%d"), #1992-10-20
        else:
            date = None
        data = {
            "date_of_distribution": date,
            "contact": self.request.get("contact"),
            "destinations": self.request.get("destinations"),
            "supply_goal": self.request.get("supply_goal"),
            "actual_supply": self.request.get("actual_supply"),
            "images": self.request.get("images")
        }
        if not instance_id:
            effort = add_distribution(data)
            self.render(effort.to_object())
        else:
            effort = add_distribution(data, instance_id)
            self.render(effort.to_object())

    @oauthed_required
    def delete(self, instance_id=None):
        resp = API_RESPONSE.copy()
        resp["method"] = "delete"
        if instance_id:
            effort = Distribution.get_by_id(int(instance_id))
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
        contacts_json = []
        if not instance_id:
            if self.request.get("cursor"):
                curs = Cursor(urlsafe=self.request.get("cursor"))
                if curs:
                    contacts, next_cursor, more = Contact.query().fetch_page(25, start_cursor=curs)
                else:
                    contacts, next_cursor, more = Contact.query().fetch_page(25)
            else:
                contacts, next_cursor, more = Contact.query().fetch_page(25)

            for contact in contacts:
                contacts_json.append(contact.to_object())

            data = {}
            data["locations"] = contacts_json
            if more:
                data["next_page"] = "http://api.bangonph.com/v1/contacts?cursor=" + str(next_cursor.urlsafe())
            else:
                data["next_page"] = False

            self.render(data)
        else:
            contacts = Contact.get_by_id(instance_id)
            if contacts:
                self.render(contacts.to_object())

    @oauthed_required
    def post(self, instance_id=None):
        data = {}
        data["name"] = self.request.get("name")
        data["contacts"] = self.request.get("contacts")
        data["email"] = self.request.get("email")
        data["facebook"] = self.request.get("facebook")
        data["twitter"] = self.request.get("twitter")
        if not instance_id:
            contact = add_contact(data)
            self.render(contact.to_object())
        else:
            contact = add_contact(data, instance_id)
            self.render(contact.to_object())

    @oauthed_required
    def delete(self, instance_id=None):
        resp = API_RESPONSE.copy()
        resp["method"] = "delete"
        if instance_id:
            contact = Contact.get_by_id(int(instance_id))
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
        distributors_json = []
        if not instance_id:
            if self.request.get("cursor"):
                curs = Cursor(urlsafe=self.request.get("cursor"))
                if curs:
                    distributors, next_cursor, more = Distributor.query().fetch_page(25, start_cursor=curs)
                else:
                    distributors, next_cursor, more = Distributor.query().fetch_page(25)
            else:
                distributors, next_cursor, more = Distributor.query().fetch_page(25)

            for distributor in distributors:
                distributors_json.append(distributor.to_object())

            data = {}
            data["distributors"] = distributors_json
            if more:
                data["next_page"] = "http://api.bangonph.com/v1/distributors?cursor=" + str(next_cursor.urlsafe())
            else:
                data["next_page"] = False

            self.render(data)
        else:
            contacts = Distributor.get_by_id(instance_id)
            if contacts:
                self.render(contacts.to_object())

    @oauthed_required
    def post(self, instance_id=None):
        data = {
            "email": self.request.get("email"),
            "name": self.request.get("name"),
            "contact_num": self.request.get("contact_num"),
            "website": self.request.get("website"),
            "facebook": self.request.get("facebook")
        }
        logging.critical(data)

        if not instance_id:
            distributor = add_distributor(data)
            self.render(distributor.to_object())
        else:
            distributor = add_distributor(data, instance_id)
            self.render(distributor.to_object())


    @oauthed_required
    def delete(self, instance_id=None):
        resp = API_RESPONSE.copy()
        resp["method"] = "delete"
        if instance_id:
            distributor = Distributor.get_by_id(int(instance_id))
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
        logging.error(upload_files)
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

        if "?" in self.request.referer:
            self.redirect(self.request.referer + "&success=File%20Uploaded")
        else:
            self.redirect(self.request.referer + "?success=File%20Uploaded")



app = webapp2.WSGIApplication([
    routes.DomainRoute(r'<:gcdc2013-bangonph\.appspot\.com|www\.bangonph\.com>', [
        webapp2.Route('/', handler=PublicFrontPage, name="www-front"),
        webapp2.Route('/reliefoperations', handler=ReliefOperationsPage, name="www-reliefoperations"),
        webapp2.Route(r'/locations/<:.*>', handler=PublicLocationPage, name="www-locations"),
        
        webapp2.Route('/api/posts', handler=APIPostsHandler, name="www-api-posts"),
        webapp2.Route(r'/api/posts/<:.*>', handler=APIPostsHandler, name="www-api-posts"),

        # richmond:
        webapp2.Route('/s', handler=sampler, name="www-get-authorization-code"),

        webapp2.Route(r'/<:.*>', ErrorHandler)
    ]),
    routes.DomainRoute(r'<:admin\.bangonph\.com|localhost>', [
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



        # richmond:
        webapp2.Route('/s', handler=sampler, name="www-get-authorization-code"),

        webapp2.Route(r'/<:.*>', ErrorHandler)
    ]),

    routes.DomainRoute(r'<:api\.bangonph\.com|localhost>', [
        webapp2.Route('/v1/locations', handler=APILocationsHandler, name="api-locations"),
        webapp2.Route('/v1/users', handler=APIUsersHandler, name="api-users"),
        webapp2.Route('/v1/contacts', handler=APIContactsHandler, name="api-locations"),
        webapp2.Route('/v1/posts', handler=APIPostsHandler, name="api-locations"),
        webapp2.Route('/v1/drop-off-centers', handler=APIDropOffCentersHandler, name="api-locations"),
        webapp2.Route('/v1/subscribers', handler=APISubscribersHandler, name="api-subscribers"),
        webapp2.Route('/v1/orgs', handler=APIOrganizationsHandler, name="api-locations"),
        webapp2.Route('/v1/efforts', handler=APIEffortsHandler, name="api-locations"),
        webapp2.Route('/v1/distributors', handler=APIDistributorsHandler, name="api-locations"),


        webapp2.Route(r'/v1/distributors/<:.*>', handler=APIDistributorsHandler, name="api-locations"),
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

        webapp2.Route(r'/<:.*>', ErrorHandler)
    ])
])


