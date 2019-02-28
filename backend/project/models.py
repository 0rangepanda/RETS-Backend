from copy import deepcopy
from decimal import *
from datetime import datetime, timedelta
from sqlalchemy.sql.sqltypes import TIMESTAMP

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


# County Model (for CRMLS)
class County(db.Model):
    """
    A county shorname to full name mapping (for CRMLS)
    """
    __tablename__ = "counties"

    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String, nullable=False)
    short_value = db.Column(db.String, nullable=False)
    long_value = db.Column(db.String, nullable=False)
    cities = db.relationship('City', backref='counties', lazy=True) # one-to-many field
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


# City Model (for CRMLS)
class City(db.Model):
    """
    A city shorname to full name mapping (for CRMLS)
    """
    __tablename__ = "citys"

    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String, nullable=False)
    short_value = db.Column(db.String, nullable=False)
    long_value = db.Column(db.String, nullable=False)
    county = db.Column(db.Integer, db.ForeignKey('counties.id'), nullable=True)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


# Property Model
class Property(db.Model):
    """
    Properties data
    * NOTE: If change schema, change the related config file as well
    """
    __tablename__ = "properties"
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

    ## Nullable fields
    # price
    close_price = db.Column(db.Numeric(16,2), nullable=True, default=__default__["Numeric"]) # money
    original_price = db.Column(db.Numeric(16,2), nullable=True, default=__default__["Numeric"]) # money
    prev_price = db.Column(db.Numeric(16,2), nullable=True, default=__default__["Numeric"]) # money
    low_price = db.Column(db.Numeric(16,2), nullable=True, default=__default__["Numeric"]) # money
    reduce_price = db.Column(db.Numeric(16,2), nullable=True, default=__default__["Numeric"]) # money
    reduce_percent = db.Column(db.Numeric(8,2), nullable=True, default=__default__["Numeric"]) # percentage
    # location
    # county should be related to city
    city = db.Column(db.String, nullable=True, default=__default__["String"])
    streetname = db.Column(db.String, nullable=True, default=__default__["String"])
    postalcode = db.Column(db.String, nullable=True, default=__default__["String"])
    postalcodep4 = db.Column(db.String, nullable=True, default=__default__["String"])
    # infos
    beds = db.Column(db.SmallInteger, nullable=True, default=__default__["Int"])
    baths = db.Column(db.SmallInteger, nullable=True, default=__default__["Int"])
    yearbuilt = db.Column(db.SmallInteger, nullable=True, default=__default__["Int"])
    area = db.Column(db.Numeric(16,2), nullable=True, default=__default__["Numeric"])
    squarefeet = db.Column(db.Numeric(16,2), nullable=True, default=__default__["Numeric"])
    pricepersquare = db.Column(db.Numeric(6,2), nullable=True, default=__default__["Numeric"])
    # misc
    # a string that can convert to json. 
    # Any field that does not related to seaching, indexing or sorting goes here
    misc = db.Column(db.String, nullable=True, default=__default__["String"])
    # images
    coverimage = db.Column(db.String, nullable=True, default=__default__["String"])
    image = db.Column(db.String, nullable=True, default=__default__["String"])
    # timestamps
    created_on = db.Column(db.DateTime, server_default=db.func.now())
    updated_on = db.Column(db.DateTime, server_default=db.func.now(), server_onupdate=db.func.now())
    # others
    total_view = db.Column(db.Integer, default=0)
    # indexing
    # __table_args__ = (db.Index('listingkey_numeric', 'listing_id', 'list_price'), )
    # NOTE: ban list, not touched by any function 
    __banlist__ = ['id', '_sa_instance_state']
    # NOTE: no update list, not touched by self.diff(), 
    # but works with self.to_dict() and self.from_dict()
    __noupdatelist__ = ['coverimage', 'image', 'reduce_price', 'reduce_percent', 
                        'created_on', 'updated_on', 'total_view']

    def __init__(self, **kwargs):
        """
        NOTE: the super().__init__(**kwargs) do the same thing as the code
        below does.
        :param kwargs:
        """
        super().__init__(**kwargs)
        #could be negative, meaning price rised
        getcontext().prec = 2
        # reduce price and percent
        if kwargs['original_price'] and kwargs['list_price']:
            self.reduce_price = Decimal(kwargs['original_price']) - Decimal(kwargs['list_price'])
            if self.reduce_price>0 and Decimal(kwargs['original_price'])>0:
                reduce_percent = 100* self.reduce_price / Decimal(kwargs['original_price'])
                if abs(reduce_percent) > Decimal('10000.00'):
                    neg = reduce_percent / abs(reduce_percent)
                    self.reduce_percent = neg * Decimal('10000.00') # db.Numeric(6,2)
                else:
                    self.reduce_percent = reduce_percent


    def __repr__(self):
       return '<Listingkey: %s>' % self.listingkey_numeric

    def diff(self, kwargs):
        """
        Check if the kwargs data is the same as the property instance
        for each val in return, [0] is the old val, [1] is the new val
        NOTE: this function changes NOTHING
        :param kwargs: dict
        :return: dict of diff
        """
        var_dict = deepcopy(self.__dict__ )
        res = {}
        for key, val in var_dict.items():
            if key[0]=='_' or key in self.__banlist__ or key in self.__noupdatelist__:
                continue
            if key=='misc': # compare a dict str
                misc_self = eval(val)
                misc_kwargs = eval(kwargs[key])
                if misc_self != misc_kwargs:
                    for k in misc_self:
                        if misc_self[k] != misc_kwargs[k]:
                            res[k] = [misc_self[k], misc_kwargs[k]]
                continue
            # if kwargs[key] is empty, val will be stored as None
            # val won't be None, know default val by self.__default__
            # kwargs[key] can be None, if None, compare to the default val
            if kwargs[key] is None:
                if val != self.__default_val__[type(val)]:
                # if val not in self.__default__.values(): # ugly but works
                    res[key] = [val, kwargs[key]]
            else:
                if val != type(val)(kwargs[key]): # type(val): type casting
                    res[key] = [val, kwargs[key]]
        # if res is not empty, will update and call server_onupdate=db.func.now()
        if not res:
            self.updated_on = db.func.now()
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

    def update(self):
        """
        Timestamp and other caculated fields, called after self.from_dict()
        """
        getcontext().prec = 2
        if self.original_price!=self.__default__["Numeric"] and self.list_price!=self.__default__["Numeric"]:
            self.reduce_price = Decimal(self.original_price) - Decimal(self.list_price) 
            if self.reduce_price>0 and Decimal(self.original_price)>0:
                reduce_percent = 100* self.reduce_price / Decimal(self.original_price)
                if abs(reduce_percent) > Decimal('10000.00'):
                    neg = reduce_percent / abs(reduce_percent)
                    self.reduce_percent = neg * Decimal('10000.00') # db.Numeric(6,2)
                else:
                    self.reduce_percent = reduce_percent
        return True

    def from_dict(self, data):
        """
        Update data from a dict
        :param data:
        :return: True if any field is changed
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
        self.update()
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
