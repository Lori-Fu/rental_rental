from rental_root import create_app

from rental_root import db
app = create_app("develop")


if __name__ == '__main__':
    app.run(host="0.0.0.0")
