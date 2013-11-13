import logging
import webapp2, jinja2, os
import datetime
from models import User, Contact, Location, Distribution, Post
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

def add_location(data):
    location = Location()
    location.name = data["name"]
    location.needs = data["needs"]
    location.centers = data["centers"]
    location.latlong = data["latlong"]
    location.featured_photo = data["featured_photo"]
    location.death_count = int(data["death_count"])
    location.affected_count = int(data["affected_count"])
    location.status_board = data["status_board"]
    location.needs = data["needs"]
    location.status = data["status"]
    
    location.put()
    return location

def add_destribution(data):
    distribution = Distribution()
    distribution.date_of_distribution = data["date_of_distribution"]
    distribution.contact = ndb.Key('Contact', int(data["contact"]))
    distribution.destinations = ndb.Key('Location', int(data["destinations"]))
    distribution.supply_goal = data["supply_goal"]
    distribution.actual_supply = data["actual_supply"]
    distribution.put()
    return distribution

def add_drop_off_centers(data):
    center = DropOffCenter(id=data["name"])
    center.drop_off_locations = data["drop_off_locations"]
    center.distributor = data["distributor"]
    center.address = data["address"]
    center.latlong = data["latlong"]
    center.destinations = data["destinations"]
    center.schedule = data["schedule"]
    center.twitter = data["twitter"]
    center.facebook = data["facebook"]
    center.contacts = data["contacts"]
    center.email = data["email"]

    center.put()
    return center

def add_subcriber(data):
    subscriber = Subscriber()
    subscriber.name = data["name"]
    subscriber.email = data["email"]
    subscriber.fb_id = data["fb_id"]
    subscriber.distribution = data["distribution"]

    subscriber.put()
    return subscriber
    
def add_post(data):
    post = Post()
    post.name = data["name"]
    post.email = data["email"]
    post.twitter = data["twitter"]
    post.facebook = data["facebook"]
    post.phone = data["phone"]
    post.message = data["message"]

    post.put()
    return post

def add_contact(data):
    contact = Contact()
    contact.name = data["name"]
    contact.contacts = data["contacts"]
    contact.email = data["email"]
    contact.facebook = data["facebook"]
    contact.twitter = data["twitter"]

    contact.put()
    return contact


def log_trail(data):
    log = LogActivity()
    log.user = data["user"]
    log.previous_values = data["previous_values"]
    log.new_values = data["new_values"]

    log.put()
    return log
