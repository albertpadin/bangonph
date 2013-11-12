from google.appengine.ext import ndb
import time


class User(ndb.Model):
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)
    email = ndb.StringProperty()
    password = ndb.StringProperty()
    fb_id = ndb.StringProperty()
    fb_access_token = ndb.StringProperty()
    fb_username = ndb.StringProperty()
    name = ndb.StringProperty()
    first_name = ndb.StringProperty()
    middle_name = ndb.StringProperty()
    last_name = ndb.StringProperty()
    addressbook = ndb.JsonProperty()

    def to_object(self):
        details = {}
        details["created"] = int(time.mktime(self.created.timetuple()))
        details["updated"] = int(time.mktime(self.updated.timetuple()))
        details["email"] = self.email
        details["fb_id"] = self.fb_id
        details["name"] = self.name
        details["addressbook"] = self.addressbook
        return details

class AddressBook(ndb.Model):
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)
    fullname = ndb.StringProperty()
    email = ndb.StringProperty()
    phone = ndb.StringProperty()
    address = ndb.StringProperty()