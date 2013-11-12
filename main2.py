import webapp2, jinja2, os
from webapp2_extras import routes
from models import User, AddressBook
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

    def render(self, template_path=None, force=False):
        self.tv["current_timestamp"] = time.mktime(self.now.timetuple())
        self.settings["current_year"] = self.now.year
        self.tv["settings"] = self.settings

        if self.request.get('json') or not template_path:
            self.response.out.write(simplejson.dumps(self.tv))
            return

        template = jinja_environment.get_template(template_path)
        self.response.out.write(template.render(self.tv))
        logging.debug(self.tv)

class CosmoPage(BaseHandler):
    def get(self):
        self.render("frontend/cosmo.html")

class FrontPage(BaseHandler):
    def get(self):
        datas = []
        for i in range(1, 6):
            datas.append(i)
        self.tv["numbers"] = datas
        self.render('frontend/test-front.html')

class AddressBookHandler(BaseHandler):
    def get(self):
        id_edit = self.request.get("id_edit")
        if id_edit:
            temp = {}
            addressbook = AddressBook.get_by_id(int(id_edit))
            if addressbook:
                temp["id"] = addressbook.key.id()
                temp["fullname"] = addressbook.fullname
                temp["email"] = addressbook.email
                temp["phone"] = addressbook.phone
                temp["address"] = addressbook.address

            self.response.out.write(simplejson.dumps(temp))
            return

        id_delete = self.request.get("id_delete")
        if id_delete:
            temp = {}
            addressbook = AddressBook.get_by_id(int(id_delete))
            if addressbook:
                addressbook.key.delete()
                
                temp["message"] = "Success"

            self.response.out.write(simplejson.dumps(temp))
            return

        addressbooks = AddressBook.query().order(-AddressBook.created).fetch(100)
        if addressbooks:
            datas = []
            for ab in addressbooks:
                temp = {}
                temp["id"] = ab.key.id()
                temp["fullname"] = ab.fullname
                temp["email"] = ab.email
                temp["phone"] = ab.phone
                temp["address"] = ab.address
                datas.append(temp)

            self.response.out.write(simplejson.dumps(datas))

    def post(self):
        details = self.request.body
        temp = {}
        if details:
            newmessage = simplejson.loads(details)

            addressbook = AddressBook()
            addressbook.fullname = newmessage["fullname"]
            addressbook.email = newmessage["email"]
            addressbook.phone = newmessage["phone"]
            addressbook.address = newmessage["address"]
            addressbook.put()

            temp = {}
            temp["id"] = addressbook.key.id()
            temp["fullname"] = newmessage["fullname"]
            temp["email"] = newmessage["email"]
            temp["phone"] = newmessage["phone"]
            temp["address"] = newmessage["address"]

        self.response.out.write(simplejson.dumps(temp))

class AddressBookUpdateHandler(BaseHandler):
    def put(self, *args, **kwargs):
        temp = {}
        id = kwargs["id"]
        details = self.request.body

        if id and details:
            newmessage = simplejson.loads(details)

            addressbook = AddressBook.get_by_id(int(id))
            addressbook.fullname = newmessage["fullname"]
            addressbook.email = newmessage["email"]
            addressbook.phone = newmessage["phone"]
            addressbook.address = newmessage["address"]
            addressbook.put()

            temp["id"] = addressbook.key.id()
            temp["fullname"] = newmessage["fullname"]
            temp["email"] = newmessage["email"]
            temp["phone"] = newmessage["phone"]
            temp["address"] = newmessage["address"]

        self.response.out.write(simplejson.dumps(temp))

class AddressBookSearchHandler(BaseHandler):
    def get(self, *args, **kwargs):
        temp = {}
        search = kwargs["value"]
        if search:
            addressbooks = AddressBook.query(AddressBook.fullname == search.title()).fetch(100)
            if addressbooks:
                datas = []
                for ab in addressbooks:
                    temp["id"] = ab.key.id()
                    temp["fullname"] = ab.fullname
                    temp["email"] = ab.email
                    temp["phone"] = ab.phone
                    temp["address"] = ab.address
                    datas.append(temp)

                self.response.out.write(simplejson.dumps(datas))

class ErrorHandler(BaseHandler):
    def get(self, page):
        self.response.out.write(simplejson.dumps({"error":"This route is not handled."}))

site_domain = SETTINGS["site_domain"].replace(".","\.")

app = webapp2.WSGIApplication([
    routes.DomainRoute(r'<:' + site_domain + '|localhost|' + SETTINGS["app_id"] + '\.appspot\.com>', [
        webapp2.Route('/', handler=FrontPage, name="www-front"),
        webapp2.Route('/cosmo', handler=CosmoPage, name="www-test"),

        webapp2.Route('/addressbook', handler=AddressBookHandler, name="www-address-book"),
        webapp2.Route(r'/addressbook/<id>', handler=AddressBookUpdateHandler, name="www-address-book-update"),
        webapp2.Route(r'/addressbook/search/<value>', handler=AddressBookSearchHandler, name="www-address-book-search"),
        webapp2.Route(r'/<:.*>', ErrorHandler)
    ])
])