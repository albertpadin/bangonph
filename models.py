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
    drop_of_locations = ndb.StringProperty(repeated=True)
    distributor = ndb.StringProperty(repeated=True)
    address = ndb.StringProperty(repeated=True)
    latlong = ndb.StringProperty()
    destinations = ndb.StringProperty()
    schedule = ndb.StringProperty()
    twitter = ndb.StringProperty()
    facebook = ndb.StringProperty()
    phone = ndb.StringProperty()
    email = ndb.StringProperty()


class Distribution(ndb.Model):
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)
    location = ndb.KeyProperty()
    date_of_distribution = ndb.DateTimeProperty()
    contact = ndb.KeyProperty()
    destinations = ndb.KeyProperty()
    supply_goal = ndb.JsonProperty(repeated=True)
    actual_supply = ndb.JsonProperty(repeated=True)
    status = ndb.StringProperty(default="undelivered")
    drop_off_centers = ndb.StringProperty(repeated=True)



class Contact(ndb.Model):
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)
    name = ndb.StringProperty()
    contacts = ndb.StringProperty(repeated=True)
    email = ndb.StringProperty()
    facebook = ndb.StringProperty()
    twitter = ndb.StringProperty()




