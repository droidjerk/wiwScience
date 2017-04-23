import flask
from mainapp import app

@app.route('/')
def search_form():
    return flask.render_template('search.html')
