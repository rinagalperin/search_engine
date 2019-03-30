import math
import ujson


class Ranker:

    def __init__(self, output_path):
        """initiates the docs dictionary and average length using the class methods
                                """
        self.output_path = output_path
        self.docs = self.init_docs()
        self.avg_doc_length = self.get_avg_doc_length()

    def init_docs(self):
        """initiates the docs dictionary
                                """
        dict_doc = {}
        file_name = self.output_path + '/output/docs.txt'

        with open(file_name, 'r') as docs:
            for doc in docs.readlines():
                doc_json = ujson.loads(doc)
                dict_doc[doc_json['name']] = doc_json

        return dict_doc

    def rank(self, terms, appearances, docs_to_rank):
        """sends each doc to be ranked
           """
        bm25_ranks = {}
        for doc_num in docs_to_rank:
            bm25_ranks[doc_num] = self.get_bm25_score(terms, appearances, doc_num)

        return bm25_ranks

    def get_bm25_score(self, terms, appearances, doc_num):
        """calculates the score of the doc based on 2 parameters.
        the first one (corresponding to weight 1: w1) is the bm25
        rank. the second one (corresponding to weight 2: w2) is the
        number of query terms that appear in the doc's title
                                        """
        w1 = 0.9
        w2 = 0.1

        k = 1.7
        b = 0.5
        doc_length = self.get_doc_length(doc_num)
        ans = 0
        in_title = 0

        for term in terms:
            if doc_num in appearances[term].keys():
                if 'title' in self.docs[doc_num].keys() and term.lower() in self.docs[doc_num]['title'].lower():
                    in_title += 1
                f = appearances[term][doc_num]
            else:
                f = 0

            ans += self.get_term_idf(term, appearances) * \
                   ((f * (k + 1))/(f + k * (1 - b + (b * (doc_length / self.avg_doc_length)))))

        return (w1 * ans) + (w2 * (in_title / len(terms)) * 4)

    def get_term_idf(self, term, appearances):
        """calculated the term's IDF for the bm25 calculation
                   """
        N = len(self.docs)
        nq = int(len(appearances[term]))
        calculation = (N - nq + 0.5)/(nq + 0.5)
        return math.log(calculation)

    def get_avg_doc_length(self):
        """returns average doc length using the dictionary
                   """
        total_length = 0

        for doc in self.docs.keys():
            total_length += self.get_doc_length(doc)

        return int(total_length / len(self.docs))

    def get_doc_length(self, doc_num):
        """calculated a specific doc's rank
                   """
        return self.docs[doc_num]['length']
