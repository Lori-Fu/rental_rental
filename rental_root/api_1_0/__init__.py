from flask import Blueprint, jsonify
from flask_wtf.csrf import CSRFError
from rental_root.utils.response_code import RET

api = Blueprint("api_1_0", __name__)

from . import demo, passport, profile, houses, orders, payment


@api.errorhandler(CSRFError)
def handle_csrf_error(e):
    return jsonify(errno=RET.REQERR, errmsg="Please refresh page")
