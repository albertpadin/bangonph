from oauth_models import *
import datetime
from requests import Response
from cStringIO import StringIO
from google.appengine.ext import ndb
from google.appengine.api import urlfetch
import random
import logging
import json
from oauth_helpers import *


class Resp(object):
    def __init__(self):
        self._status = 200
        self._headers = None
        self._content = {}

    @property
    def status_code(self):
        return self._status

    @status_code.setter
    def status_code(self, value):
        self._status = value

    @property
    def headers(self):
        return self._headers

    @headers.setter
    def headers(self, value):
        self._headers = value

    @property
    def content(self):
        return self._content

    @content.setter
    def content(self, value):
        self._content = value



class Provider(object):

    def _make_response(self, body={}, headers=None, status_code=200):
        # res = Response()
        # res.status_code = status_code
        # if headers is not None:
        #     res.headers.update(headers)
        # res.raw = body
        # logging.info(body)
        # return res

        res = Resp()
        res.status_code = status_code
        if headers is not None:
            res.headers = headers
        res.content = body
        logging.info(body)
        return res

    def _make_redirect_error_response(self, redirect_uri, err, status_code=200):
        params = {
            'error': err,
            'response_type': None,
            'client_id': None,
            'redirect_uri': None
        }
        redirect = build_url(redirect_uri, params)
        return self._make_response(body=params,
                                    headers={'Location': str(redirect)},
                                    status_code=status_code)

    def _make_json_response(self, data, headers=None, status_code=200):
        response_headers = {}
        if headers is not None:
            response_headers.update(headers)
        response_headers['Content-Type'] = 'application/json;charset=UTF-8'
        response_headers['Cache-Control'] = 'no-cache'
        response_headers['Pragma'] = 'no-cache'
        return self._make_response(data,
                                   response_headers,
                                   status_code)

    def _make_json_error_response(self, err):
        return self._make_json_response({'error': str(err)}, status_code=400)

    def _invalid_redirect_uri_response(self):
        return self._make_json_error_response('invalid_request')



class AuthorizationProvider(Provider):
    @property
    def token_length(self):
        return 40

    @property
    def token_expires_in(self):
        """ expiration in seconds """
        return 604800  # 7 days

    def generate_authorization_code(self):
        return random_ascii_string(self.token_length)

    def generate_access_token(self):
        return random_ascii_string(self.token_length)

    def generate_refresh_token(self):
        return random_ascii_string(self.token_length)

    def get_authorization_code(self,
                               client_id,
                               user_id,
                               redirect_uri,
                               **params):

        # Check conditions
        is_valid_client_id = self.validate_client_id(client_id)
        is_valid_user_id = self.validate_user_id(user_id)

        # Return proper error responses on invalid conditions
        if not is_valid_client_id:
            err = 'unauthorized_client'
            return self._make_redirect_error_response(redirect_uri, err, 401)
        if not is_valid_user_id:
            err = 'user_does_not_exist'
            return self._make_redirect_error_response(redirect_uri, err, 401)

        # Check redirect URI
        is_valid_redirect_uri = self.validate_redirect_uri(client_id,redirect_uri)
        if not is_valid_redirect_uri:
            return self._invalid_redirect_uri_response()

        has_active_token = self.check_active_token(client_id, user_id)

        if has_active_token:
            code = has_active_token
        else:
            # if no active tokens
            # Generate authorization token
            for i in range(0,3):
                token = self.generate_authorization_code()
                token_exist = self.check_access_token(token)
                if token_exist:  # check if it exists
                    pass
                else:
                    break
                if i == (limit - 1):
                    return self._make_json_error_response('cannot_generate_token')
            # Generate authorization code
            for i in range(0,3):
                code = self.generate_authorization_code()
                code_exist = self.check_access_code(code)
                if code_exist:  # check if it exists
                    pass
                else:
                    break
                if i == (limit - 1):
                    return self._make_json_error_response('cannot_generate_code')

            # Save information to be used to validate later requests
            self.persist_authorization_code(client_id=client_id,
                                        user_id=user_id,
                                        access_token=token,
                                        code=code)

        # Return redirection response
        params.update({
            'code': code,
            'response_type': None,
            'client_id': None,
            'redirect_uri': None
        })
        redirect = build_url(redirect_uri, params)
        return self._make_response(body=params,
                                    headers={'Location': str(redirect)},
                                    status_code=200)

    def check_active_token(self, client_id, user_id):
        logging.info("validata_client_id")
        client = ndb.Key("Client", client_id)
        user = ndb.Key("User", user_id)
        active = UserToken.query(UserToken.client == client, UserToken.expires >= datetime.datetime.now(), UserToken.user == user).get()
        if active:
            return active.code

        return False

    def validate_client_id(self, client_id):
        logging.info("validata_client_id")
        client = Client.get_by_id(client_id)
        if client:
            return client.access_enabled
        return False

    def validate_user_id(self, user_id):
        logging.info("validata_client_id")
        user = User.get_by_id(user_id)
        if user:
            if user.permissions is None:
                return True
        return False

    def validate_redirect_uri(self, client_id, redirect_uri):
        logging.info("validate_redirect_uri")
        url = redirect_uri
        client = Client.get_by_id(client_id)
        # check if redirect url is not the same as bangonPH url
        #
        if client:
            if not client.base_url in url:
                return False
        else:
            return False
        result = urlfetch.fetch(url)
        if result.status_code == 200:
            return True
        return False

    def check_access_token(self, token):
        logging.info("check_access_token")
        token = UserToken.get_by_id(token)
        if token:
            return True
        return False

    def check_access_code(self, code):
        logging.info("check_access_code")
        code = UserToken.query(UserToken.code == code).get()
        if code:
            return True
        return False

    def persist_authorization_code(self, client_id, user_id, access_token, code):
        logging.info("persist_authorization_code")
        client_token = UserToken(id=access_token)
        client_token.client = ndb.Key("Client", client_id)
        client_token.user = ndb.Key("User", user_id)
        client_token.token = access_token
        client_token.code = code
        client_token.expires = datetime.datetime.now() + datetime.timedelta(seconds=self.token_expires_in)
        client_token.put()
