import datetime

from math import ceil

import flask

from flask import abort, session
from werkzeug.contrib.cache import MemcachedCache
import string
from .forms import SearchForm
from .data_retrieval import finder
from mainapp import app

cache = MemcachedCache(['127.0.0.1:11211'])


def url_for_other_page(page):
    args = flask.request.view_args.copy()
    args['page'] = page
    return flask.url_for(flask.request.endpoint, **args)


app.jinja_env.globals['url_for_other_page'] = url_for_other_page


class Pagination(object):
    """
        A class for handling pagination in the results template.
        Code borrowed from http://flask.pocoo.org/snippets/44/
    """
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

    # Filling choice fields in SearchForm
    years = [(str(x), str(x)) for x in
             range(1970, datetime.datetime.now().year + 1)] + [("", "")]
    for datefield in [form.do, form.od]:
        datefield.choices = years
        datefield.data = years[-1][0]

    if flask.request.method == 'POST':
        find = finder.DBLPAccess()
        arguments = {
            'firstname': flask.request.form['imie'],
            'lastname': flask.request.form['nazwisko'],
            'interests': flask.request.form['keywords'],
            'keywords': flask.request.form['publikacja'],
            'venue': '',
            'affiliation': flask.request.form['afilacja'],
            'years': (flask.request.form['od'], flask.request.form['do'])
        }
        results = find.find(arguments)
        # key identifies a search query; it is held in a cookie and used
        # in show_results to present entries for the given query
        key = str(hash(frozenset(arguments.items())))
        session['latest-search'] = key
        # Each found author profile is held in cache for an hour;
        # a uid identifies the author, and a list of author uids is bound to
        # the query key
        query_pointers = []
        for author in results:
            cache.add(author['uid'], author, timeout=60 * 60)
            query_pointers.append(author['uid'])
        cache.add(key, query_pointers, timeout=60 * 60)
        return flask.redirect(flask.url_for('show_results'))
    return flask.render_template('search.html', form=form)


@app.route('/results/', defaults={'page': 1})
@app.route('/results/page/<int:page>')
def show_results(page):
    # If latest-search is not present in the cookie, a search query has to be
    # ran first. The search also has to be ran again in case the cache has
    # deleted the key-pointers pair due to a timeout.
    if ('latest-search' not in session or
            cache.get(session['latest-search']) is None):
        flask.flash("Your search query has expired!")
        return flask.redirect('/')
    key = session['latest-search']
    entries = [cache.get(x) for x in cache.get(key)]
    content = []
    for author in entries:
        # TODO
        # In case an author times out in the cache while being
        # retrived an error should show. Currently it's failing silently.
        if author is None:
            continue
        name, surname = author['name'].split(" ")[0], author['name'].split(" ")[1]
        content.append([flask.url_for('static', filename='default.png'),
                        name, surname,
                        author['affiliation'],
                        author['uid']])
    if not content and page != 1:
        abort(404)
    # Pagination is 3 for testing.
    pagination = Pagination(page, 3, len(content))
    return flask.render_template('results.html',
                                 pagination=pagination,
                                 content=content)


def process_profile(profile, pubs):
    def process_author(author):
        if isinstance(author, str):
            author = ''.join([char for char in author
                              if char not in string.digits])
            return author
        new_author = []
        for person in author:
            person = process_author(person)
            new_author.append(person)
        return ", ".join(new_author)

    def process_homepages(page):
        if isinstance(page, str):
            page = flask.Markup('<a href="' + profile[keyword]
                                + '">Homepage<a>')
            return page
        new_page = '<li` class="nav nav-tabs span2">'
        for adress in page:
            new_page += '<li><a href="' + adress + '">Homepage</a></li>'
        new_page += '</li>'
        return flask.Markup(new_page)
    submap = {
        'name': "Name",
        'affiliation': "Institution",
        'homepages': "Homepage"
    }
    nprofile = {}
    for keyword in profile:
        if keyword not in submap:
            continue
        if keyword == 'name':
            profile[keyword] = process_author(profile['name'])
        if keyword == 'homepages':
            profile[keyword] = process_homepages(profile[keyword])
        nprofile[submap[keyword]] = profile[keyword]
    npubs = []
    for pub in pubs:
        key = list(pub.keys())[0]
        pub = pub[key]
        npubs.append([process_author(pub.get('author') or pub['editor']),
                      pub['title'], pub['year']])
    return nprofile, npubs


@app.route('/profile/<id>')
def profile(id):
    content = cache.get(id)
    if content is None:
        flask.flash("Profile is not cached on server")
        return flask.redirect('/')
    profile = content
    publications = profile['publications']

    profile, publications = process_profile(profile, publications)

    return flask.render_template('profile.html', profile=profile,
                                 pubs=publications)
