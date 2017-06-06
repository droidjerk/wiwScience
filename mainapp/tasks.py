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
    results = _consolidate(results)
    # Each found author profile is held in cache for an hour;
    # a uid identifies the author, and a list of author uids is bound to
    # the query key
    query_pointers = []
    for author in results:
        cache.add(author['uid'], author, timeout=60 * 60)
        query_pointers.append(author['uid'])
    cache.add(key, query_pointers, timeout=60 * 60)
    return {'status': "Success!"}


def _consolidate(entries):
    complete = entries.pop(0)
    while entries:
        entry = entries.pop(0)
        while entry:
            person = entry.pop()
            join(complete, person)
    return complete


def join(full_list, new_entry):
    attributes = ['name', 'affiliation']
    scores = []
    for entry in full_list:
        scores.append(mean([fuzz.partial_ratio(entry[x], new_entry[x])
                            for x in attributes]))
    print(max(scores))
    if max(scores) < 60:
        full_list.append(new_entry)
        return full_list
    main = full_list[scores.index(max(scores))]
    attributes.extend(['biography', 'interests', 'homepages'])
    for attribute in attributes:
        if attribute not in main:
            main[attribute] = ['']
        if attribute not in new_entry:
            new_entry[attribute] = ['']
        main[attribute] = list_join(main[attribute], new_entry[attribute])
    main['publications'] = list_join(main['publications'], new_entry['publications'], key=lambda x:x['title'])


def list_similarity(list1, list2, key=lambda x: x):
    all_scores = []
    for element in list1:
        all_scores.append(max([fuzz.partial_ratio(key(element), key(element2))
                               for element2 in list2]))
    return mean(all_scores)

def list_join(list1, list2, key=lambda x: x):
    if list1 == [''] or list2 == ['']:
        list1.extend(list2)
        return list1
    in_list = [0 for x in list2]
    for element in list1:
        scores = [fuzz.partial_ratio(key(element), key(element2))
                  for element2 in list2]
        for index, score in enumerate(scores):
            if score > 90:
                in_list[index] = 1
    for index, mask in enumerate(in_list):
        if mask == 0:
            list1.append(list2[index])
    return list1


