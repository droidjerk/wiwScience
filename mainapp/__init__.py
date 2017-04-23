from flask import Flask
from flask_bootstrap import Bootstrap
import flask

app = Flask(__name__)
Bootstrap(app)


if __name__ == '__main__':
    app.run()


from mainapp import views, models
