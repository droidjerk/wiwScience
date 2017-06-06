import celery
from .data_retrieval import finder
from flask import session
from mainapp import cache
from concurrent.futures.thread import ThreadPoolExecutor
from fuzzywuzzy import fuzz
from statistics import mean

CUTOFF = 10

@celery.task(bind=True)
def aggregate(self, arguments):
    executor = ThreadPoolExecutor(max_workers=5)
    engines = [finder.DBLPAccess(), finder.ORCiD()]
    futures = [executor.submit(engine.find, arguments) for engine in engines]
    self.update_state(state='PROGRESS',
                      meta={'status': "Started the lookup"})

    results = [future.result() for future in futures]
    self.update_state(state='PROGRESS',
                      meta={'status': "Aggregating the data"})
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


def _consolidate(entires):
    complete = entires.pop(0)
    while entries:
        entry = entries.pop()
        index = _find_match(entry, complete)
        if index < 0:
            continue
        join(complete[i], entry)


def join(main, new):
    if fuzz.partial_ratio(main['affiliation'], new['affiliation']) < 90:
        main['affiliation'].append(new['affiliation'])
    new_pubs = []
    for npub in new['publications']:
        for mpub in main['publications']:
            if (fuzz.partial_ratio(npub['title'], mpub['title']) < 90 and
                    str(mpub['year']) != str(npub['year'])):
                new_pubs.append(npub)

            if mpub['link'] == npub['link']:
                continue
            if isinstance(mpub['link'], str):
                mpub['link'] = [mpub['link']]
            if isinstance(npub['link'], str):
                mpub['link'].append(npub['link'])
            else:
                mpub['link'].extend(mpub['link'])






def _find_match(person, entries):
    def compare(person1, person2):
        attribs = ['name', 'affilation']
        return mean([fuzz.partial_ratio(person1[x], person2[x]) for x in attribs])
    scores = [compare(person, candidate) for candidate in entries]
    if max(scores) < CUTOFF:
        return -1
    return scores.index(max(scores))





