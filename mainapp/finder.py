import datetime

from statistics import mean
from concurrent.futures.thread import ThreadPoolExecutor
import collections
from fuzzywuzzy import fuzz, process

import dblp
import orcid

from orcid import Q

# crtieria dict:
#    firstname, lastname
#   affilation
#   interests
#   publication keyword
#   years range


def flatten(x):
    if isinstance(x, (list, set)):
        return [a for i in x for a in flatten(i)]
    else:
        return [x]


def flatten_dict(entry):
    for key in entry:
        entry[key] = flatten(entry[key])
    return entry


def name_fix(name):
    return "".join([x for x in name if x not in [str(i) for i in range(0, 10)]]).strip()


class SchoarlyAccess:
    def __init__(self):
        pass

    def _msearch_name(name):
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
                    match = mean([fuzz.partial_ratio(title, keyword)
                                  for keyword in criteria['keywords']])
                    if match > 50:
                        is_relevant = True
                        break
                if is_relevant:
                    tmp.append(author)
            authors = tmp
        for author in authors:
            print(author.name, author.affiliation)



class DBLPAccess:
    def __init__(self):
        pass

    def _msearch_name(self, name, affiliation):
        return dblp.search_author(name, affiliation)

    def _msearch_pubs(self, keywords, years, venue, affiliation):
        print("Searching")
        if (keywords == venue == '' and 1970 in years and
                int(datetime.datetime.now().year) in years):
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
            futures.append(author_executor.submit(self._msearch_name, author,
                                                  affiliation))
        candidates = []
        [candidates.extend(x.result()) for x in futures]
        return candidates

    def refine_by_pubs(self, authors, keywords, years, venue):
        print("refining")
        if (not keywords and not venue and 1970 in years and
                int(datetime.datetime.now().year) in years):
            print("Skipping")
            return authors
        new_authors = []
        for author in authors:
            venue_check = year_check = keyword_check = False
            for pub in author.data['publications']:
                venue_check = keyword_check = year_check = True
                pub_type = list(pub.keys())[0]
                if pub_type not in ['inproceedings', 'article']:
                    continue
                if venue is not '':
                    venue_check = fuzz.partial_ratio(pub[pub_type]['venue'],
                                                     venue) >= 50
                if keywords is not '':
                    keyword_check = fuzz.partial_ratio(pub[pub_type]['title'],
                                                       keywords) >= 50
                year_check = int(pub[pub_type]['year']) in years
                if venue_check and keyword_check and year_check:
                    new_authors.append(author)
                    break
        return new_authors

    def refine_publication(self, author):
        pubs = author['publications']
        new_pubs = []
        for pub in pubs:
            pub_type = list(pub.keys())[0]
            if pub_type in ['inproceedings', 'article', 'book']:
                pub = pub[pub_type]
                pub['other'] = ''
                if pub_type == 'book':
                    pub['author'] = pub['editor']
                    pub['title'] = pub['booktitle']
                    pub['other'] = "Publisher: " + pub['publisher'] + ", ISBN: " + pub['isbn']
                if 'url' not in pub:
                    pub['url'] = ''
                if 'ee' not in pub:
                    pub['ee'] = ''
                if 'journal' not in pub:
                    pub['journal'] = ''
                if isinstance(pub['author'], str):
                    pub['author'] = [pub['author']]
                new_pub = {
                    'title': pub['title'],
                    'author': pub['author'],
                    'link': pub['ee'],
                    'year': pub['year'],
                    'other': pub['other'],
                    'journal': pub['journal']
                }
                new_pub = flatten_dict(new_pub)
                new_pub['author'] = [name_fix(name) for name in new_pub['author']]
                new_pubs.append(new_pub)
        return new_pubs

    def find(self, criteria):
        """
            DBLP uses as main search lastname firstname and publications.
            affiliation, venue and publication years can narrow down the search
        """
        od = 1970 if criteria['years'][0] == '' else int(criteria['years'][0])
        do = (datetime.datetime.now().year if criteria['years'][0] == '' else
              int(criteria['years'][1]))
        authors = []
        if (criteria['firstname'] or criteria['lastname'] or
                criteria['affiliation']):
            name = (criteria['firstname'] or "") + " " + \
                   (criteria['lastname'] or "")
            authors = self._msearch_name(name, criteria['affiliation'])
            authors = self.refine_by_pubs(authors, criteria['keywords'],
                                          range(od, do + 1), criteria['venue'])
        if not authors:
            authors = self._msearch_pubs(criteria['keywords'],
                                         range(od, do + 1),
                                         criteria['venue'],
                                         criteria['affiliation'])
        result = []
        for author in authors:
            author = dict(author.data)
            author['publications'] = self.refine_publication(author)
            if not isinstance(author['name'], str):
                author['name'] = author['name'][0]
            author['uid'] = str(hash(author['name']))
            flatten_dict(author)
            author['name'] = [name_fix(name) for name in author['name']]
            result.append(author)
        return result


# crtieria dict:
#   firstname, lastname
#   affilation
#   interests
#   publication keyword
#   years range
orcid_map = {
    'firstname': 'given-names',
    'lastname': 'family-name',
    'affiliation': 'affiliation-org-name',
    'interests': 'keywords',
    'keywords': 'work-titles'
}
class ORCiD:

    def process_author(self, author):
        print(author)
        new_entry = {
            'name': author.given_name + " " + author.family_name,
            'affiliation': '',
            'biography': author.biography['value'],
            'interests':  author.keywords,
            'homepages': author.researcher_urls,
            'publications': self.process_publications(author.publications)
        }
        return flatten_dict(new_entry)

    def process_publications(self, pubs):
        publications = []
        for pub in pubs:
            new_pub = {
                'title': pub.title,
                'link': pub.url,
                'year': pub._original_dict['publication-date']['year']['value']
            }
            authors = pub._original_dict['work-contributors']['contributor']
            authors = [x['credit-name']['value'] for x in authors]
            new_pub['author'] = authors
            if 'journal-title' in pub._original_dict:
                new_pub['journal'] = new_pub._original_dict['journal-title']
            publications.append(flatten_dict(new_pub))
        return publications

    def find(self, criteria):
        queries = []
        for keyword in criteria:
            if not criteria[keyword] or keyword not in orcid_map:
                continue
            queries.append(Q(orcid_map[keyword],
                             fuzzy=(criteria[keyword], 0.5)))
        query = queries.pop()
        while queries:
            query = query & queries.pop()
        authors = [self.process_author(x) for x in list(orcid.search(query))]
        return authors



class Elsavier:
    def __init__(self):
        pass

    def find_author(criteria):
        pass

    def find_publication(criteria):
        pass
