

from flask import Flask
import os
from config import urlize
from config import *
from db import *
from routes.auth_route import auth_bp
from routes.admin_route import admin_bp
from routes.chat_route import chatbot_bp
from routes.course_route import course_bp
from routes.upload_route import upload_bp
from routes.download_route import download_bp
from routes.export_route import export_bp
from routes.dashboard_route import dash_bp
from routes.tutoriel_route import tuto_bp
from routes.respo_coding_route import respo_bp

#l'email doit pas etre utilise dans l'url faut corriger ca 
#pour la messagerie les message sont bloques et pas tout s'affichent


#une mauvaise gestion de session ( la deconnection d'une personne n'est prise en compte que s'il appuie sur logout
#alors que ce n'est pas le seul cas a traiter 





app = Flask(__name__)
app.secret_key = APP_SECRET_KEY

#l'ensemble des routes (api endpoints)
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(chatbot_bp)
app.register_blueprint(upload_bp)
app.register_blueprint(download_bp)
app.register_blueprint(course_bp)
app.register_blueprint(export_bp)
app.register_blueprint(dash_bp)
app.register_blueprint(tuto_bp)
app.register_blueprint(respo_bp)



if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


app.jinja_env.filters['urlize'] = urlize

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)


