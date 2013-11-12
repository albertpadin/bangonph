import webapp2, jinja2, os
from webapp2_extras import routes
from models import User
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
    def post(self):
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

class AddressBookHandler(BaseHandler):
    def get(self):
        id_edit = self.request.get("id_edit")
        if id_edit:
            temp = {}
            user = User.get_by_id(self.user.email)
            if user:
                for a in user.addressbook:
                    if a["id"] == id_edit:
                        temp["id"] = a["id"]
                        temp["fullname"] = a["fullname"]
                        temp["email"] = a["email"]
                        temp["phone"] = a["phone"]
                        temp["address"] = a["address"]

                self.response.out.write(simplejson.dumps(temp))
                return

        id_delete = self.request.get("id_delete")
        if id_delete:
            temp = {}
            user = User.get_by_id(self.user.email)
            if user:
                x = 0
                for a in user.addressbook:
                    if a["id"] == id_delete:
                        user.addressbook.pop(int(x))
                    x += 1

                user.put()
                
                temp["message"] = "Success"

            self.response.out.write(simplejson.dumps(temp))
            return

        user = User.get_by_id(self.user.email)
        if user:
            datas = []
            if user.addressbook:
                for a in user.addressbook:
                    temp = {}
                    temp["id"] = a["id"]
                    temp["fullname"] = a["fullname"]
                    temp["email"] = a["email"]
                    temp["phone"] = a["phone"]
                    temp["address"] = a["address"]
                    datas.append(temp)

                self.response.out.write(simplejson.dumps(datas))

    def post(self):
        details = self.request.body
        temp = {}
        if details:
            newmessage = simplejson.loads(details)

            user = User.get_by_id(self.user.email)
            datas = []
            if user:
                data = {}
                data["fullname"] = newmessage["fullname"]
                data["email"] = newmessage["email"]
                data["phone"] = newmessage["phone"]
                data["address"] = newmessage["address"]
                data["id"] = str(uuid.uuid4())
                if user.addressbook:
                    user.addressbook.append(data)
                else:
                    datas.append(data)
                    user.addressbook = datas

                user.put()

                temp = {}
                temp["id"] = data["id"]
                temp["fullname"] = newmessage["fullname"]
                temp["email"] = newmessage["email"]
                temp["phone"] = newmessage["phone"]
                temp["address"] = newmessage["address"]

            self.response.out.write(simplejson.dumps(temp))

class AddressBookUpdateHandler(BaseHandler):
    def put(self, *args, **kwargs):
        id = kwargs["id"]
        details = self.request.body
        logging.critical(details)

        if id:
            newmessage = simplejson.loads(details)
            user = User.get_by_id(self.user.email)
            if user:
                for a in user.addressbook:
                    if a["id"] == id:
                        a["id"] = newmessage["id"]
                        a["fullname"] = newmessage["fullname"]
                        a["email"] = newmessage["email"]
                        a["phone"] = newmessage["phone"]
                        a["address"] = newmessage["address"]

                user.put()

                self.response.out.write(simplejson.dumps(a))
                return

class ErrorHandler(BaseHandler):
    def get(self, page):
        logging.critical("This route is not handled.")

site_domain = SETTINGS["site_domain"].replace(".","\.")

app = webapp2.WSGIApplication([
    routes.DomainRoute(r'<:addressbook-backbone\.appspot\.com|localhost>', [
        webapp2.Route('/', handler=FrontPage, name="www-front"),
        webapp2.Route('/register', handler=RegisterPage, name="www-register"),
        webapp2.Route('/logout', handler=Logout, name="www-logout"),
        webapp2.Route('/login', handler=LoginPage, name="www-login"),
        webapp2.Route('/fblogin', handler=FBLoginPage, name="www-fblogin"),
        webapp2.Route('/dashboard', handler=DashboardPage, name="www-dashboard"),
        webapp2.Route('/cosmo', handler=CosmoPage, name="www-test"),

        webapp2.Route('/addressbook', handler=AddressBookHandler, name="www-address-book"),
        webapp2.Route(r'/addressbook/<id>', handler=AddressBookUpdateHandler, name="www-address-book-update"),
        webapp2.Route(r'/<:.*>', ErrorHandler)
    ])
])