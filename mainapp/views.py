import datetime

from math import ceil

import flask

from flask import abort
from werkzeug.contrib.cache import SimpleCache

from .forms import SearchForm
from mainapp import app

cache = SimpleCache()

def url_for_other_page(page):
    args = flask.request.view_args.copy()
    args['page'] = page
    return flask.url_for(flask.request.endpoint, **args)
app.jinja_env.globals['url_for_other_page'] = url_for_other_page



class Pagination(object):

    def __init__(self, page, per_page, total_count):
        self.page = page
        self.per_page = per_page
        self.total_count = total_count

    @property
    def pages(self):
        return int(ceil(self.total_count / float(self.per_page)))

    @property
    def has_prev(self):
        return self.page > 1

    @property
    def has_next(self):
        return self.page < self.pages

    def iter_pages(self, left_edge=2, left_current=2,
                   right_current=5, right_edge=2):
        last = 0
        for num in range(1, self.pages + 1):
            if num <= left_edge or \
               (num > self.page - left_current - 1 and
                num < self.page + right_current) or \
               num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num


@app.route('/', methods=['GET', 'POST'])
@app.route('/search', methods=['GET', 'POST'])
def search_form():
    form = SearchForm()
    years = [(x, x) for x in range(1970, datetime.datetime.now().year + 1)]
    for datefield in [form.do, form.od]:
        datefield.choices = years
        datefield.data = years[-1][0]
    if form.validate_on_submit():
        return flask.redirect(flask.url_for('show_results'))
    return flask.render_template('search.html', form=form)

@app.route('/results/', defaults={'page': 1})
@app.route('/results/page/<int:page>')
def show_results(page):
    # Placeholder content
    content = [
        ['http://i.imgur.com/bPxNnAa.jpg',
         'Donald', 'Knuth', 'Stanford University'],
        ['', 'Pedro', 'Domingos', 'University of Washington'],
        ['http://upload.wikimedia.org/wikipedia/en/9/92/Wojciech_zaremba.png',
         'Wojciech', 'Zaremba', 'University of Warsaw'],
        ['http://upload.wikimedia.org/wikipedia/commons/thumb/b/b9/Markus_Gro'
         'ss_at_Eurographics%272010.jpg',
         'Markus', 'Gross', 'ETH Zurich']
    ]
    if not content and page != 1:
        abort(404)
    pagination = Pagination(page, 3, len(content))
    return flask.render_template('results.html',
                                 pagination=pagination,
                                 content=content)


@app.route('/profile/<id>')
def profile(id):
    # TODO Enable when the search engine will be actually working.
    # if cache.get(id) is None:
    #     abort(404)
    profile = {'Name': "Adam",
               'Surname': "Kowalski",
               'Affilation': "Politechnika Wrocławska",
               'Keywords': "Machine learning",
               'image': "http://www-cs-faculty.stanford.edu/~uno/dek-14May10-2.jpeg"
               }
    publications = [
        ["Mathematical Vanity Plates", "Knuth, D.E.",
            "2011", "Mathematical Intelligencer", "1"],
        ["The art of Programming", "Knuth D.", "2011", "ITNOW", "0"]
    ]
    return flask.render_template('profile.html', profile=profile,
                                 pubs=publications)
