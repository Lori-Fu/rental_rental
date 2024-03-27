import functools
import boto3
from flask import session, jsonify, g, current_app
from werkzeug.routing import BaseConverter

from rental_root.utils.response_code import RET
from rental_root import constants
import os
from dotenv import load_dotenv

load_dotenv()


class ReConverter(BaseConverter):
    def __init__(self, url_map, regex):
        super(ReConverter, self).__init__(url_map)
        self.regex = regex


def login_required(view_function):
    @functools.wraps(view_function)
    def wrapper(*args, **kwargs):
        user_id = session.get("user_id")
        if user_id is not None:
            g.user_id = user_id
            return view_function(*args, **kwargs)
        else:
            return jsonify(errno=RET.SESSIONERR, errmsg="Please log in")

    return wrapper


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in constants.ALLOWED_EXTENSIONS


def upload_to_s3(pictures, house_id):
    s3 = boto3.resource("s3")
    res = []
    try:
        for i in range(len(pictures)):
            picture = pictures[i]
            file_name = "image_" + house_id + "_" + str(i)
            s3.Bucket(os.getenv('AWS_S3_BUCKET_NAME')).upload_fileobj(picture, file_name)
            res.append(file_name)
        return res
    except Exception as e:
        current_app.logger.error(e)
        raise RuntimeError(e)


def check_type(pictures):
    for i in range(len(pictures)):
        picture = pictures[i]
        if not allowed_file(picture.filename):
            raise TypeError("File not allowed")
