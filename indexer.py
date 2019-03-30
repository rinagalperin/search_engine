import ujson
import os
import numpy as np
import urllib.request

from parse import extract_parsed_number
from classifier import is_alpha


def extract_city_metadata(city_name):
    """gets a city name and retrieves all it's metadata using the provided API.
                    """
    capital_metadata = {}

    try:
        city_info = urllib.request.urlopen(
            'http://restcountries.eu/rest/v2/capital/' + city_name + '?fields=name;population;currencies').read()
        # 'http://getcitydetails.geobytes.com/GetCityDetails?fqcn=' + city_name).read()

        if city_info:
            city_info = ujson.loads(city_info)[0]
            currency = city_info['currencies'][0]['code']
            country = city_info['name']
            population = extract_parsed_number(city_info['population'])
            # currency = city_info['geobytescurrencycode']
            # country = city_info['geobytescountry']
            # population = extract_parsed_number(city_info['geobytespopulation'])

            capital_metadata = {
                'currency': currency,
                'country': country,
                'population': population
            }
    except:
        pass

    return {
        'name': city_name.upper(),
        'metadata': capital_metadata
    }


class Indexer:
    def __init__(self):
        self.minis = dict()

    def get_term_key(self, term):
        """handles the lower-case/upper-case law and saves the given term in its valid form
                        """
        term_lower = term.lower()
        if term_lower in self.minis.get(term[0].upper(), []):
            return term_lower

        if term[0].upper() == term[0]:
            return term.upper()
        else:
            term_upper = term.upper()
            if term_upper in self.minis.get(term[0].upper(), []):
                self.minis[term[0].upper()][term_lower] = self.minis[term[0].upper()].pop(term_upper)
            return term_lower

    def add_to_dict(self, parser_results, doc_dict, doc_file, file, city_minis):
        """
            Updates both the doc index and the inverted index for
            the terms according to the given doc and its parsing results
        """
        doc_name = doc_dict['name']
        unique_term, count_term = np.unique(parser_results, return_counts=True)

        # update doc index with the doc's information
        doc_metadata = {"name": doc_name,
                        "max_appearances": int(max(count_term)),
                        "num_of_unique_terms": len(unique_term),
                        "length": doc_dict['length'],
                        "path": file}
        # if there is information regarding the doc's city/date/language/title - then add it to its metadata
        if doc_dict['city'] != "":
            doc_metadata['city'] = doc_dict['city']
        if doc_dict['date'] != "":
            doc_metadata['date'] = doc_dict['date']
        if doc_dict['language'] != "":
            doc_metadata['language'] = doc_dict['language']
        if doc_dict['title'] != "":
            doc_metadata['title'] = doc_dict['title']

        doc_file.write(ujson.dumps(doc_metadata)+'\n')

        # update mini inverted index with this doc's term appearances information
        i = 0
        for term, term_appearances in zip(unique_term, count_term):
            if is_alpha(term):
                term = self.get_term_key(term)
                city = term.upper()
                if city == doc_metadata.get('city', False):
                    if city not in city_minis:
                        city_minis[city] = extract_city_metadata(city)
                    city_minis[city][doc_name] = [i for i,t in enumerate(parser_results) if t.upper() == city]

            liter_type = term[0].upper()
            if liter_type not in self.minis:
                self.minis[liter_type] = {}

            self.minis[liter_type][term] = self.minis[liter_type].get(term, []) + [[doc_name, int(term_appearances)]]
            i += 1

    def save(self, file, output_path):
        """
        Saves the mini inverted index to a file after sorting the terms alphabetically
        """
        for key, val in self.minis.items():
            name_file = os.path.join(output_path + "/output/mini", key)
            if not os.path.exists(name_file):
                os.makedirs(name_file)

            with open(os.path.join(name_file, os.path.basename(file) + ".txt"), 'w') as outfile:
                # sort the terms
                val = sorted(val, key=str.lower)

                # add an entry in the file for the given term
                for term in val:
                    outfile.write(ujson.dumps({'name': term, 'appearances': self.minis[key][term]}) + '\n')
