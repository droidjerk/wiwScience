from . import finder
from concurrent.futures.thread import ThreadPoolExecutor
from fuzzywuzzy import fuzz
from statistics import mean

CUTOFF = 10


def flatten(x):
    if isinstance(x, (list, set)):
        return [a for i in x for a in flatten(i)]
    else:
        return [x]


def aggregate(arguments):
    executor = ThreadPoolExecutor(max_workers=5)
    engines = [finder.DBLPAccess(), finder.ORCiD(), finder.ScholarlyAccess()]
    futures = [executor.submit(engine.find, arguments) for engine in engines]

    results = [future.result() for future in futures]
    # key identifies a search query; it is held in a cookie and used
    # in show_results to present entries for the given query
    results = _consolidate(results)
    # Each found author profile is held in cache for an hour;
    # a uid identifies the author, and a list of author uids is bound to
    # the query key
    return results


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
        matches = [fuzz.partial_ratio(entry['affiliation'], new_entry['affiliation']) for x in attributes]
        matches.append(100 if entry['name'] == new_entry['name'] else 0)
        if entry['name'] != new_entry['name']:
            scores.append(0)
        else:
            scores.append(mean(matches))
    if max(scores) < 50:
        full_list.append(new_entry)
        return full_list
    main = full_list[scores.index(max(scores))]
    attributes.extend(['biography', 'interests', 'homepages'])
    for attribute in set(list(new_entry) + attributes):
        if attribute not in main:
            main[attribute] = []
        if attribute not in new_entry:
            new_entry[attribute] = []
        main[attribute] = list_join(main[attribute], new_entry[attribute])
    main['publications'] = list_join(main['publications'],
                                     new_entry['publications'],
                                     key=lambda x: x['title'])


def indentity(x):
    return x


def list_similarity(list1, list2, key=indentity):
    all_scores = []
    for element in list1:
        all_scores.append(max([fuzz.partial_ratio(key(element), key(element2))
                               for element2 in list2]))
    return mean(all_scores)


def list_join(list1, list2, key=indentity):
    # list2 to list1
    mapping = {}
    if list1 == [''] or list2 == [''] or list1 == [] or list2 == []:
        list1.extend(list2)
        return list1
    in_list = [0 for x in list2]
    for i, element in enumerate(list1):
        scores = [fuzz.partial_ratio(key(element), key(element2))
                  for element2 in list2]
        for index, score in enumerate(scores):
            if score > 90:
                in_list[index] = 1
                mapping[index] = i
    for index, mask in enumerate(in_list):
        if mask == 0:
            list1.append(list2[index])
    return list1