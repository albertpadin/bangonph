import logging
import webapp2, jinja2, os
import datetime
from models import User, Contact, Location, Distribution, Post, DropOffCenter, Subscriber, Distributor
import json as simplejson

from google.appengine.ext import ndb
from google.appengine.api import urlfetch

from settings import SETTINGS
from settings import SECRET_SETTINGS
jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)), autoescape=True)


currenturl = str(os.environ['wsgi.url_scheme'])+"://"+str(os.environ['HTTP_HOST'])+"/"

def send_email(receiver_name=False,receiver_email=False,subject=False,content={},email_type=False):
    if not receiver_email or not receiver_name or not subject or not email_type:
        return False
    template = jinja_environment.get_template('frontend/newsletter.html')
    data = {}
    content['date'] = datetime.datetime.utcnow().strftime('%B %d, %Y %H:%M:%S')
    data['current_url'] = currenturl
    data['email_content'] = content
    data['type'] = email_type
    data['receiver_name'] = receiver_name
    data['receiver_email'] = receiver_email
    receiver = [{"email": receiver_email,"name": receiver_name}]
    send_via_mandrill(receiver, subject, html=template.render(data), plain_text = None, email_type = email_type)
    return True

def send_via_mandrill(receiver, subject, html=None, plain_text = None, email_type = None):
    data = {
    "key": SECRET_SETTINGS["mandrill_key"],
    "message": {
        "html": html,
        "subject": subject,
        "from_email": "company@email.com", #company email
        "from_name": "company name", #company name
        "to": receiver,
        "headers": {
            "Reply-To": "company@email.com" #company email that accepts reply
        },
        "tags": [
            "notifications",
            email_type
        ],
        "important": True,
        "track_opens": True,
        "track_clicks": True,
        "auto_text": True
        },
    "async": False
    }

    logging.debug(urlfetch.fetch(url="https://mandrillapp.com/api/1.0/" + "messages/send.json", method=urlfetch.POST, payload=simplejson.dumps(data)).content)

def send_reset_password_email(user, token):
    content = {}
    content['token'] = str(token)

    email = send_email(receiver_name=user.name,receiver_email=user.email,subject="Password Reset",content=content,email_type="reset_password")

    if email:
        return True
    else:
        return False


def slugify(value):
    return value.strip().lower().replace(' ','-').replace("'","").replace('"','').replace(",","").replace('--','-').replace('.','').replace('@','').replace('!','').replace('$','').replace('*','').replace('&','and').replace('(','').replace(')','').replace('+','plus').replace('=','').replace(':','').replace(';','').replace('<','').replace('>','').replace('/','').replace('?','').replace('~','').replace('`','')


def get_all_user(data):
    users = User.query(User.email != data).fetch(100)
    if users:
        datas = []
        for user in users:
            temp = {}
            temp["id"] = user.key.id()
            temp["name"] = user.name
            temp["email"] = user.email
            temp["contacts"] = user.contacts
            temp["permissions"] = user.permissions
            datas.append(temp)

        return datas

def add_user(data):
    user = User(id=data["email"])
    user.password = data["password"]
    user.name = data["name"]
    user.email = data["email"]
    user.contacts = data["contacts"]
    user.permissions = data["permissions"]

    user.put()
    return user

def update_user(data):
    user = data["user"]
    user.name = data["name"]
    user.contacts = data["contacts"]
    user.email = data["email"]
    user.permissions = data["permissions"]

    user.put()
    return user


def add_location(data, location_key=""):
    if location_key:
        location = Location.get_by_id(location_key)
    else:
        location_id = slugify(data["name"])
        temp_location_id = location_id
        while True:
            count = 1
            if Location.get_by_id(temp_location_id):
                temp_location_id = location_id + str(count)
                count += 1
            else:
                location = Location(id=temp_location_id)
                break

    if data["name"]:
        location.name = data["name"]

    if data["needs"]:
        location.needs = data["needs"]

    if data["centers"]:
        location.centers = data["centers"]

    if data["latlong"]:
        location.latlong = data["latlong"]

    if data["featured_photo"]:
        location.featured_photo = data["featured_photo"]

    if data["death_count"]:
        location.death_count = int(data["death_count"])

    if data["death_count_text"]:
        location.death_count_text = data["death_count_text"]

    if data["affected_count"]:
        location.affected_count = int(data["affected_count"])

    if data["affected_count_text"]:
        location.affected_count_text = data["affected_count_text"]

    if data["status_board"]:
        location.status_board = data["status_board"]

    if data["needs"]:
        location.needs = data["needs"]

    if data["status"]:
        location.status = data["status"]

    if data["images"]:
        location.images = data["images"]

    if data["hash_tag"]:
        location.hash_tag = data["hash_tag"]

    if data["featured"]:
        location.featured = data["featured"]

    if data["missing_person"]:
        location.missing_person = data["missing_person"]

    location.put()
    return location

def add_distribution(data, instance_id=""):
    if instance_id:
        distribution = Distribution.get_by_id(int(instance_id))
    else:
        distribution = Distribution()

    if data["date_of_distribution"]:
        distribution.date_of_distribution = data["date_of_distribution"]


    if data["contact"]:
        distribution.contact = data["contact"]

    if data["destinations"]:
        distribution.destinations = ndb.Key("Location", data["destinations"])

    if data["supply_goal"]:
        distribution.supply_goal = data["supply_goal"]

    if data["actual_supply"]:
        distribution.actual_supply = data["actual_supply"]

    if data["images"]:
        distribution.images = data["images"]

    if data["status"]:
        distribution.status = data["status"]

    if data["info"]:
        distribution.info = data["info"]

    if data["featured_photo"]:
        distribution.featured_photo = data["featured_photo"]

    if data["description"]:
        distribution.description = data["description"]

    distribution.put()

    return distribution

def add_drop_off_centers(data, instance_id=""):
    if instance_id:
        center = DropOffCenter.get_by_id(instance_id)
    else:
        center_id = slugify(data["name"])
        temp_center_id = center_id
        while True:
            count = 1
            if DropOffCenter.get_by_id(temp_center_id):
                temp_center_id = center_id + str(count)
                count += 1
            else:
                center = DropOffCenter(id=temp_center_id)
                break

    if data["name"]:
        center.name = data["name"]

    if data["drop_off_locations"]:
        center.drop_off_locations = data["drop_off_locations"].split(", ")

    if data["distributor"]:
        center.distributor = data["distributor"].split(", ")

    if data["address"]:
        center.address = data["address"]

    if data["latlong"]:
        center.latlong = data["latlong"]

    if data["destinations"]:
        center.destinations = data["destinations"].split(", ")

    if data["schedule"]:
        center.schedule = data["schedule"]

    if data["twitter"]:
        center.twitter = data["twitter"]

    if data["facebook"]:
        center.facebook = data["facebook"]

    if data["contacts"]:
        center.contacts = data["contacts"].split(", ")

    if data["email"]:
        center.email = data["email"]

    center.put()
    return center

def add_subcriber(data, instance_id=""):
    if instance_id:
        subscriber = Subscriber.get_by_id(str(instance_id))
    else:
        subscriber = Subscriber()

    if data["name"]:
        subscriber.name = data["name"]
    if data["email"]:
        subscriber.email = data["email"]
    if data["fb_id"]:
        subscriber.fb_id = data["fb_id"]
    if data["distribution"]:
        subscriber.distribution = ndb.Key("Distribution", data["distribution"])

    subscriber.put()
    return subscriber

def add_post(data, instance_id=""):
    if instance_id:
        post = Post.get_by_id(int(instance_id))
    else:
        post = Post()

    if data["name"]:
        post.name = data["name"]

    if data["email"]:
        post.email = data["email"]

    if data["twitter"]:
        post.twitter = data["twitter"]

    if data["facebook"]:
        post.facebook = data["facebook"]

    if data["phone"]:
        post.phone = data["phone"]

    if data["message"]:
        post.message = data["message"]

    if data["post_type"]:
        
        types = []
        for this_type in data["post_type"]:
            post_type = this_type.replace(" ", "_")
            types.append(post_type.upper())
        if post.post_type:
            for item in types:
                post.post_type.append(item)
        else:
            post.post_type = types

    if data["expiry"]:
        post.expiry = data["expiry"]

    if data["status"]:
        post.status = data["status"].upper()

    if data["location"]:
        post.location = data["location"]

    post.put()
    return post


def add_mock_post(data, instance_id=""):
    if instance_id:
        post = Post.get_by_id(int(instance_id))
    else:
        post = Post()

    if data["name"]:
        post.name = data["name"]

    if data["email"]:
        post.email = data["email"]

    if data["twitter"]:
        post.twitter = data["twitter"]

    if data["facebook"]:
        post.facebook = data["facebook"]

    if data["phone"]:
        post.phone = data["phone"]

    if data["message"]:
        post.message = data["message"]

    if data["post_type"]:
        
        types = []
        for this_type in data["post_type"]:
            post_type = this_type.replace(" ", "_")
            types.append(post_type.upper())
        if post.post_type:
            for item in types:
                post.post_type.append(item)
        else:
            post.post_type = types

    if data["expiry"]:
        post.expiry = data["expiry"]

    if data["status"]:
        post.status = data["status"].upper()

    if data["location"]:
        post.location = data["location"]

    return post


def add_contact(data, instance_id=""):
    if instance_id:
        contact = Contact.get_by_id(int(instance_id))
    else:
        contact = Contact()

    if data["name"]:
        contact.name = data["name"]

    if data["contacts"]:
        if contact.contacts:
            contact.contacts.append(data["contacts"])
        else:
            contact.contacts = data["contacts"]

    if data["email"]:
        contact.email = data["email"]

    if data["facebook"]:
        contact.facebook = data["facebook"]

    if data["twitter"]:
        contact.twitter = data["twitter"]

    contact.put()
    return contact


def add_distributor(data, instance_id=""):
    if instance_id:
        distributor = Distributor.get_by_id(int(instance_id))
    else:
        distributor = Distributor()

    if data["name"]:
        distributor.name = data["name"]

    if data["contact_num"]:
        distributor.contact_num = data["contact_num"]

    if data["email"]:
        distributor.email = data["email"]

    if data["website"]:
        distributor.website = data["website"]

    if data["facebook"]:
        distributor.facebook = data["facebook"]

    distributor.put()
    return distributor


def log_trail(data):
    log = LogActivity()
    log.user = data["user"]
    log.previous_values = data["previous_values"]
    log.new_values = data["new_values"]

    log.put()
    return log


def check_all_keys(keys=[], haystack=[]):
    for key in keys:
        if key not in haystack:
            return False
    return True
