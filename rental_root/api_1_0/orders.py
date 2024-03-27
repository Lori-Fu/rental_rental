import datetime

from flask import request, g, jsonify, current_app
from rental_root import db, redis_store
from rental_root.utils.common import login_required
from rental_root.utils.response_code import RET
from rental_root.model import House, Order, User
from rental_root.tasks.email.tasks import send_order_email
from . import api


@api.route("/orders", methods=["POST"])
@login_required
def save_order():
    user_id = g.user_id

    order_data = request.get_json()
    if not order_data:
        return jsonify(errno=RET.PARAMERR, errmsg="Invalid Param")

    house_id = order_data.get("house_id")
    start_date_str = order_data.get("start_date")
    end_date_str = order_data.get("end_date")
    if not all((house_id, start_date_str, end_date_str)):
        return jsonify(errno=RET.PARAMERR, errmsg="Invalid Param")

    try:
        start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d")
        assert start_date <= end_date
        days = (end_date - start_date).days  # datetime.timedelta
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="Invalid dates")

    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="Database Error")
    if not house:
        return jsonify(errno=RET.NODATA, errmsg="Invalid house")

    if user_id == house.user_id:
        return jsonify(errno=RET.ROLEERR, errmsg="You are the owner of the house")

    try:
        count = Order.query.filter(Order.house_id == house_id, Order.begin_date <= end_date,
                                   Order.end_date >= start_date).count()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="Database Error")
    if count > 0:
        return jsonify(errno=RET.DATAERR, errmsg="Unavailable dates")

    amount = days * house.price

    order = Order(
        house_id=house_id,
        user_id=user_id,
        begin_date=start_date,
        end_date=end_date,
        days=days,
        house_price=house.price,
        amount=amount
    )
    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="Database Error")
    return jsonify(errno=RET.OK, errmsg="OK", data={"order_id": order.id})


@api.route("/user/orders", methods=["GET"])
@login_required
def get_user_orders():
    user_id = g.user_id

    role = request.args.get("role", "")

    try:
        if "landlord" == role:
            houses = House.query.filter(House.user_id == user_id).all()
            houses_ids = [house.id for house in houses]
            orders = Order.query.filter(Order.house_id.in_(houses_ids)).order_by(Order.create_time.desc()).all()
        else:
            orders = Order.query.filter(Order.user_id == user_id).order_by(Order.create_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="Database Error")

    orders_dict_list = []
    if orders:
        for order in orders:
            orders_dict_list.append(order.to_dict())

    return jsonify(errno=RET.OK, errmsg="OK", data={"orders": orders_dict_list})


@api.route("/orders/<int:order_id>/status", methods=["PUT"])
@login_required
def accept_reject_order(order_id):
    user_id = g.user_id

    req_data = request.get_json()
    if not req_data:
        return jsonify(errno=RET.PARAMERR, errmsg="Invalid Param")

    action = req_data.get("action")
    if action not in ("accept", "reject"):
        return jsonify(errno=RET.PARAMERR, errmsg="Invalid Param")

    try:
        order = Order.query.filter(Order.id == order_id, Order.status == "WAIT_ACCEPT").first()
        house = order.house
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="Database Error")

    if not order or house.user_id != user_id:
        return jsonify(errno=RET.REQERR, errmsg="Not authorized")

    if action == "accept":
        order.status = "WAIT_PAYMENT"
    elif action == "reject":
        reason = req_data.get("reason")
        if not reason:
            return jsonify(errno=RET.PARAMERR, errmsg="Invalid Param")
        order.status = "REJECTED"
        order.comment = reason

    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="Database Error")

    return jsonify(errno=RET.OK, errmsg="OK")


@api.route("/orders/<int:order_id>/payment", methods=["POST"])
@login_required
def save_order_payment(order_id):
    user_id = g.user_id
    user = User.query.get(user_id)
    try:
        order = Order.query.filter(Order.id == order_id, Order.user_id == user_id,
                                   Order.status == "WAIT_PAYMENT").first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="Database Error")

    if not order:
        return jsonify(errno=RET.REQERR, errmsg="Invalid request")

    try:
        order.status = "WAIT_COMMENT"
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="Database Error")

    # TODO: send email
    send_order_email.delay(user.email, order)

    return jsonify(errno=RET.OK, errmsg="OK")


@api.route("/orders/<int:order_id>/comment", methods=["PUT"])
@login_required
def save_order_comment(order_id):
    user_id = g.user_id

    req_data = request.get_json()
    comment = req_data.get("comment")

    if not comment:
        return jsonify(errno=RET.PARAMERR, errmsg="Invalid Param")

    try:
        order = Order.query.filter(Order.id == order_id, Order.user_id == user_id,
                                   Order.status == "WAIT_COMMENT").first()
        house = order.house
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="Database Error")

    if not order:
        return jsonify(errno=RET.REQERR, errmsg="Invalid Request")

    try:
        order.status = "COMPLETED"
        order.comment = comment
        house.order_count += 1
        db.session.add(order)
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="Database Error")

    try:
        redis_store.delete("house_info_%s" % order.house.id)
    except Exception as e:
        current_app.logger.error(e)

    return jsonify(errno=RET.OK, errmsg="OK")


@api.route("/order/<int:order_id>", methods=["GET"])
@login_required
def get_order(order_id):
    user_id = g.user_id

    try:
        order = Order.query.filter(Order.id == order_id, Order.user_id == user_id).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="Database Error")

    if order:
        return jsonify(errno=RET.OK, errmsg="OK", data={"order": order})
    else:
        return jsonify(errno=RET.REQERR, errmsg="Invalid Request")