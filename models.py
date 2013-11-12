from google.appengine.ext import ndb
import time


class User(ndb.Model):
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)
    email = ndb.StringProperty()
    password = ndb.StringProperty()
    name = ndb.StringProperty()
    
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


class Locations(ndb.Model):
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)
    goal = ndb.StringProperty()
    needs = ndb.TextProperty()
    centers = ndb.StringProperty(repeated=True)
    distributions = ndb.StringProperty(repeated=True)


class DropOfCenters(ndb.Model):
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)
    locations = ndb.StringProperty(repeated=True)
    distributor = ndb.StringProperty(repeated=True)
    address = ndb.StringProperty(repeated=True)


class Distributions(ndb.Model):
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)
    location = ndb.KeyProperty()
    status = ndb.StringProperty(default="undelivered")
    centers = ndb.StringProperty(repeated=True)






