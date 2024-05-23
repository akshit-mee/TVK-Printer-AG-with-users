import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'random-string-for-sequrity'
    
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'app.db')

class user_default:
    weekly_limit = 10
    balance = 0
    pages_printed = 0 
    weekly_print_number = 0
    room_number = 9999
    role_id = 3
    banned = False
    print_cost = 0.05
    registered = False