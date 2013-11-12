SETTINGS = {
    "app_id": "app_id_goes_here",
    "site_domain": "www.example.com",
    "site_name": "Bangon PH",
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