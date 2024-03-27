from . import api
from rental_root.utils.common import login_required
from rental_root.model import Order
from flask import g, current_app, jsonify, request
from rental_root.utils.response_code import RET
from rental_root.tasks.email.tasks import send_order_email

from rental_root import db
import requests
import base64
import os
from dotenv import load_dotenv

load_dotenv()

base = "https://api-m.sandbox.paypal.com"


@api.route("/order/<int:order_id>/payment", methods=["POST"])
@login_required
def payment(order_id):
    user_id = g.user_id

    try:
        order = Order.query.filter(Order.id == order_id, Order.user_id == user_id,
                                   Order.status == "WAIT_PAYMENT").first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="Database Error")
    if order is None:
        return jsonify(errno=RET.NODATA, errmsg="Invalid Request")
    try:
        http_status_code, json_response = create_order(order.amount/100)
        return jsonify(errno="0", errmsg="OK", data=json_response)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=500, errmsg=e)


def create_order(amount):
    access_token = generate_access_token()
    url = base + "/v2/checkout/orders"
    payload = '{ "intent": "CAPTURE", "purchase_units": [{"amount": {"currency_code": "USD","value": "%s"}}]}' % str(
        amount)

    try:
        response = requests.post(url=url,
                                 headers={"Content-Type": "application/json",
                                          "Authorization": "Bearer " + access_token},
                                 data=payload)
        return response.status_code, response.json()
    except Exception as e:
        return 500, response.json()["message"]


def generate_access_token():
    paypal_client_id = os.getenv("PAYPAL_CLIENT_ID")
    paypal_client_secret = os.getenv("PAYPAL_CLIENT_SECRET")

    try:
        if not paypal_client_id or not paypal_client_secret:
            raise RuntimeError("MISSING_API_CREDENTIALS")
        auth = paypal_client_id + ":" + paypal_client_secret
        auth = base64.b64encode(auth.encode()).decode()
        response = requests.post(base + "/v1/oauth2/token",
                                 data={"grant_type": "client_credentials"},
                                 headers={"Authorization": "Basic " + auth})
        data = response.json()
        return data["access_token"]
    except Exception as e:
        print("Failed to generate Access Token ", e)


@api.route("/order/<int:order_id>/<transaction_id>/capture", methods=["POST"])
@login_required
def save_order_payment_result(order_id, transaction_id):
    user_id = g.user_id

    try:
        order = Order.query.filter(Order.id == order_id, Order.user_id == user_id,
                                   Order.status == "WAIT_PAYMENT").first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="Database Error")

    if order is None:
        return jsonify(errno=RET.NODATA, errmsg="Invalid Request")

    try:
        http_status_code, json_response = capture_order(transaction_id)
        print(http_status_code, json_response)
        try:
            transaction = json_response["purchase_units"][0]["payments"]["captures"][0]
        except Exception as e:
            transaction = json_response["purchase_units"][0]["payments"]["authorizations"][0]
        print(transaction)
        trade_no = transaction["id"]
        status = transaction["status"]
        if status == "COMPLETED":
            send_order_email.delay(order.user.email, order.id)
            try:
                Order.query.filter_by(id=order_id).update({"status": "WAIT_COMMENT", "trade_no": trade_no})
                db.session.commit()
            except Exception as e:
                current_app.logger.error(e)
                db.session.rollback()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=500, errmsg="Transaction Failed")
    return jsonify(errno=http_status_code, errmsg="OK", data=json_response)


def capture_order(transaction_id):
    access_token = generate_access_token()
    url = (base + "/v2/checkout/orders/%s/capture") % transaction_id
    response = requests.post(url=url,
                             headers={"Content-Type": "application/json",
                                      "Authorization": "Bearer " + access_token})
    return response.status_code, response.json()
