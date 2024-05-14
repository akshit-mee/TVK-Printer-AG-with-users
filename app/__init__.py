from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import logging
from logging.handlers import RotatingFileHandler
import os
from flask_admin.contrib.sqla import ModelView
from flask_security import SQLAlchemyUserDatastore, Security

app = Flask(__name__)
app.config.from_object(Config)
login = LoginManager(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'login'
# conn = cups.Connection



if not app.debug:
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/PrinterAG.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    
    app.logger.setLevel(logging.INFO)
    app.logger.info('PrinterAG Startup')
    
    

from app import routes, models, errors

login.anonymous_user = models.Anonymous
# user_datastore = SQLAlchemyUserDatastore(db, models.User, models.Role)
# security = Security(app, user_datastore)