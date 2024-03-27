from flask import jsonify, current_app, request, g, session
from datetime import datetime
import json
from rental_root import redis_store, db
from . import api
from rental_root.utils.response_code import RET
from rental_root.model import User, Area, House, Facility, HouseImage, Order
from rental_root.utils.common import login_required, upload_to_s3, check_type
from rental_root import constants


@api.route("/areas")
def get_area():
    try:
        data = redis_store.get("area_info")
    except Exception as e:
        current_app.logger.error(e)
    if data is None:
        try:
            areas = Area.query.all()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="Database Error")

        res = []
        for area in areas:
            res.append(area.to_dict())

        data = json.dumps(res)
        try:
            redis_store.setex("area_info", constants.AREA_CACHE_EXPIRE_TIME, data)
        except Exception as e:
            current_app.logger.error(e)
        # print(data)
    return jsonify(errno=RET.OK, errmsg="success", data={"areas": json.loads(data)})


@api.route("/facilities")
def get_facility():
    try:
        data = redis_store.get("facility_info")
    except Exception as e:
        current_app.logger.error(e)
    if data is None:
        try:
            facilities = Facility.query.all()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="Database Error")

        res = []
        for facility in facilities:
            res.append(facility.to_dict())

        data = json.dumps(res)
        try:
            redis_store.setex("facility_info", constants.FACILITY_CACHE_EXPIRE_TIME, data)
        except Exception as e:
            current_app.logger.error(e)

    return jsonify(errno=RET.OK, errmsg="success", data={"facilities": json.loads(data)})


@api.route("/houses", methods=["POST"])
@login_required
def save_house():
    user_id = g.user_id
    house_data = request.get_json()

    title = house_data.get("title")
    price = house_data.get("price")
    area_id = house_data.get("area_id")
    address = house_data.get("address")
    room_count = house_data.get("room_count")
    acreage = house_data.get("acreage")
    unit = house_data.get("unit")
    capacity = house_data.get("capacity")
    beds = house_data.get("beds")
    min_days = house_data.get("min_days")
    max_days = house_data.get("max_days")

    if not all(
            [title, price, area_id, address, room_count, acreage, unit, capacity, beds, min_days, max_days]):
        return jsonify(errno=RET.PARAMERR, errmsg="Invalid param")

    try:
        price = int(float(price) * 100)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="Invalid param")

    try:
        area = Area.query.get(area_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="Database Error")

    if area is None:
        return jsonify(errno=RET.NODATA, errmsg="Invalid area")

    house = House(
        user_id=user_id,
        area_id=area_id,
        title=title,
        price=price,
        address=address,
        room_count=room_count,
        acreage=acreage,
        unit=unit,
        capacity=capacity,
        beds=beds,
        min_days=min_days,
        max_days=max_days
    )

    facility_ids = house_data.get("facility")

    if facility_ids:
        # ["7","8"]
        try:
            facilities = Facility.query.filter(Facility.id.in_(facility_ids)).all()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="Database Error")

        if facilities:
            house.facilities = facilities

    try:
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="Database Error")

    return jsonify(errno=RET.OK, errmsg="OK", data={"house_id": house.id})


@api.route("/houses/image", methods=["POST"])
@login_required
def upload_images():
    house_images = request.files.getlist("house_image")
    house_id = request.form.get("house_id")

    if not all([house_images, house_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="Invalid param")

    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="Database Error")

    if house is None:  # if not house:
        return jsonify(errno=RET.PARAMERR, errmsg="Invalid param")

    try:
        check_type(house_images)
    except Exception as e:
        return jsonify(errno=RET.DBERR, errmsg="File not supported")

    try:
        images_url = upload_to_s3(house_images, house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="Image upload failed")

    for image_url in images_url:
        house_image = HouseImage(house_id=house_id, url=image_url)
        db.session.add(house_image)

    if not house.index_image_url:
        house.index_image_url = images_url[0]
        db.session.add(house)

    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="Database Error")

    return jsonify(errno=RET.OK, errmsg="OK", data={"hid": house_id})


@api.route("/user/houses", methods=["GET"])
@login_required
def get_user_houses():
    user_id = g.user_id

    try:
        user = User.query.get(user_id)
        houses = user.houses
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="Database Error")

    houses_list = []
    if houses:
        for house in houses:
            houses_list.append(house.to_basic_dict())
    return jsonify(errno=RET.OK, errmsg="OK", data={"houses": houses_list})


@api.route("/houses/index", methods=["GET"])
def get_house_index():
    try:
        ret = redis_store.get("home_page_data")
    except Exception as e:
        current_app.logger.error(e)
        ret = None

    if ret:
        current_app.logger.info("hit house index info redis")
        return jsonify(errno=0, errmsg="OK", data={"houses": json.loads(ret)})

    else:
        try:
            houses = House.query.order_by(House.order_count.desc()).limit(constants.HOME_PAGE_MAX_HOUSES)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="Database Error")

        if not houses:
            return jsonify(errno=RET.NODATA, errmsg="No Data")

        houses_list = []
        for house in houses:
            if not house.index_image_url:
                continue
            houses_list.append(house.to_basic_dict())

        json_houses = json.dumps(houses_list)
        try:
            redis_store.setex("home_page_data", constants.HOME_PAGE_DATA_REDIS_EXPIRES, json_houses)
        except Exception as e:
            current_app.logger.error(e)

        return jsonify(errno=0, errmsg="OK", data={"houses": houses_list})


@api.route("/houses", methods=["GET"])
def get_house_list():
    start_date = request.args.get("sd", "")
    end_date = request.args.get("ed", "")
    area_id = request.args.get("aid", "")
    sort = request.args.get("sort", "0")
    page = request.args.get("p")

    try:
        if start_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
        if start_date and end_date:
            assert start_date < end_date
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="Invalid param")

    if area_id:
        try:
            area = Area.query.get(area_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.PARAMERR, errmsg="Invalid param")

    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    redis_key = constants.REDIS_HOUSE_LIST_PREFIX + "_%s_%s_%s_%s" % (start_date, end_date, area_id, sort)

    try:
        json_res = redis_store.hget(redis_key, page)
    except Exception as e:
        current_app.logger.error(e)
    else:
        if json_res:
            res = json.loads(json_res)
            return jsonify(errno=0, errmsg="OK", data=res)

    filter_params = []
    conflict_orders = None
    try:
        if start_date and end_date:
            # select * from order where order.begin_date<end_date and order.end>start_date
            conflict_orders = Order.query.filter(Order.begin_date <= end_date, Order.end_date >= start_date).all()
        elif start_date:
            conflict_orders = Order.query.filter(Order.end_date >= start_date).all()
        elif end_date:
            conflict_orders = Order.query.filter(Order.begin_date <= end_date).all()

    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="Database Error")

    if conflict_orders:
        conflict_house_id = [order.house_id for order in conflict_orders]
        if conflict_house_id:
            filter_params.append(House.id.notin_(conflict_house_id))

    if area_id:
        filter_params.append(House.area_id == area_id)

    if sort == "1":
        house_query = House.query.filter(*filter_params).order_by(House.order_count.desc())
    elif sort == "2":
        house_query = House.query.filter(*filter_params).order_by(House.price.asc())
    elif sort == "3":
        house_query = House.query.filter(*filter_params).order_by(House.price.desc())
    else:
        house_query = House.query.filter(*filter_params).order_by(House.create_time.desc())

    try:
        page_obj = house_query.paginate(page=page, per_page=constants.HOUSE_LIST_PAGE_SIZE, error_out=False)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="Database Error")

    houses_list = []
    for house in page_obj.items:
        houses_list.append(house.to_basic_dict())
    total_pages = page_obj.pages
    res = {"houses": houses_list, "total_pages": total_pages, "current_page": page}
    json_res = json.dumps(res)

    try:
        pipeline = redis_store.pipeline()
        pipeline.multi()
        pipeline.hset(redis_key, page, json_res)
        pipeline.expire(redis_key, constants.HOUSE_LIST_REDIS_EXPIRES)
        pipeline.execute()
    except Exception as e:
        current_app.logger.error(e)

    return jsonify(errno=0, errmsg="OK", data=res)


@api.route("/house/<int:house_id>", methods=["GET"])
def get_house(house_id):
    if not house_id:
        return jsonify(errno=RET.PARAMERR, errmsg="Invalid Param")
    user_id = session.get("user_id", "-1")

    try:
        ret = redis_store.get("house_info_%s" % house_id)
    except Exception as e:
        current_app.logger.error(e)
        ret = None
    if ret:
        house = json.loads(ret)
        current_app.logger.info("hit house info redis")
        return jsonify(errno=RET.OK, errmsg="OK", data={"house": house, "user_id": user_id})

    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="Database Error")
    if house:
        house = house.to_full_dict()

        json_house = json.dumps(house)
        try:
            redis_store.setex("house_info_%s" % house_id, constants.HOUSE_DETAIL_REDIS_EXPIRES, json_house)
        except Exception as e:
            current_app.logger.error(e)

        return jsonify(errno=RET.OK, errmsg="OK", data={"house": house, "user_id": user_id})
    else:
        return jsonify(errno=RET.NODATA, errmsg="No Data")
