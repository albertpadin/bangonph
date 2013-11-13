SETTINGS = {
    "app_id": "app_id_goes_here",
    "site_domain": "www.example.com",
    "site_name": "BangonPH",
    "start_year": 2012,
    "enable_fb_login": True,
    "fb_id": "",
    "fb_secret": "",
    "fb_permissions": ["email"],
    "fb_app_access_token": "",
    "pubnub_subscriber_token": "",
    "pubnub_publisher_token": "",
    "pubnub_secret_key": "",
    "google_analytics_code": "",
    "password_salt": "ENTER_SALT_HERE"  # Only set once. Do NOT change. If changed, users will not be able to login
}

SECRET_SETTINGS = {
    "fb_secret": "",
    "fb_app_access_token": "",
    "pubnub_secret_key": "",
    "password_salt": "ENTER_SALT_HERE",  # Only set once. Do NOT change. If changed, users will not be able to login
    "mandrill_key": "VOGMtY1YpD0bNmMIt2bMPQ"
}

OAUTH_RESP = {
	"response": "ok", # ok||invalid_client||invalid_code||missing_params
	"code": 200,  # 200||404||404||406
	"success": {
        "access_token": "",
        "expires_in": "",
        "token_code": ""
    }
}

API_OAUTH_RESP = {
	"response": "ok",
	"code": 200,
	"type": "",
	"message": ""
}

# ------------
"""
	### FOR DOCUMENTATION PURPOSES ###

	*** please put created response, e.g. "ok", "invalid_instance", etc. ***
	start:
	format: {response_string} ({code}) - {description}

	ok (200) - success
	invalid_instance (404) - instance not found, or incorrect instance id
	cannot_create (500) - i dont even know what happened!
	missing_params (406) - missing parameterssss
"""
#-------------

API_RESPONSE = {
	"response": "ok",
	"code": 200,
	"data": {},
	"type": "",
	"method": "",
	"property": "",
	"description": ""
}

API_RESPONSE_DATA = {
	"meta": {
		"href": "", # uri of the instance
	},
	"parent": {
		"meta": {
			"href": "", # uri of the parent model or instance
		}
	},
	"children": {
		"meta": {
			"href": "", # uri for the children instances if any
		}
	},
	"id": "", # i dont know, for now same as instance id
	"name": "", # general name for indentity or frontend display purposes
	"instance_id": "" # model instance id
}

# Local Settings
import os
def development():
    if os.environ['SERVER_SOFTWARE'].find('Development') == 0:
        return True
    else:
        return False


if development():
    SETTINGS["fb_id"] = "569550796388888"
    SECRET_SETTINGS["fb_secret"] = "be20b1c85858844bf561c82e139b25e8"
    SECRET_SETTINGS['fb_app_access_token'] = "539310509418887|dPefXXFnqaygLJ8RxWG_-9Xm9JY"