import re

import gensim
import json
import linecache
from copy import deepcopy
import warnings
import numpy as np
from bs4 import BeautifulSoup

from classifier import is_alpha

warnings.filterwarnings(action='ignore', category=UserWarning, module='gensim')


class Searcher:
    """the searcher receives the inverted index we saved to memory and
    the output path where the posting files are located.
    the search method receives the query and does the following:
    1. for each term in the query - retrieves the appearances in docs
    2. for each doc in all the appearances from step 1 - calculate the doc's rank
    3. sort by rank
    4. return first 50 docs
                    """

    def __init__(self, inverted_index, output_path, ranker, corpus_path):
        self.inverted_index = inverted_index
        self.output_path = output_path
        self.ranker = ranker

        with open(corpus_path + "/stop_words.txt", 'r') as outfile:
            self.stop_words = outfile.read().split('\n')

            # create a Hash Map of the stop words for a faster check
        self.stop_words = dict(zip(self.stop_words, self.stop_words))

    # TODO: remove print function and 'query_num' parameter
    def search(self, query, query_num, is_semantic, is_entities, chosen_cities=[]):
        docs_to_rank = set()
        terms = self.filter_stop_words(query.split(' '))

        terms_appearances = self.get_appearances(terms, is_semantic, is_entities)

        for docs in terms_appearances.values():
            docs_to_rank = docs_to_rank | set(docs.keys())

            # filter docs to only include docs that contain a chosen city
            if not len(chosen_cities) == 0:
                docs_to_rank = self.filter_docs_by_cities(docs_to_rank, chosen_cities)

        all_ranks = self.ranker.rank(terms, terms_appearances, docs_to_rank)
        fifty_ranks = sorted(all_ranks.items(), key=lambda x: x[1], reverse=True)[:50]

        result_entities = {}
        if is_entities:
            for doc in [x[0] for x in fifty_ranks]:
                result_entities[doc] = self.get_entities_from_doc(doc)

        linecache.clearcache()
        #self.print_results(fifty_ranks, query_num)
        return fifty_ranks, result_entities

    def get_entities_from_doc(self, doc_name):
        path = self.ranker.docs[doc_name]['path']
        ans = []
        with open(path) as FileObj:
            text = FileObj.read()
            soup = BeautifulSoup(text, "html.parser")

            # gather doc information for the metadata
            for doc in soup.find_all('doc'):
                name = doc.find_all('docno')[0].text.strip()

                if name != doc_name or len(doc.find_all('text')) == 0:
                    continue
                doc_text = doc.find_all('text')[0].text
                for word in re.split('[\s+\n+\"\'\:\[\]\)\(\;\:\{\}\!\?]', doc_text):
                    if not word == '' and word[0].upper() == word[0] and\
                            is_alpha(word) and word.lower() not in self.stop_words:
                        ans += [word.upper()]

                break

        unique, count = np.unique(np.array(ans), return_counts=True)
        for word in re.split('[\s+\n+\"\'\:\[\]\)\(\;\:\{\}\!\?]', doc_text):
            if not word == '' and word[0] == word[0].lower() and word.upper() in unique:
                idx = unique == word.upper()
                unique = unique[np.bitwise_not(idx)]
                count = count[np.bitwise_not(idx)]

        sort_unique = sorted(zip(unique, count), key=lambda x: x[1], reverse=True)
        return sort_unique[:5]

    def get_appearances(self, terms, is_semantic, is_entities):
        """calculates the terms' appearances in the docs.
        we take the terms from the query and find other terms that include them,
        giving a higher score (weight) to terms that are closer in length to the original term.
        for example:
            original term - 'dog'
            similar term - 'dog' --> will get the max score since both are identical
            similar term - 'dogs' --> will get a high score
            similar term - 'dogmatic' --> will get a much smaller score
        in this function we also utilize the fact that we're going over the entire dictionary
        to collect all the entities (capital letter terms) into a separate list.
                            """
        ans = {}
        # entities = []
        semantic_to_check = []

        for key in self.inverted_index.keys():
            # if is_entities and key.encode('ascii').isalpha() and key == key.upper():
            #     entities.append(key)
            for term in terms:
                ans[term] = ans.get(term, {})
                if term.lower() in key.lower():
                    semantic_to_check.append(key.lower())
                    appearances_to_add = self.get_term_appearances(key)
                    ans[term] = self.update_term_appearances(ans[term], appearances_to_add, 15 * len(term) / len(key))

        if is_semantic:
            model = self.get_word_to_vec_model()
            for term in semantic_to_check:
                try:
                    result = model.most_similar(positive=[term.replace('-',' ')], topn=3)
                    for res in ([x[0] for x in result]):
                        for r in res.split('_'):
                            appearances_to_add = self.get_term_appearances(r)
                            ans[term] = self.update_term_appearances(ans[term], appearances_to_add, 1)
                except KeyError:
                    #print('no such word: ' + term)
                    pass

        return ans #, entities

    def find_term_ptr(self, term):
        """given a term, finds the corresponding entry in the inverted index
        and retrieves its 'ptr' value - the row number in the term's posting file.
        the function also returns the term in its correct casing as it appears in the
        dictionary.
                        """
        if term.lower() in self.inverted_index.keys():
            return term.lower(), self.inverted_index[term.lower()]['ptr']
        elif term.upper() in self.inverted_index.keys():
            return term.upper(), self.inverted_index[term.upper()]['ptr']
        return term, -1

    def get_dictionary_entry(self, term, ptr):
        """given a term and its posting pointer (row number),
        finds the posting file using the term's first character
        and retrieves the correct entry containing the term's metadata.
                                    """
        first_char = term[0].upper()
        file_name = self.output_path + '/output/inverted_index/' + first_char + '.txt'
        line = ''
        while line == '':
            line = linecache.getline(file_name, int(ptr) + 1)
            break

        return json.loads(line)

    def get_term_appearances(self, term):
        """retrieves only the given term's appearances in the docs.
                                    """
        appearances_to_add = {}
        correct_term_case, ptr = self.find_term_ptr(term)
        if ptr != -1:
            term_entry = self.get_dictionary_entry(correct_term_case, ptr)

            for entry in term_entry['appearances']:
                doc_number = entry[0]
                num_of_appearances = entry[1]
                appearances_to_add[doc_number] = num_of_appearances

        return appearances_to_add

    def update_term_appearances(self, current_appearances, appearances_to_add, r):
        """merges the term appearances
                                    """
        for doc, appearances in appearances_to_add.items():
            current_appearances[doc] = current_appearances.get(doc, 0) + r * appearances

        return current_appearances

    def get_entities(self, docs_to_rank, entities):
        """return a Hash Map from a doc's number to its top 5 entities
        as defined in the capital/lower letters clause in the instructions
                                            """
        ans = {}

        for doc in docs_to_rank:
            ans[doc] = {}
            for entity in entities:
                correct_term_case, ptr = self.find_term_ptr(entity)
                if ptr != -1:
                    term_entry = self.get_dictionary_entry(correct_term_case, ptr)
                    for entry in term_entry['appearances']:
                        doc_number = entry[0]
                        num_of_appearances = entry[1]
                        if doc_number == doc:
                            ans[doc][entity] = num_of_appearances
            ans[doc] = sorted(ans[doc].items(), key=lambda kv: kv[1], reverse=True)[:5]

        return ans

    def get_word_to_vec_model(self):
        """returns google's pre-trained Word2Vec model.
                                            """
        return gensim.models.KeyedVectors.load_word2vec_format(
            'model.bin',
            #'https://s3.amazonaws.com/dl4j-distribution/GoogleNews-vectors-negative300.bin.gz',
            binary=True, limit=32000)

    # @staticmethod
    # def print_results(result_ranks, query_num):
    #     dcs = []
    #     for pair in result_ranks:
    #         dcs.append(pair[0])
    #
    #     total = 0
    #     count = 0
    #     with open('D:\\documents\\users\\rinag\\Downloads\\qrels.txt', 'r') as results:
    #         for result in results.readlines():
    #             s = result.split(' ')
    #             if s[0] == query_num:
    #                 total += 1
    #                 if s[2] in dcs:
    #                     count += 1
    #
    #     if total != 0:
    #         #print((count / total) * 100)
    #         print(query_num, count)

    def is_doc_legit_city(self, doc, chosen_cities):
        """return True if a certain doc has a legit city (a city from the list
        that the user has chosen) in its 104 tag
                                            """
        return 'city' in self.ranker.docs[doc] and self.ranker.docs[doc]['city'] in chosen_cities

    def filter_docs_by_cities(self, docs_to_rank, chosen_cities):
        """filteres docs to only contain those that have a city that
        was chosen by the user in their 104 tag
                                    """
        filtered_doc_to_rank = []
        for doc in docs_to_rank:
            if self.is_doc_legit_city(doc, chosen_cities):
                filtered_doc_to_rank.append(doc)
        return filtered_doc_to_rank

    def filter_stop_words(self, terms):
        filtered_terms = []

        for term in terms:
            if not term.lower() in self.stop_words:
                filtered_terms.append(term)

        return filtered_terms
