

from flask import Flask
import os
from config import urlize
from config import *
from utils.db import *
from routes.auth_2 import auth_bp
from routes.admin_route import admin_bp
from routes.dashboard_route import dash_bp







app = Flask(__name__)
app.secret_key = APP_SECRET_KEY

#l'ensemble des routes (api endpoints)
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(dash_bp)




app.jinja_env.filters['urlize'] = urlize

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False,port=5002)


