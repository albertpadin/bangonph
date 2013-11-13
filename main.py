import webapp2, jinja2, os
from webapp2_extras import routes
from models import *
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
from oauth_models import Client

from google.appengine.api import urlfetch

from settings import SETTINGS
from settings import SECRET_SETTINGS

jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)), autoescape=True)


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

        contacts = Contact.query().fetch(100)
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
        locations = Location.query().fetch(100)
        if locations:
            datas = []
            for location in locations:
                temp = {}
                temp["id"] = location.key.id()
                temp["name"] = location.name
                temp["latlong"] = location.latlong
                temp["featured_photo"] = location.featured_photo
                temp["death_count"] = location.death_count
                temp["affectedCount"] = location.affected_count
                temp["status_board"] = location.status_board
                temp["needs"] = location.needs
                temp["status"] = location.status
                datas.append(temp)
            self.response.out.write(simplejson.dumps(datas))

    def post(self):
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
            "water": self.request.get("status_water")
        }

        data = {
            "name": self.request.get("name"),
            "needs": needs, # json format
            "centers": self.request.get_all("centers"),
            "latlong": self.request.get("latlong"),
            "featured_photo": self.request.get("featured_photo"),
            "death_count": self.request.get("death_count"),
            "affected_count": self.request.get("affected_count"),
            "status_board": self.request.get("status_board"),
            "status": status # json format
        }
        add_location(data)

class DistributionHandler(BaseHandler):
    @login_required
    def get(self):
        pass

    def post(self):
        data = {
            "date_of_distribution": datetime.datetime.strptime(self.request.get("date_of_distribution"), "%Y-%m-%d"), #1992-10-20
            "contact": int(self.request.get("contact")),
            "destinations": int(self.request.get("destinations")),
            "supply_goal": self.request.get("supply_goal"),
            "actual_supply": self.request.get("actual_supply")
        }

        add_destribution(data)

class DistributionFetchHandler(BaseHandler):
    @login_required
    def get(self):
        datas_contacts = []
        temp_type = {}
        contacts = Contact.query().fetch(100)
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
        locations = Location.query().fetch(100)
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

class CentersHandler(BaseHandler):
    @login_required
    def get(self):
        pass
    def post(self):
        data = {
            "drop_off_locations": self.request.get("drop_of_locations"),
            "distributor": self.request.get("distributor"),
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
        posts = Post.query().fetch(100)
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


class GetAuthorizationCode(BaseHandler):
    def post(self):
        from oauth import AuthorizationProvider as provider
        self.provider = provider()
        if self.request.body:
            body = simplejson.loads(self.request.body)
            response = self.provider.get_authorization_code(body['client_id'], body['user_id'], body['redirect_url'])

            self.response.headers.update(response.headers)
            self.response.out.write(response.content)
            # self.response.out = response.raw


# for testing purposes only
class sampler(BaseHandler):
    def get(self):
        pass

class ErrorHandler(BaseHandler):
    def get(self, page):
        logging.critical("This route is not handled.")

# API Handlers

class APIBaseHandler(webapp2.RequestHandler):
    def __init__(self, request=None, response=None):
        self.initialize(request, response)

    def render(self, response_body):
        self.response.headers["Content-Type"] = "application/json"

        self.response.out.write(simplejson.dumps(response_body))


class APIUsersHandler(APIBaseHandler):
    def get(self, instance_id=None):
        users_json = []
        if not instance_id:
            if self.request.get("cursor"):
                curs = Cursor(urlsafe=self.request.get("cursor"))
                if curs:
                    users, next_cursor, more = User.query().fetch_page(20, start_cursor=curs)
                else:
                    users, next_cursor, more = User.query().fetch_page(100)
            else:
                users, next_cursor, more = User.query().fetch_page(100)
                
            for user in users:
                users_json.append(user.to_object())

            data = {}
            data["users"] = users_json
            if more:
                data["next_page"] = "http://api.bangonph.com/users/?cursor=" + next_cursor
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
                    locations, next_cursor, more = Location.query().fetch_page(10, start_cursor=curs)
                else:
                    locations, next_cursor, more = Location.query().fetch_page(10)
            else:
                locations, next_cursor, more = Location.query().fetch_page(10)

            for location in locations:
                locations_json.append(location.to_object())

            data = {}
            data["locations"] = locations_json
            if more:
                data["next_page"] = "http://api.bangonph.com/locations/?cursor=" + next_cursor
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
            "water": self.request.get("status_water")
        }

        data = {
            "name": self.request.get("name"),
            "needs": needs, # json format
            "centers": self.request.get_all("centers"),
            "latlong": self.request.get("latlong"),
            "featured_photo": self.request.get("featured_photo"),
            "death_count": self.request.get("death_count"),
            "affected_count": self.request.get("affected_count"),
            "status_board": self.request.get("status_board"),
            "status": status # json format
        }
        if not instance_id:
            location = add_location(data)
            self.render(location.to_object())
        else:
            location = add_location(data, instance_id)
            self.render(location.to_object())


    def delete(self, instance_id=None):
        location = ndb.Key("Location", instance_id)
        location.delete()
        data = {}
        data["success"] = True
        self.render(data)

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
                    posts, next_cursor, more = Post.query().fetch_page(10, start_cursor=curs)
                else:
                    posts, next_cursor, more = Post.query().fetch_page(10)
            else:
                posts, next_cursor, more = Post.query().fetch_page(10)

            for post in posts:
                posts_json.append(post.to_object())

            data = {}
            data["posts"] = posts_json
            if more:
                data["next_page"] = "http://api.bangonph.com/locations/?cursor=" + next_cursor
            else:
                data["next_page"] = False
            self.render(data)
        else:
            post = Post.get_by_id(instance_id)
            if post:
                self.render(post.to_object())

    def post(self, instance_id=None):
        pass

    def delete(self, instance_id=None):
        pass


class APIDropOffCentersHandler(APIBaseHandler):
    def get(self, instance_id=None):
        centers_json = []
        if not instance_id:
            if self.request.get("cursor"):
                curs = Cursor(urlsafe=self.request.get("cursor"))
                if curs:
                    centers, next_cursor, more = DropOffCenter.query().fetch_page(10, start_cursor=curs)
                else:
                    centers, next_cursor, more = DropOffCenter.query().fetch_page(10)
            else:
                centers, next_cursor, more = DropOffCenter.query().fetch_page(10)

            for center in centers:
                centers_json.append(center.to_object())

            data = {}
            data["dropOffCenters"] = centers_json
            if more:
                data["next_page"] = "http://api.bangonph.com/locations/?cursor=" + next_cursor
            else:
                data["next_page"] = False
            self.render(data)
        else:
            center = DropOffCenter.get_by_id(instance_id)
            if center:
                self.render(center.to_object())

    def post(self, instance_id=None):
        pass

    def delete(self, instance_id=None):
        pass


class APISubscribersHandler(APIBaseHandler):
    def get(self, instance_id=None):
        pass

    def post(self, instance_id=None):
        pass

    def delete(self, instance_id=None):
        pass


class APIEffortsHandler(APIBaseHandler):
    def get(self, instance_id=None):
        pass

    def post(self, instance_id=None):
        pass

    def delete(self, instance_id=None):
        pass


class APIContactsHandler(APIBaseHandler):
    def get(self, instance_id=None):
        contacts_json = []
        if not instance_id:
            if self.request.get("cursor"):
                curs = Cursor(urlsafe=self.request.get("cursor"))
                if curs:
                    contacts, next_cursor, more = Contact.query().fetch_page(10, start_cursor=curs)
                else:
                    contacts, next_cursor, more = Contact.query().fetch_page(10)
            else:
                contacts, next_cursor, more = Contact.query().fetch_page(10)

            for contact in contacts:
                contacts_json.append(contact.to_object())

            data = {}
            data["locations"] = contacts_json
            if more:
                data["next_page"] = "http://api.bangonph.com/contacts/?cursor=" + next_cursor
            else:
                data["next_page"] = False

            self.render(data)
        else:
            contacts = Contact.get_by_id(instance_id)
            if contacts:
                self.render(contacts.to_object())


    def post(self, instance_id=None):
        pass

    def delete(self, instance_id=None):
        pass


app = webapp2.WSGIApplication([
    routes.DomainRoute(r'<:gcdc2013-bangonph\.appspot\.com|www\.bangonph\.com>', [
        webapp2.Route('/', handler=FrontPage, name="www-front"),
        webapp2.Route('/public', handler=PublicFrontPage, name="www-front"),
        webapp2.Route('/register', handler=RegisterPage, name="www-register"),
        webapp2.Route('/logout', handler=Logout, name="www-logout"),
        webapp2.Route('/login', handler=LoginPage, name="www-login"),
        webapp2.Route('/fblogin', handler=FBLoginPage, name="www-fblogin"),
        webapp2.Route('/dashboard', handler=DashboardPage, name="www-dashboard"),
        webapp2.Route('/cosmo', handler=CosmoPage, name="www-test"),

        # leonard gwapo:
        webapp2.Route('/locations', handler=LocationHandler, name="www-locations"),
        webapp2.Route('/users', handler=UserHandler, name="www-users"),
        webapp2.Route('/contacts', handler=ContactHandler, name="www-contacts"),
        webapp2.Route('/locations', handler=LocationHandler, name="www-locations"),
        webapp2.Route('/distributions', handler=DistributionHandler, name="www-distributions"),
        webapp2.Route('/distributions/fetch', handler=DistributionFetchHandler, name="www-distributions-fetch"),


        webapp2.Route('/posts', handler=PostsHandler, name="www-post"),

        webapp2.Route('/drop-off-center', handler=CentersHandler, name="www-centers"),


        webapp2.Route('/subscribers', handler=SubscriberPage, name="www-subscribers"),


        # richmond:
        webapp2.Route('/get_authorization_code', handler=GetAuthorizationCode, name="www-get-authorization-code"),
        webapp2.Route('/s', handler=sampler, name="www-get-authorization-code"),

        webapp2.Route(r'/<:.*>', ErrorHandler)
    ]),
    routes.DomainRoute('admin.bangonph.com', [
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

        webapp2.Route('/contacts', handler=ContactHandler, name="www-contacts"),
        webapp2.Route('/drop-off-center', handler=CentersHandler, name="www-centers"),


        webapp2.Route('/subscribers', handler=SubscriberPage, name="www-subscribers"),


        # richmond:
        webapp2.Route('/get_authorization_code', handler=GetAuthorizationCode, name="www-get-authorization-code"),
        webapp2.Route('/s', handler=sampler, name="www-get-authorization-code"),

        webapp2.Route(r'/<:.*>', ErrorHandler)
    ]),

    routes.DomainRoute(r'<:api\.bangonph\.com|localhost>', [
        webapp2.Route('/locations', handler=APILocationsHandler, name="api-locations"),
        webapp2.Route('/users', handler=APIUsersHandler, name="api-users"),
        webapp2.Route('/contacts', handler=APIContactsHandler, name="api-locations"),
        webapp2.Route('/posts', handler=APIPostsHandler, name="api-locations"),
        webapp2.Route('/drop-off-centers', handler=APIDropOffCentersHandler, name="api-locations"),
        webapp2.Route('/subscribers', handler=APISubscribersHandler, name="api-locations"),
        webapp2.Route('/orgs', handler=APIOrganizationsHandler, name="api-locations"),
        webapp2.Route('/efforts', handler=APIEffortsHandler, name="api-locations"),

        webapp2.Route(r'/locations/<:.*>', handler=APILocationsHandler, name="api-locations"),
        webapp2.Route(r'/users/<:.*>', handler=APIUsersHandler, name="api-users"),
        webapp2.Route(r'/contacts/<:.*>', handler=APIContactsHandler, name="api-locations"),
        webapp2.Route(r'/posts/<:.*>', handler=APIPostsHandler, name="api-locations"),
        webapp2.Route(r'/drop-off-centers/<:.*>', handler=APIDropOffCentersHandler, name="api-locations"),
        webapp2.Route(r'/subscribers/<:.*>', handler=APISubscribersHandler, name="api-locations"),
        webapp2.Route(r'/orgs/<:.*>', handler=APIOrganizationsHandler, name="api-locations"),
        webapp2.Route(r'/efforts/<:.*>', handler=APIEffortsHandler, name="api-locations"),



        # richmond:
        webapp2.Route('/get_authorization_code', handler=GetAuthorizationCode, name="api-get-authorization-code"),
        webapp2.Route('/s', handler=sampler, name="api-get-authorization-code"),

        webapp2.Route(r'/<:.*>', ErrorHandler)
    ])
])


