appstats_CALC_RPC_COSTS = True

from gaesessions import SessionMiddleware
def webapp_add_wsgi_middleware(app):
	from google.appengine.ext.appstats import recording
	app = recording.appstats_wsgi_middleware(app)
    # To generate the cookie_key below, run the following:
    # ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits + "!@#$%^&*()-=+_[]}{;:'/.,<>?") for x in range(100))
	app = SessionMiddleware(app, cookie_key="!LHa-PU;Jtaitvd1#EXmKmDhP}Z43CXDNf3:qizp!O}Vzv['LU:P<f*UF]ro.wA10<qZ&1JIcW{Pgp&v{TPJ8eH.qI,0+P2?3=Tf")
	return app
