from flask_login import UserMixin

from sqlalchemy.orm import relationship
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from datetime import datetime

from apps import db, login_manager
from flask_sqlalchemy import SQLAlchemy
from apps.authentication.util import hash_pass

db = SQLAlchemy()
class AuctionItem(db.Model):

    __tablename__ = 'auction_items'

    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.String(512), nullable=False)
    title = db.Column(db.Text, nullable=False)
    url = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(100), nullable=False)
    ends = db.Column(db.DateTime, nullable=False)
    description = db.Column(db.Text, nullable=False)
    current = db.Column(db.Float, nullable=False)
    open = db.Column(db.Float, nullable=False)
    reserve = db.Column(db.String(100), nullable=False)
    bids = db.Column(db.Integer, nullable=False)
    business = db.Column(db.String(255), nullable=False)
    updated = db.Column(db.Date, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'image': self.image,
            'title': self.title,
            'url': self.url,
            'status': self.status,
            'ends': self.ends,
            'description': self.description,
            'current': self.current,
            'open': self.open,
            'reserve': self.reserve,
            'bids': self.bids,
            'business': self.business,
            'updated': self.updated
        }
    
class Users(db.Model, UserMixin):

    __tablename__ = 'users'

    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(64), unique=True)
    email         = db.Column(db.String(64), unique=True)
    password      = db.Column(db.LargeBinary)
    first_name    = db.Column(db.String)
    last_name     = db.Column(db.String)
    address       = db.Column(db.Text)
    about         = db.Column(db.Text)

    oauth_github  = db.Column(db.String(100), nullable=True)

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)
            if hasattr(value, '__iter__') and not isinstance(value, str):
                # the ,= unpack of a singleton fails PEP8 (travis flake8 test)
                value = value[0]

            if property == 'password':
                value = hash_pass(value)  # we need bytes here (not plain str)

            setattr(self, property, value)

    def __repr__(self):
        return str(self.username)

    @classmethod
    def find_by_email(cls, email: str) -> "Users":
        return cls.query.filter_by(email=email).first()

    @classmethod
    def find_by_username(cls, username: str) -> "Users":
        return cls.query.filter_by(username=username).first()
    
    @classmethod
    def find_by_id(cls, _id: int) -> "Users":
        return cls.query.filter_by(id=_id).first()
   
    def save(self) -> None:
        try:
            db.session.add(self)
            db.session.commit()
          
        except SQLAlchemyError as e:
            db.session.rollback()
            db.session.close()
            error = str(e.__dict__['orig'])
            raise InvalidUsage(error, 422)
    
    def delete_from_db(self) -> None:
        try:
            db.session.delete(self)
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            db.session.close()
            error = str(e.__dict__['orig'])
            raise InvalidUsage(error, 422)
        return

@login_manager.user_loader
def user_loader(id):
    return Users.query.filter_by(id=id).first()

@login_manager.request_loader
def request_loader(request):
    username = request.form.get('username')
    user = Users.query.filter_by(username=username).first()
    return user if user else None

class OAuth(OAuthConsumerMixin, db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="cascade"), nullable=False)
    user = db.relationship(Users)
