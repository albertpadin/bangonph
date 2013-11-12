from google.appengine.ext import ndb
import time


class User(ndb.Model):
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)
    email = ndb.StringProperty()
    password = ndb.StringProperty()
    name = ndb.StringProperty()
    contacts = ndb.StringProperty()
    permissions = ndb.StringProperty()
    
    def to_object(self):
        details = {}
        details["created"] = int(time.mktime(self.created.timetuple()))
        details["updated"] = int(time.mktime(self.updated.timetuple()))
        details["email"] = self.email
        details["name"] = self.name
        
        return details

class Distributor(ndb.Model):
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)
    name = ndb.StringProperty()
    contact_num = ndb.StringProperty()
    location = ndb.StringProperty()
    email = ndb.StringProperty()
    website = ndb.StringProperty()
    contacts = ndb.KeyProperty()
    facebook = ndb.StringProperty()


class Location(ndb.Model):
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)
    name = ndb.StringProperty()
    latlong = ndb.StringProperty()
    featured_photo = ndb.StringProperty(repeated=True)
    death_count = ndb.IntegerProperty()
    affected_count = ndb.IntegerProperty()
    status_board = ndb.StringProperty()
    needs = ndb.JsonProperty()
    centers = ndb.StringProperty(repeated=True)
    status = ndb.JsonProperty(repeated=True)
    

class DropOffCenter(ndb.Model):
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)
    name = ndb.StringProperty()
    drop_off_locations = ndb.StringProperty(repeated=True)
    distributor = ndb.StringProperty(repeated=True)
    address = ndb.StringProperty(repeated=True)
    latlong = ndb.StringProperty()
    destinations = ndb.StringProperty()
    schedule = ndb.StringProperty()
    twitter = ndb.StringProperty()
    facebook = ndb.StringProperty()
    contacts = ndb.StringProperty(repeated=True)
    email = ndb.StringProperty()


class Distribution(ndb.Model):
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)
    date_of_distribution = ndb.DateTimeProperty()
    contact = ndb.KeyProperty()
    destinations = ndb.KeyProperty()
    supply_goal = ndb.JsonProperty(repeated=True)
    actual_supply = ndb.JsonProperty(repeated=True)


    def to_object(self):
        details = {}
        details["key"] = self.key.urlsafe()

        return details

class Subscriber(ndb.Model):
    name = ndb.StringProperty()
    email = ndb.StringProperty()
    fb_id = ndb.StringProperty()
    distribution = ndb.KeyProperty()

class Contact(ndb.Model):
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)
    name = ndb.StringProperty()
    contacts = ndb.StringProperty(repeated=True)
    email = ndb.StringProperty()
    facebook = ndb.StringProperty()
    twitter = ndb.StringProperty()


class Post(ndb.Model):
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)
    name = ndb.StringProperty()
    email = ndb.StringProperty()
    twitter = ndb.StringProperty()
    facebook = ndb.StringProperty()
    contacts = ndb.StringProperty(repeated=True)
    message = ndb.TextProperty()


class LogActivity(ndb.Model):
    created = ndb.DateTimeProperty(auto_now_add=True)
    user = ndb.StringProperty()
    previous_values = ndb.JsonProperty()
    new_values = ndb.JsonProperty
    action = ndb.StringProperty()





