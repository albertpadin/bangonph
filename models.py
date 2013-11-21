from google.appengine.ext import ndb
import logging
import time, os, datetime
from settings import API_RESPONSE, API_RESPONSE_DATA
from settings import DATES, MULTIPLIER

currenturl = str(os.environ['wsgi.url_scheme'])+"://"+str(os.environ['HTTP_HOST'])

def get_current_date():
    now = datetime.datetime.now() + datetime.timedelta(hours=8)
    return now.strftime("%m/%d/%Y")


def get_next_seven_days():
    days = []
    now = datetime.datetime.now() + datetime.timedelta(hours=8)
    for i in range(0,7):
        if i:
            day = now + datetime.timedelta(days=i)
        else:
            day = now
        days.append(day.strftime("%m/%d/%Y"))
    return days


def get_past_seven_days():
    days = []
    now = datetime.datetime.now() + datetime.timedelta(hours=8)
    for i in range(0,7):
        if i:
            day = now - datetime.timedelta(days=i)
        else:
            day = now
        days.append(day.strftime("%m/%d/%Y"))
    return days


class Contributor(ndb.Model):
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)
    fb_email = ndb.StringProperty()
    fb_id = ndb.StringProperty()
    fb_username = ndb.StringProperty()
    fb_lastname = ndb.StringProperty()
    fb_firstname = ndb.StringProperty()
    fb_middlename = ndb.StringProperty()
    contributions = ndb.IntegerProperty(default=0)
    locations = ndb.StringProperty(repeated=True)
    locations_pretty = ndb.StringProperty(repeated=True)


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
        details["meta"] = {"href": "http://api.bangonph.com/v1/users/" + self.key.id()}
        details["created"] = str(self.created)
        details["updated"] = str(self.updated)
        details["email"] = self.email
        details["name"] = self.name
        details["id"] = self.key.id()
        details["contacts"] = self.contacts
        details["permissions"] = self.permissions

        return details



class Distributor(ndb.Model):
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)
    name = ndb.StringProperty()
    contact_num = ndb.StringProperty()
    email = ndb.StringProperty()
    website = ndb.StringProperty()
    facebook = ndb.StringProperty()
    contact_details = ndb.TextProperty()

    def to_object(self):
        details = {}

        details["meta"] = {"href": "http://api.bangonph.com/v1/orgs/" + str(self.key.id())}
        details["created"] = str(self.created)
        details["updated"] = str(self.updated)
        details["email"] = self.email
        details["name"] = self.name
        details["id"] = self.key.id()
        details["contact_num"] = self.contact_num
        details["website"] = self.website
        details["facebook"] = self.contact_num
        details["contact_details"] = self.contact_details

        return details

class LocationRevisionChanges(ndb.Model):
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)
    fb_email = ndb.StringProperty()
    fb_id = ndb.StringProperty()
    fb_access_token = ndb.StringProperty()
    fb_username = ndb.StringProperty()
    fb_lastname = ndb.StringProperty()
    fb_firstname = ndb.StringProperty()
    fb_middlename = ndb.StringProperty()
    fb_name = ndb.StringProperty()
    name = ndb.StringProperty()
    status = ndb.JsonProperty()
    requirements = ndb.JsonProperty()
    revision_type = ndb.StringProperty(default="New Update")


class LocationRevision(ndb.Model):
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)
    fb_email = ndb.StringProperty()
    fb_id = ndb.StringProperty()
    fb_access_token = ndb.StringProperty()
    fb_username = ndb.StringProperty()
    fb_lastname = ndb.StringProperty()
    fb_firstname = ndb.StringProperty()
    fb_middlename = ndb.StringProperty()
    fb_name = ndb.StringProperty()
    name = ndb.StringProperty()
    death = ndb.JsonProperty() # ndb.IntegerProperty()
    affected = ndb.JsonProperty() # ndb.IntegerProperty()
    missing_person = ndb.JsonProperty()
    status = ndb.JsonProperty() # ndb.JsonProperty()
    requirements = ndb.JsonProperty() # ndb.JsonProperty()

class Location(ndb.Model):
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)
    name = ndb.StringProperty()
    latlong = ndb.StringProperty()
    featured_photo = ndb.StringProperty()
    death_count = ndb.IntegerProperty()
    death_count_text = ndb.StringProperty()
    affected_count = ndb.IntegerProperty()
    affected_count_text = ndb.StringProperty()
    status_board = ndb.TextProperty()
    relief_aid_status = ndb.StringProperty(default="Unknown")
    needs = ndb.JsonProperty()
    status = ndb.JsonProperty()
    levels = ndb.JsonProperty(default={})
    current_levels = ndb.JsonProperty(default={"food":0, "hygiene":0, "medicine":0, "medical_mission":0, "shelter":0})
    images = ndb.JsonProperty()
    hash_tag = ndb.StringProperty(repeated=True)
    featured = ndb.BooleanProperty(default=False)
    missing_person = ndb.IntegerProperty()
    missing_person_text = ndb.StringProperty()
    relief_aid_totals = ndb.JsonProperty(default={})

    def to_object(self, extended="", show_relief=False):
        details = {}
        details["meta"] = {"href": "http://api.bangonph.com/v1/locations/" + str(self.key.id())}
        details["created"] = str(self.created)
        details["updated"] = str(self.updated)
        details["latlong"] = self.latlong
        details["id"] = self.key.id()
        details["featured_photo"] = self.featured_photo
        details["death_count"] = self.death_count
        details["death_count_text"] = self.death_count_text
        details["affectedCount"] = self.affected_count
        details["affectedCountText"] = self.affected_count_text
        details["affected_count"] = self.affected_count
        details["affected_count_text"] = self.affected_count_text
        details["missing_count"] = self.missing_person
        details["missing_count_text"] = self.missing_person_text
        details["statusBoard"] = self.status_board
        details["status_board"] = self.status_board
        details["needs"] = self.needs
        details["status"] = self.status
        details["images"] = []
        try:
            for image in self.images:
                if image['src']:
                    details['images'].append(image)
        except:
            pass
        details["hash_tag"] = self.hash_tag
        details["featured"] = self.featured
        details["relief_aid_status"] = self.relief_aid_status
        details["missing_person"] = self.missing_person
        details["missing_person_text"] = self.missing_person_text
        details["name"] = self.name
        details["levels"] = self.levels
        details["current_levels"] = self.current_levels
        tags = self.name.split(",")
        details['tags'] = []
        for tag in tags:
            details['tags'].append(tag.strip().lower())
        if not self.relief_aid_totals:
            self.relief_aid_totals = {}
        details['relief_aid_ratings'] = {}
        details['relief_aid_seven_day_summary'] = {}
        details['relief_aid_totals'] = {}
        details['relief_requirement'] = {}

        if show_relief:
            details['relief_aid_totals'] = self.relief_aid_totals
            if not self.affected_count:
                self.affected_count = 1000

            for date in DATES:
                details['relief_aid_ratings'][date] = {"food":0, "hygiene":0, "medicine":0, "medical_mission":0, "shelter":0}
                if date not in details['levels']:
                    details['levels'][date] = self.current_levels
                if date not in details['relief_requirement']:
                    details['relief_requirement'][date] = {"food":0, "hygiene":0, "medicine":0, "medical_mission":0, "shelter":0}
                if date not in details['relief_aid_totals']:
                    details['relief_aid_totals'][date] = {"food":0, "hygiene":0, "medicine":0, "medical_mission":0, "shelter":0}

                for key in details['levels'][date]:
                    requirement_level = float(100 - details['levels'][date][key]) / 100
                    requirement = {}
                    requirement[key] = self.affected_count * requirement_level / MULTIPLIER[key]
                    details['relief_requirement'][date][key] = requirement[key]
                    relief_aid_rating = (float(details['relief_aid_totals'][date][key]) / float(requirement[key])) * 100
                    details['relief_aid_ratings'][date][key] = relief_aid_rating

            totals = {}
            details['relief_aid_seven_day_summary'] = {}
            details['relief_aid_seven_day_summary']['all'] = float(0)
            details['relief_seven_day_requirement_totals'] = {}
            details['relief_aid_seven_day_totals'] = {"food":0, "hygiene":0, "medicine":0, "medical_mission":0, "shelter":0}
            details['relief_seven_day_requirement'] = {"food":0, "hygiene":0, "medicine":0, "medical_mission":0, "shelter":0}
            details['relief_aid_seven_day_totals']['all'] = 0
            details['relief_seven_day_requirement_totals']['all'] = 0
            for date in get_past_seven_days():
                for key in details['relief_aid_ratings'][date]:
                    if key not in totals:
                        totals[key] = float(0)
                    totals[key] += details['relief_aid_ratings'][date][key]
                    if key not in details['relief_seven_day_requirement_totals']:
                        details['relief_seven_day_requirement_totals'][key] = 0
                    details['relief_seven_day_requirement_totals'][key] += int(details['relief_requirement'][date][key])
                    details['relief_seven_day_requirement_totals']['all'] += int(details['relief_requirement'][date][key])
                    if key not in details['relief_aid_seven_day_totals']:
                        details['relief_aid_seven_day_totals'][key] = 0
                    details['relief_aid_seven_day_totals'][key] += int(details['relief_aid_totals'][date][key])
                    details['relief_aid_seven_day_totals']['all'] += int(details['relief_aid_totals'][date][key])
            for key in totals:
                details['relief_aid_seven_day_summary'][key] = totals[key] / float(7)
                details['relief_aid_seven_day_summary']['all'] += details['relief_aid_seven_day_summary'][key]

            details['relief_aid_seven_day_summary']['all'] = details['relief_aid_seven_day_summary']['all'] / float(7)

        return details


class DropOffCenter(ndb.Model):
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)
    name = ndb.StringProperty()
    drop_off_locations = ndb.StringProperty(repeated=True)
    distributor = ndb.StringProperty(repeated=True)
    address = ndb.StringProperty()
    latlong = ndb.StringProperty()
    destinations = ndb.StringProperty(repeated=True)
    schedule = ndb.StringProperty()
    twitter = ndb.StringProperty()
    facebook = ndb.StringProperty()
    contacts = ndb.StringProperty(repeated=True)
    email = ndb.StringProperty()

    def to_object(self, expand=""):
        details = {}
        details["meta"] = {"href": "http://api.bangonph.com/v1/drop-off-centers/" + str(self.key.id())}
        details["created"] = str(self.created)
        details["updated"] = str(self.updated)
        details["drop_off_locations"] = self.drop_off_locations
        details["distributor"] = self.distributor
        details["address"] = self.address
        details["name"] = self.name
        details["latlong"] = self.latlong
        details["destinations"] = self.destinations
        details["schedule"] = self.schedule
        details["twitter"] = self.twitter
        details["facebook"] = self.facebook
        details["contacts"] = self.contacts
        details["email"] = self.email
        details["id"] = self.key.id()

        return details

class DistributionRevision(ndb.Model):
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)
    fb_email = ndb.StringProperty()
    fb_id = ndb.StringProperty()
    fb_access_token = ndb.StringProperty()
    fb_username = ndb.StringProperty()
    fb_lastname = ndb.StringProperty()
    fb_firstname = ndb.StringProperty()
    fb_middlename = ndb.StringProperty()
    fb_name = ndb.StringProperty()
    name = ndb.StringProperty() # location
    relief_name = ndb.StringProperty()
    destination = ndb.StringProperty()
    num_of_packs = ndb.IntegerProperty()
    description = ndb.TextProperty()
    contacts = ndb.StringProperty()
    needs = ndb.StringProperty()
    date = ndb.StringProperty(default="UNKNOWN") # m-d-yyyy
    tag = ndb.StringProperty()
    status = ndb.StringProperty(default="UNKNOWN")

    """ added """
    featured_photo = ndb.StringProperty()
    images = ndb.JsonProperty()
    status = ndb.StringProperty()
    info = ndb.TextProperty()
    supply_goal = ndb.JsonProperty()
    actual_supply = ndb.JsonProperty()


    def to_object(self, expand=""):
        details = {}
        
        details["relief_name"] = self.relief_name
        details["num_of_packs"] = self.num_of_packs
        details["fb_id"] = self.fb_id
        details["fb_email"] = self.fb_email
        details["fb_access_token"] = self.fb_access_token
        details["fb_username"] = self.fb_username
        details["fb_lastname"] = self.fb_lastname
        details["fb_firstname"] = self.fb_firstname
        details["fb_middlename"] = self.fb_middlename
        details["fb_name"] = self.fb_name
        details["needs"] = self.needs
        details["tag"] = self.tag
        
        details["meta"] = {"href": "http://api.bangonph.com/v1/efforts/" + str(self.key.id())}
        details["created"] = str(self.created)
        details["updated"] = str(self.updated)

        if self.date:
            try:
                date = datetime.datetime.strptime(self.date, "%m/%d/%Y")
                details["dateOfDistribution"] = str(date)
            except:
                details["dateOfDistribution"] = self.date
        else:
            details["dateOfDistribution"] = ""

        details["images"] = self.images
        details["status"] = self.status
        details["info"] = self.info
        details["featured_photo"] = self.featured_photo
        details["description"] = self.description

        if expand == "contacts":
            contact_details = {}
            try:
                cont = Contact.get_by_id(self.contacts)
                contact_details["contact_details"] = cont.to_object()
            except:
                cont = Contact.query(Contact.name == self.contacts).fetch(1)
                contact_details["contact_details"] = cont[0].to_object()
            details["contact"] = contact_details
        else:
            if self.contacts:
                data = {}
                data["meta"] = {"href": "http://api.bangonph.com/v1/contacts/" + str(self.contacts)}
                details["contact"] = data
            else:
                details["contact"] = ""



        if expand == "destinations":
            destination_details = {}
            location = Location.get_by_id(self.name)
            destination_details["destination_details"] = location.to_object()
            details["destinations"] = destination_details
        else:
            if self.name:
                data = {}
                data["meta"] = {"href": "http://api.bangonph.com/v1/locations/" + str(self.name)}
                details["destinations"] = data
            else:
                details["destinations"] = ""

        details["id"] = self.key.id()
        details["supply_goal"] = self.num_of_packs
        details["actual_supply"] = self.num_of_packs

        return details

class Distribution(ndb.Model):
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)
    date_of_distribution = ndb.DateTimeProperty()
    contact = ndb.StringProperty()
    destinations = ndb.KeyProperty()
    supply_goal = ndb.JsonProperty()
    actual_supply = ndb.JsonProperty()
    images = ndb.JsonProperty()
    status = ndb.StringProperty()
    info = ndb.TextProperty()
    featured_photo = ndb.StringProperty()
    description = ndb.TextProperty()


    def to_object(self, expand=""):
        details = {}
        details["meta"] = {"href": "http://api.bangonph.com/v1/efforts/" + str(self.key.id())}
        details["created"] = str(self.created)
        details["updated"] = str(self.updated)
        details["dateOfDistribution"] = str(self.date_of_distribution)
        details["images"] = self.images
        details["status"] = self.status
        details["info"] = self.info
        details["featured_photo"] = self.featured_photo
        details["description"] = self.description

        if expand == "contacts":
            contact_details = {}
            try:
                cont = Contact.get_by_id(self.contact)
                contact_details["contact_details"] = cont.to_object()
            except:
                cont = Contact.query(Contact.name == self.contact).fetch(1)
                contact_details["contact_details"] = cont[0].to_object()
            details["contact"] = contact_details
        else:
            if self.contact:
                # data = {}
                # data["meta"] = {"href": "http://api.bangonph.com/v1/contacts/" + str(self.contact)}
                details["contact"] = self.contact
            else:
                details["contact"] = ""



        if expand == "destinations":
            destination_details = {}
            logging.critical(self.destinations)
            location = self.destinations.get()
            destination_details["destination_details"] = location.to_object()
            details["destination"] = destination_details
        else:
            if self.destinations:
                data = {}
                data["meta"] = {"href": "http://api.bangonph.com/v1/contacts/" + str(self.destinations.urlsafe())}
                details["destinations"] = data
            else:
                details["destinations"] = ""


        details["id"] = self.key.id()
        details["supply_goal"] = self.supply_goal
        details["actual_supply"] = self.actual_supply

        return details

class Subscriber(ndb.Model):
    name = ndb.StringProperty()
    email = ndb.StringProperty()
    fb_id = ndb.StringProperty()
    distribution = ndb.KeyProperty(kind="Distribution")
    location = ndb.KeyProperty()
    all_updates = ndb.BooleanProperty(default=False)

    def to_object(self, expand=None):
        data = {}
        data["meta"] = {"href": str(currenturl + "/v1/subscribers/" + str(self.key.id()))}
        data["name"] = self.name
        data["email"] = self.email
        data["fb_id"] = self.fb_id
        distribution = self.distribution.get()
        if expand:
            if expand == "distribution":
                data["distribution"] = distribution.to_object()
        else:
            meta = {"href": str(currenturl + "/efforts/" + str(distribution.key.id()))}
            data["distribution"] = {"meta": meta}
        return data

class Contact(ndb.Model):
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)
    name = ndb.StringProperty()
    contacts = ndb.StringProperty(repeated=True)
    email = ndb.StringProperty()
    facebook = ndb.StringProperty()
    twitter = ndb.StringProperty()

    def to_object(self, extended=""):
        details = {}
        details["meta"] = {"href": "http://api.bangonph.com/v1/contacts/" + str(self.key.id())}
        details["created"] = str(self.created)
        details["updated"] = str(self.updated)
        details["name"] = self.name
        details["contacts"] = self.contacts
        details["email"] = self.email
        details["facebook"] = self.facebook
        details["twitter"] = self.twitter
        details["id"] = self.key.id()
        return details

class Post(ndb.Model):
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)
    name = ndb.StringProperty(default="Anonymous")
    email = ndb.StringProperty()
    twitter = ndb.StringProperty()
    facebook = ndb.StringProperty()
    phone = ndb.StringProperty()
    message = ndb.TextProperty()
    post_type = ndb.StringProperty(repeated=True) # need or have (transpo, people, goods, needs, have )
    expiry = ndb.DateTimeProperty()
    status = ndb.StringProperty(default="ACTIVE") # expired cancelled active
    location = ndb.StringProperty()

    def to_object(self):
        details = {}
        details["meta"] = {"href": "http://api.bangonph.com/v1/posts/" + str(self.key.id())}
        details["created"] = str(self.created)
        details["updated"] = str(self.updated)
        details["name"] = self.name
        details["twitter"] = self.twitter
        details["facebook"] = self.facebook
        details["phone"] = self.phone
        details["message"] = self.message
        details["post_type"] = self.post_type
        if self.expiry:
            details["expiry"] = str(self.expiry)
            details["expiry_friendly"] = self.expiry.strftime("%b %d, %Y")
        else:
            details["expiry"] = None
            details["expiry_friendly"] = None
        details["status"] = self.status
        details["location"] = self.location
        details["id"] = self.key.id()
        return details


class LogActivity(ndb.Model):
    created = ndb.DateTimeProperty(auto_now_add=True)
    user = ndb.StringProperty()
    previous_values = ndb.JsonProperty()
    new_values = ndb.JsonProperty
    action = ndb.StringProperty()


class File(ndb.Model):
    title = ndb.StringProperty()
    blob_key = ndb.BlobKeyProperty()
    img_serving = ndb.StringProperty()
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)