from google.appengine.ext import ndb
from models import User

class Client(ndb.Model):
    client_id = ndb.StringProperty()
    client_name = ndb.StringProperty()
    secret_key = ndb.StringProperty()
    created = ndb.DateTimeProperty(auto_now_add=True)
    base_url = ndb.StringProperty()
    access_enabled = ndb.BooleanProperty(default=True)


class UserToken(ndb.Model):  # user session per client
    user = ndb.KeyProperty(kind="User")
    client = ndb.KeyProperty(kind="Client")
    token = ndb.StringProperty()
    created = ndb.DateTimeProperty(auto_now_add=True)
    code = ndb.StringProperty()
    expires = ndb.DateTimeProperty()


class Nonce(ndb.Model):
    client = ndb.KeyProperty(kind="Client")
    created = ndb.DateTimeProperty(auto_now_add=True)
    nonce = ndb.StringProperty()