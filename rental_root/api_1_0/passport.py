from . import api
from flask import request, jsonify, current_app, session
import re
from rental_root.utils.response_code import RET
from rental_root.model import User
from rental_root import redis_store, db
from sqlalchemy.exc import IntegrityError
from rental_root import constants


@api.route("/users", methods=["POST"])
def register():
    req_dict = request.get_json()

    email = req_dict.get("email")
    password = req_dict.get("password")
    password2 = req_dict.get("password2")

    if not all([email, password, password2]):
        return jsonify(errno=RET.PARAMERR, errmsg="Invalid param")

    if not re.match(r"^.+@.+\.(com)$", email):
        return jsonify(errno=RET.PARAMERR, errmsg="Invalid email")

    if not re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,16}$", password):
        return jsonify(errno=RET.PARAMERR, errmsg="Invalid password")

    if password != password2:
        return jsonify(errno=RET.PARAMERR, errmsg="Passwords do not match")

    # try:
    #     user = User.query.filter_by(email=email).first()
    # except Exception as e:
    #     current_app.logger.error(e)
    #     return jsonify(errno=RET.DBERR, errmsg="Database Error")
    # if user is not None:
    #     return jsonify(errno=RET.DATAEXIST, errmsg="Email already registered")

    user = User(name=email, email=email)
    user.password = password
    # print(user)
    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAEXIST, errmsg="Email already registered")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="Database Error")

    return jsonify(errno=RET.OK, errmsg="Success")


@api.route("/sessions", methods=["POST"])
def login():
    req_dict = request.get_json()

    email = req_dict.get("email")
    password = req_dict.get("password")

    if not all([email, password]):
        return jsonify(errno=RET.PARAMERR, errmsg="Invalid param")

    if not re.match(r"^.+@.+\.(com)$", email):
        return jsonify(errno=RET.PARAMERR, errmsg="Invalid email")

    if not re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,16}$", password):
        return jsonify(errno=RET.PARAMERR, errmsg="Invalid password")

    user_ip = request.remote_addr
    try:
        access = redis_store.get("access_%s" % user_ip)
    except Exception as e:
        current_app.logger.error(e)
    else:
        if access is not None and int(access) >= constants.LOGIN_ACCESS_TIME:
            return jsonify(errno=RET.REQERR, errmsg="Please try again later")

    try:
        user = User.query.filter_by(email=email).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="Database error")

    if user is None or not user.check_password(password):
        try:
            redis_store.incr("access_%s" % user_ip)
            redis_store.expire("access_%s" % user_ip, constants.LOGIN_FORBIDDEN_TIME)
        except Exception as e:
            current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg="Invalid email or password")

    session["name"] = user.name
    session["email"] = user.email
    session["user_id"] = user.id

    return jsonify(errno=RET.OK, errmsg="Success")


@api.route("/session", methods=["GET"])
def check_login():
    name = session.get("name")
    if name is not None:
        return jsonify(errno=RET.OK, errmsg="ok", data={"name": name})
    return jsonify(errno=RET.SESSIONERR, errmsg="false")


@api.route("/session", methods=["DELETE"])
def logout():
    session.clear()
    return jsonify(errno=RET.OK, errmsg="ok")

