from copy import deepcopy
from decimal import *
from datetime import datetime, timedelta

from project import db, login
from flask import current_app, url_for
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash





class Manager(db.Model):
    __tablename__ = "managers"

    id = db.Column(db.Integer, primary_key=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class Log(db.Model):
    __tablename__ = "logs"

    id = db.Column(db.Integer, primary_key=True)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


# City Model
class City(db.Model):
    """
    A city shorname to full name mapping
    """
    __tablename__ = "citys"

    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String, nullable=False)
    short_value = db.Column(db.String, nullable=False)
    long_value = db.Column(db.String, nullable=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


# Property Model
class Property(db.Model):
    """
    Properties data
    * NOTE: If change schema, change the related config file as well
    """
    __tablename__ = "properties"
    __banlist__ = ['id', '_sa_instance_state']
    __default__ = {
        "Numeric" : -1.00,
        "Int" : -1,
        "String" : "",
    }
    __default_val__ = {
        type(Decimal('-1.00')) : -1.00,
        type(-1.00) : -1.00,
        type(-1) : -1,
        type("") : "",
    }

    # the var name would be the Column name in db
    # NOTE: neg values meaning not known
    id = db.Column(db.Integer, primary_key=True)
    mlsname = db.Column(db.String, nullable=False) # e.g: CRMLS

    listingkey_numeric = db.Column(db.String, nullable=False)
    listing_id = db.Column(db.String, nullable=False)
    status = db.Column(db.String, nullable=False)
    list_price = db.Column(db.Numeric(16,2), nullable=False) # money

    close_price = db.Column(db.Numeric(16,2), nullable=True, default=__default__["Numeric"]) # money
    original_price = db.Column(db.Numeric(16,2), nullable=True, default=__default__["Numeric"]) # money
    prev_price = db.Column(db.Numeric(16,2), nullable=True, default=__default__["Numeric"]) # money
    low_price = db.Column(db.Numeric(16,2), nullable=True, default=__default__["Numeric"]) # money

    city = db.Column(db.String, nullable=True, default=__default__["String"])
    streetname = db.Column(db.String, nullable=True, default=__default__["String"])
    postalcode = db.Column(db.String, nullable=True, default=__default__["String"])
    postalcodep4 = db.Column(db.String, nullable=True, default=__default__["String"])
    
    beds = db.Column(db.SmallInteger, nullable=True, default=__default__["Int"])
    baths = db.Column(db.SmallInteger, nullable=True, default=__default__["Int"])
    yearbuilt = db.Column(db.SmallInteger, nullable=True, default=__default__["Int"])
    stories = db.Column(db.SmallInteger, nullable=True, default=__default__["Int"])

    squarefeet = db.Column(db.Numeric(16,2), nullable=True, default=__default__["Numeric"])
    pricepersquare = db.Column(db.Numeric(8,2), nullable=True, default=__default__["Numeric"])
    acres = db.Column(db.Numeric(16,4), nullable=True, default=__default__["Numeric"])
    
    def __init__(self, **kwargs):
        """
        NOTE: the super().__init__(**kwargs) do the same thing as the code
        below does.
        :param kwargs:
        """
        super().__init__(**kwargs)

        #self.listingkey_numeric = kwargs['listingkey_numeric']
        #self.listing_id = kwargs['listing_id']
        #self.list_price = Decimal(kwargs['list_price'])
        #self.beds = int(kwargs['beds'])
        #self.city = kwargs['city']

    def __repr__(self):
       return '<Listingkey: %s>' % self.listingkey_numeric

    def diff(self, kwargs):
        """
        Check if the kwargs data is the same as the property instance
        for each val in return, [0] is the old val, [1] is the new val
        NOTE: this function changes NOTHING
        :param kwargs: dict
        :return: dict
        """
        var_dict = deepcopy(self.__dict__ )
        res = {}
        for key, val in var_dict.items():
            if key[0]=='_' or key in self.__banlist__:
                continue
            # if kwargs[key] is empty, val will be stored as None
            # val won't be None, know default val by self.__default__
            # kwargs[key] can be None, if None, compare to the default val
            if kwargs[key] is None:
                if val != self.__default_val__[type(val)]:
                # if val not in self.__default__.values(): # ugly but works
                    res[key] = [val, kwargs[key]]
            else:
                if val != type(val)(kwargs[key]):
                    res[key] = [val, kwargs[key]]
        return res

    def to_dict(self):
        """
        Gather all data of this property and return a dict
        :return: dict
        """
        var_dict = deepcopy(self.__dict__)
        data = {}
        for key, val in var_dict.items():
            if key[0] == '_' or key in self.__banlist__:
                continue
            else:
                data[key] = val
        return data

    def from_dict(self, data):
        """
        Update data from a dict
        :param data:
        :return:
        """
        flag = False
        var_dict = deepcopy(self.__dict__ ) # original data
        for key, val in data.items():
            if key in self.__banlist__:
                continue
            elif key in self.__dict__:
                if val is None:
                    # should set to default value
                    defaultval = self.__default_val__[type(var_dict[key])]
                    setattr(self, key, defaultval)
                else:
                    setattr(self, key, val)
                flag = True
        return flag

    def getallcolum(self):
        members = [attr for attr in dir(self)
                   if not callable(getattr(self, attr))
                   and not attr.startswith("__")]
        return members



# User Model
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    token = db.Column(db.String(32), index=True, unique=True)
    token_expiration = db.Column(db.DateTime)
    last_message_read_time = db.Column(db.DateTime)

    # TODO: set authen level

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'],
            algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

    def to_dict(self, include_email=False):
        data = {
            'id': self.id,
            'username': self.username,
            'last_seen': self.last_seen.isoformat() + 'Z',
            'about_me': self.about_me,
            'post_count': self.posts.count(),
            'follower_count': self.followers.count(),
            'followed_count': self.followed.count(),
            '_links': {
                'self': url_for('api.get_user', id=self.id),
                'followers': url_for('api.get_followers', id=self.id),
                'followed': url_for('api.get_followed', id=self.id),
                'avatar': self.avatar(128)
            }
        }
        if include_email:
            data['email'] = self.email
        return data

    def from_dict(self, data, new_user=False):
        for field in ['username', 'email', 'about_me']:
            if field in data:
                setattr(self, field, data[field])
        if new_user and 'password' in data:
            self.set_password(data['password'])

    def get_token(self, expires_in=3600):
        now = datetime.utcnow()
        if self.token and self.token_expiration > now + timedelta(seconds=60):
            return self.token
        self.token = base64.b64encode(os.urandom(24)).decode('utf-8')
        self.token_expiration = now + timedelta(seconds=expires_in)
        db.session.add(self)
        return self.token

    def revoke_token(self):
        self.token_expiration = datetime.utcnow() - timedelta(seconds=1)

    @staticmethod
    def check_token(token):
        user = User.query.filter_by(token=token).first()
        if user is None or user.token_expiration < datetime.utcnow():
            return None
        return user


@login.user_loader
def load_user(id):
    return User.query.get(int(id))
# end
