import smtplib
from email.mime.text import MIMEText

from rental_root.tasks.main import celery_app
from rental_root import constants

import os
from dotenv import load_dotenv

load_dotenv()


@celery_app.task
def send_order_email(to, order_id):
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        pwd = os.getenv("GMAIL_SMTP_PASSWORD")
        server.login(constants.SENDER_EMAIL, pwd)

        text = email_template(order_id)
        msg = MIMEText(text, 'html')
        msg['Subject'] = 'Order Confirmation from Rental-rental'
        msg['From'] = constants.SENDER_EMAIL
        msg['To'] = to

        server.sendmail(constants.SENDER_EMAIL, to, msg.as_string())
        return 0
    except Exception as e:
        return -1


def email_template(order_id):
    text = ("Hello! Your order NO.%s is placed! Please see details from <a "
            "href='http://127.0.0.1:5000/orders.html'>MY ORDER</a> page.") % str(order_id)
    return text
