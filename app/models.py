from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, AnonymousUserMixin
from datetime import datetime, timezone
import pytz


class User(UserMixin, db.Model):
    
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index= True, unique = True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    weekly_limit: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=True)
    balance: so.Mapped[float] = so.mapped_column(sa.Float, nullable=True)
    pages_printed: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=True)
    weekly_print_number: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=True)
    room_number: so.Mapped[int] = so.mapped_column(sa.Integer)
    role_id: so.Mapped[int] = db.mapped_column(sa.ForeignKey('role.id'), index=True)
    role: so.Mapped['Role'] = so.relationship(backref=db.backref('users', lazy=True))
    prints: so.WriteOnlyMapped['Prints'] = so.relationship(back_populates='printed_by_name')
    fs_uniquifier: so.Mapped[str] = so.mapped_column(sa.String(64), unique = True, nullable=True)



    def __repr__(self):
        return '<User{}>'.format(self.username)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def can_print(self, number_of_pages):
        return (self.balance*20 >= number_of_pages)
            # and self.weekly_print_number + number_of_pages <= self.weekly_limit
    
    def post_printing(self, number_of_pages):
        self.pages_printed += number_of_pages
        self.balance -= number_of_pages*0.05

class Prints(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    number_of_pages: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=True)
    time_stamp: so.Mapped[datetime] = so.mapped_column(index=True, default=lambda: datetime.now(timezone.utc))
    printed_by_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True)
    printed_by_name: so.Mapped[User] = so.relationship(back_populates='prints')
    
class Role(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(80), unique=True, nullable = False)

@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))

class Anonymous(AnonymousUserMixin):
    def __init__(self):
        self.username = 'Guest'
        role_details = {'id':4, 'name': 'guest'}
        self.role = role_details