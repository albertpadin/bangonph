SETTINGS = {
    "app_id": "app_id_goes_here",
    "site_domain": "www.example.com",
    "site_name": "BangonPH",
    "start_year": 2012,
    "enable_fb_login": True,
    "fb_id": "759672407382550",
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
    "fb_secret": "220b69e931bc5790ada6b858a6cc68a7",
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
	invalid_date_format (406) - invalid date format
	invalid_cursor (406) - invalid cursor
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

# Dates since Typhoon
DATES = [
	"11/08/2013",
	"11/09/2013",
	"11/10/2013",
	"11/11/2013",
	"11/12/2013",
	"11/13/2013",
	"11/14/2013",
	"11/15/2013",
	"11/16/2013",
	"11/17/2013",
	"11/18/2013",
	"11/19/2013",
	"11/20/2013",
	"11/21/2013",
	"11/22/2013",
	"11/23/2013",
	"11/24/2013",
	"11/25/2013",
	"11/26/2013",
	"11/27/2013",
	"11/28/2013",
	"11/29/2013",
	"11/30/2013",
	"12/01/2013",
	"12/02/2013",
	"12/03/2013",
	"12/04/2013",
	"12/05/2013",
	"12/06/2013",
	"12/07/2013",
	"12/08/2013",
	"12/09/2013",
	"12/10/2013",
	"12/11/2013",
	"12/12/2013",
	"12/13/2013",
	"12/14/2013",
	"12/15/2013",
	"12/16/2013",
	"12/17/2013",
	"12/18/2013",
	"12/19/2013",
	"12/20/2013",
	"12/21/2013",
	"12/22/2013",
	"12/23/2013",
	"12/24/2013",
	"12/25/2013",
	"12/26/2013",
	"12/27/2013",
	"12/28/2013",
	"12/29/2013",
	"12/30/2013",
	"12/31/2013",
]

# RELIEF GOODS LAST HOW LONG IN DAYS?
FOOD_MULTIPLIER = 1
HYGIENE_MULTIPLIER = 3
SHELTER_MULTIPLIER = 20
MEDICINE_MULTIPLIER = 10
MEDICAL_MISSION_MULTIPLIER = 30

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