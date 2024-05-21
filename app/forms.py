from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, NumberRange
import sqlalchemy as sa
from app import db
from app.models import User
from flask_login import current_user

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')
    
    
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    room_number = IntegerField('Room Number', validators=[DataRequired(), NumberRange(min=0, max=1517)])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeated Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = db.session.scalar(sa.select(User).where(
            User.username == username.data))
        if user is not None:
            raise ValidationError('Username already registered')
        
class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired()])
    new_password2 = PasswordField('Repeat New Password', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Change Password')
    
    def validate_old_password(self, old_password):
        user = User.query.filter_by(username=current_user.username).first()
        if not user.check_password(old_password.data):
            raise ValidationError('Old password is incorrect')
        
class AddUserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    room_number = IntegerField('Room Number', validators=[DataRequired(), NumberRange(min=0, max=1517)])
    balance = IntegerField('Balance', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Add User')
    
    def validate_username(self, username):
        user = db.session.scalar(sa.select(User).where(
            User.username == username.data))
        if user is not None:
            raise ValidationError('Username already registered')
        
class AddBalanceForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    balance = IntegerField('Balance', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Add Balance')
    
    def validate_username(self, username):
        user = db.session.scalar(sa.select(User).where(
            User.username == username.data))
        if user is None:
            raise ValidationError('Username not found')
        

