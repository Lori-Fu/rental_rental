from flask import g, current_app, jsonify, request, session

from . import api
from rental_root.utils.common import login_required
from rental_root.utils.response_code import RET
from rental_root.model import User
from rental_root import db


@api.route("/profile/session", methods=["GET"])
@login_required
def get_session():
    name = session.get('name')
    email = session.get('email')
    return jsonify(errno=RET.OK, errmsg="Success", data={"name": name, "email": email})


@api.route("/users/name", methods=["POST"])
@login_required
def set_user_name():
    user_id = g.user_id
    username = request.get_json().get("name")
    if username is None:
        return jsonify(errno=RET.PARAMERR, errmsg="Invalid Input")
    try:
        User.query.filter_by(id=user_id).update({"name": username})
        db.session.commit()
        session["name"] = username
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="Update failed")

    return jsonify(errno=RET.OK, errmsg="Success", data={"name": username})



