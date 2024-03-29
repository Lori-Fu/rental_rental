from datetime import datetime
from . import db
# from werkzeug.security import generate_password_hash, check_password_hash
import bcrypt
from rental_root import constants


class BaseModel(object):
    create_time = db.Column(db.DateTime, default=datetime.now)
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


class User(BaseModel, db.Model):
    __tablename__ = "user_profile"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    email = db.Column(db.String(20), unique=True, nullable=False)
    avatar_url = db.Column(db.String(128))
    houses = db.relationship("House", backref="user")
    orders = db.relationship("Order", backref="user")

    @property
    def password(self):
        raise AttributeError("Cannot read password")

    @password.setter
    def password(self, value):
        # self.password_hash = generate_password_hash(value)
        bytes = value.encode()
        salt = bcrypt.gensalt()
        hash = bcrypt.hashpw(bytes, salt)
        self.password_hash = hash

    def check_password(self, value):
        # return check_password_hash(self.password_hash, value)
        userBytes = value.encode('utf-8')

        # checking password
        return bcrypt.checkpw(userBytes, self.password_hash.encode('utf-8'))


class Area(BaseModel, db.Model):
    __tablename__ = "area_info"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False)
    houses = db.relationship("House", backref="area")

    def to_dict(self):
        d = {
            "aid": self.id,
            "aname": self.name
        }
        return d


house_facility = db.Table(
    "house_facility",
    db.Column("house_id", db.Integer, db.ForeignKey("house_info.id"), primary_key=True),
    db.Column("facility_id", db.Integer, db.ForeignKey("facility_info.id"), primary_key=True)
)


class House(BaseModel, db.Model):
    __tablename__ = "house_info"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user_profile.id"), nullable=False)
    area_id = db.Column(db.Integer, db.ForeignKey("area_info.id"), nullable=False)
    title = db.Column(db.String(64), nullable=False)
    price = db.Column(db.Integer, default=0)
    address = db.Column(db.String(512), default="")
    room_count = db.Column(db.Integer, default=1)
    acreage = db.Column(db.Integer, default=0)
    unit = db.Column(db.String(32), default="")
    capacity = db.Column(db.Integer, default=1)
    beds = db.Column(db.String(64), default="")
    min_days = db.Column(db.Integer, default=1)
    max_days = db.Column(db.Integer, default=0)
    order_count = db.Column(db.Integer, default=0)
    index_image_url = db.Column(db.String(256), default="")
    facilities = db.relationship("Facility", secondary=house_facility)
    images = db.relationship("HouseImage")
    orders = db.relationship("Order", backref="house")

    def to_basic_dict(self):
        house_dict = {
            "house_id": self.id,
            "title": self.title,
            "price": self.price,
            "area_name": self.area.name,
            "img_url": constants.AWS_IMAGE_PREFIX + self.index_image_url if self.index_image_url else "",
            "room_count": self.room_count,
            "order_count": self.order_count,
            "address": self.address,
            "user_avatar": "",
            "ctime": self.create_time.strftime("%Y-%m-%d")
        }
        return house_dict

    def to_full_dict(self):
        house_dict = {
            "hid": self.id,
            "user_id": self.user_id,
            "user_name": self.user.name,
            "user_avatar": "",
            "title": self.title,
            "price": self.price,
            "address": self.address,
            "room_count": self.room_count,
            "acreage": self.acreage,
            "unit": self.unit,
            "capacity": self.capacity,
            "beds": self.beds,
            "min_days": self.min_days,
            "max_days": self.max_days,
        }

        img_urls = []
        for image in self.images:
            img_urls.append(constants.AWS_IMAGE_PREFIX + image.url)
        house_dict["img_urls"] = img_urls

        facilities = []
        for facility in self.facilities:
            facilities.append(facility.id)
        house_dict["facilities"] = facilities

        comments = []
        orders = Order.query.filter(Order.house_id == self.id, Order.status == "COMPLETED", Order.comment != None) \
            .order_by(Order.update_time.desc()).limit(constants.HOUSE_DETAIL_COMMENT_DISPLAY_COUNTS)
        for order in orders:
            comment = {
                "comment": order.comment,
                "user_name": order.user.name,
                "ctime": order.update_time.strftime("%Y-%m-%d %H:%M:%S")
            }
            comments.append(comment)
        house_dict["comments"] = comments
        return house_dict


class Facility(BaseModel, db.Model):
    __tablename__ = "facility_info"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False)

    def to_dict(self):
        d = {
            "fid": self.id,
            "fname": self.name
        }
        return d


class HouseImage(BaseModel, db.Model):
    __tablename__ = "house_image"

    id = db.Column(db.Integer, primary_key=True)
    house_id = db.Column(db.Integer, db.ForeignKey("house_info.id"), nullable=False)
    url = db.Column(db.String(256), nullable=False)

    def to_basic_dict(self):
        image_dict = {
            "image_id": self.id,
            "house_id": self.house_id,
            "url": constants.AWS_IMAGE_PREFIX + self.url,
        }
        return image_dict


class Order(BaseModel, db.Model):
    __tablename__ = "order_info"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user_profile.id"), nullable=False)
    house_id = db.Column(db.Integer, db.ForeignKey("house_info.id"), nullable=False)
    begin_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    days = db.Column(db.Integer, nullable=False)
    house_price = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    status = db.Column(
        db.Enum(
            "WAIT_ACCEPT",
            "WAIT_PAYMENT",
            "PAID",
            "WAIT_COMMENT",
            "COMPLETED",
            "CANCELED",
            "REJECTED"
        ),
        default="WAIT_ACCEPT", index=True)
    comment = db.Column(db.Text)
    trade_no = db.Column(db.String(80))

    def to_dict(self):
        order_dict = {
            "order_id": self.id,
            "title": self.house.title,
            "img_url": constants.AWS_IMAGE_PREFIX + self.house.index_image_url if self.house.index_image_url else "",
            "start_date": self.begin_date.strftime("%Y-%m-%d"),
            "end_date": self.end_date.strftime("%Y-%m-%d"),
            "ctime": self.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            "days": self.days,
            "amount": self.amount,
            "status": self.status,
            "comment": self.comment if self.comment else ""
        }
        return order_dict
