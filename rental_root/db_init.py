from flask import current_app, Blueprint
from rental_root import redis_store, db
from rental_root.model import Area, Facility

import os
from dotenv import load_dotenv

load_dotenv()

db_init = Blueprint("db", __name__)


@db_init.route("/db_init/<uuid>")
def init(uuid):
    if uuid == os.getenv("DB_INIT_UUID"):
        try:
            init = redis_store.get("db_init_%s" % uuid)
            if init is None:
                areas = [Area(id=1, name="Midtown"), Area(id=2, name="Upper East Side"),
                         Area(id=3, name="Upper West Side"),
                         Area(id=4, name="Lower Manhattan"), Area(id=5, name="Greenwich Village"),
                         Area(id=6, name="Soho"),
                         Area(id=7, name="East Village"), Area(id=8, name="Harlem"),
                         Area(id=9, name="Financial District"),
                         Area(id=10, name="Chelsea")]
                facilities = [Facility(id=1, name="Wifi"), Facility(id=2, name="Air conditioning"),
                              Facility(id=3, name="Heating"),
                              Facility(id=4, name="Towels and toilet paper"), Facility(id=5, name="Bathtub/Shower"),
                              Facility(id=6, name="Hair dryer"), Facility(id=7, name="TV"),
                              Facility(id=8, name="Washer"),
                              Facility(id=9, name="Dryer"), Facility(id=10, name="Extra pillows&blankets"),
                              Facility(id=11, name="Iron"),
                              Facility(id=12, name="Cable Network"), Facility(id=13, name="Kitchen"),
                              Facility(id=14, name="Coffee maker"),
                              Facility(id=15, name="Dishwasher"), Facility(id=16, name="Parking"),
                              Facility(id=17, name="Private outdoor area"),
                              Facility(id=18, name="Private pool"), Facility(id=19, name="Security cameras"),
                              Facility(id=20, name="Smart lock"),
                              Facility(id=21, name="Self check-in"), Facility(id=22, name="Pets allowed")]
                db.session.add_all(areas)
                db.session.add_all(facilities)
                db.session.commit()
                return "success"
        except Exception as e:
            current_app.logger.error(e)
            return "fail"
