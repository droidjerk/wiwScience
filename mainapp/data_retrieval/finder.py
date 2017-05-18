from statistics import mean

from fuzzywuzzy import fuzz, process

# import dblp
# import orcid
# import elsapy

from . import dblp

from concurrent.futures.thread import ThreadPoolExecutor

# crtieria dict:
#    firstname, lastname
#   affilation
#   interests
#   publication keyword
#   years range

import datetime

class SchoarlyAccess:
    def __init__(self):
        pass

    def _msearch_name(name):
        name = criteria['firstname'] + ' ' + criteria['lastname']
        authors = scholarly.search_author(name)
        return authors

    def _msearch_keywords(keywords):
        authors = []
        for keyword in keywords:
            partial_list = scholarly.search_pubs_query(keyword.replace(" ", "_"))
            authors += partial_list
        return authors

    def _msearch_pubs(words):
        for pub in scholarly.search_pubs_query(words):
            pass

    def find(criteria):
        name = criteria['firstname'] + ' ' + criteria['lastname']
        authors = scholarly.search_author(name)
        if 'affiliation' in criteria:
            authors = [author for author in authors if
                       fuzz.partial_ratio(author.affiliation,
                                          criteria['affiliation']) >= 50]
            tmp = []
        if 'interests' in criteria:
            for author in authors:
                given_interests = author.interests
                match_array = []
                for interest in criteria['interests']:
                    _, ratio = process.extractOne(interest, given_interests)
                    match_array.append(ratio > 30)
                if all(match_array):
                    tmp.append(author)
            authors = [x.fill() for x in tmp]

        tmp = []
        if 'keywords' in criteria:
            for author in authors:
                is_relevant = False
                for pub in author.publications:
                    title = pub.bib['title']
                    match = mean([fuzz.partial_ratio(title, keyword) for keyword in
                                   criteria['keywords']])
                    if match > 50:
                        is_relevant = True
                        break
                if is_relevant:
                    tmp.append(author)
            authors = tmp
        for author in authors:
            print(author.name, author.affiliation)

# crtieria dict:
#   firstname, lastname
#   affilation
#   interests
#   publication keyword
#   years range
class DBLPAccess:
    def __init__(self):
        pass

    def _msearch_name(self, name):
        return dblp.search_author(name)

    def _msearch_pubs(self, keywords, years, venue):
        print("Searching")
        if keywords == venue == '' and 1970 in years and int(datetime.datetime.now().year) in years:
            print("Skipping")
            return []
        publications = dblp.search_publication(keywords, years, venue)
        author_executor = ThreadPoolExecutor(max_workers=500)
        candidates = []
        for pub in publications:
            try:
                author = pub['authors']['author']
                if isinstance(author, str):
                    candidates.append(author)
                else:
                    candidates.extend(author)
            except:
                pass
        futures = []
        for author in candidates:
            futures.append(author_executor.submit(self._msearch_name, author))
        candidates = []
        [candidates.extend(x.result()) for x in futures]
        return candidates

    def refine_by_pubs(self, authors, keywords, years, venue):
        print("refining")
        if keywords == venue == '' and 1970 in years and int(datetime.datetime.now().year) in years:
            print("Skipping")
            return authors
        new_authors = []
        for author in authors:
            found_keywords = False
            for pub in author.data['publications']:
                venue_check = keyword_check = year_check = True
                pub_type = list(pub.keys())[0]
                if pub_type not in ['inproceedings', 'article']:
                    continue
                if venue is not '':
                    venue_check = fuzz.partial_ratio(pub[pub_type]['venue'], venue) >= 50
                if keywords is not '':
                    keyword_check = fuzz.partial_ratio(pub[pub_type]['title'], keywords) >= 50
                year_check = int(pub[pub_type]['year']) in years
                if venue_check and keyword_check and year_check:
                    new_authors.append(author)
                    break
        return new_authors


    def find(self, criteria):
        """
            DBLP uses as main search lastname firstname and publications.
            affiliation, venue and publication years can narrow down the search
        """
        od = 1970 if criteria['years'][0] == '' else int(criteria['years'][0])
        do = datetime.datetime.now().year if criteria['years'][0] == '' else int(criteria['years'][1])
        authors = []
        if criteria['firstname'] or criteria['lastname']:
            name = (criteria['firstname'] or "") + " " + (criteria['lastname'] or "")
            authors = self._msearch_name(name)
            authors = self.refine_by_pubs(authors, criteria['keywords'],
                                     range(od, do + 1), criteria['venue'])
        if not authors:
            authors = self._msearch_pubs(criteria['keywords'],
                                          range(od, do + 1),
                                          criteria['venue'])
        if authors and criteria['affiliation'] != '':
            authors = [x for x in authors if
                       fuzz.partial_ratio(x.data['affiliation'],
                                          criteria['affiliation']) >= 50]
        result = []
        for author in authors:
            author = dict(author.data)
            author['uid'] = str(hash(author['name']))
            result.append(author)
        return result


class ORCiD:
    def __init__(self):
        pass

    def find_author(criteria):
        pass

    def find_publication(criteria):
        pass


class Elsavier:
    def __init__(self):
        pass

    def find_author(criteria):
        pass

    def find_publication(criteria):
        pass
