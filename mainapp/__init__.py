from flask import Flask
from flask_bootstrap import Bootstrap
import flask
import config

app = Flask(__name__)
Bootstrap(app)

app.secret_key = config.SECRET
app.config['SECRET_KEY'] = config.SECRET

if __name__ == '__main__':
    app.run()


from mainapp import views
