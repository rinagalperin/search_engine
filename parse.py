import locale
import re
import snowballstemmer
import numpy as np
from enum import Enum
from classifier import \
    is_alpha, \
    is_fraction, \
    is_number_with_commas, \
    extract_number, \
    extract_parsed_number, \
    compare_type, \
    extract_int, \
    extract_number_with_commas


# the possible types a term can be classified as
class TERM_TYPE(Enum):
    MONTH = 1
    WORD_NUMBER = 2
    WORD = 3
    FRACTION = 4
    NUMBER = 5
    BETWEEN = 6
    AND = 7
    PERCENT = 8
    DOLLARS = 9
    US = 10
    HYPHEN = 11
    DOLLAR_NUMBER = 12
    DOLLAR_NUMBER_COMMA = 13
    NONE = 14


class Parser:
    def __init__(self, stem, corpus_path):
        self.stem = stem
        self.stemmer = snowballstemmer.stemmer('english')
        self.months = dict()
        self.word_numbers = dict()
        self.init_months()
        self.init_word_numbers()
        self.alpha = {
            "between": TERM_TYPE.BETWEEN,
            'and': TERM_TYPE.AND,
            'percent': TERM_TYPE.PERCENT,
            'percentage': TERM_TYPE.PERCENT,
            'dollars': TERM_TYPE.DOLLARS,
            'u.s.': TERM_TYPE.US}
        locale.setlocale(locale.LC_ALL, 'en_US')

        with open(corpus_path + "/stop_words.txt", 'r') as outfile:
            self.stop_words = outfile.read().split('\n')

        # create a Hash Map of the stop words for a faster check
        self.stop_words = dict(zip(self.stop_words, self.stop_words))

        # handle the removing of terms that are part of the parsing rules
        for word in self.alpha:
            if word in self.stop_words:
                self.stop_words.pop(word)
        for word in self.months.keys():
            if word in self.stop_words:
                self.stop_words.pop(word)
        for word in self.word_numbers.keys():
            if word in self.stop_words:
                self.stop_words.pop(word)

    def parse(self, doc):
        parse_results = []
        text = doc['text']

        # separate the terms in the document by white spaces
        terms = re.split('[\s+\n+\"\'\:\[\]\)\(\;\:\{\}\!\?]', text)

        ##############################################################################
        #   STEP 1: Classify each term                                               #
        ##############################################################################
        classifications = self.classify_terms(terms)

        ##############################################################################
        #   STEP 2: Parse numbers with all the connecting terms that follow the      #
        #   current term, creating the final 'Number' unit                           #
        ##############################################################################
        i = 0
        while i < len(classifications):
            classification, term = classifications[i]

            # NUMBER
            if compare_type(i, classifications, TERM_TYPE.NUMBER):
                new_num = term

                # Number + WordNumber
                if compare_type(i + 1, classifications, TERM_TYPE.WORD_NUMBER):
                    word = classifications[i + 1][1]
                    new_num = term * self.word_numbers[word]
                    del classifications[i + 1]

                    classifications[i][1] = extract_parsed_number(new_num)

                # Number + Fraction
                elif compare_type(i + 1, classifications, TERM_TYPE.FRACTION):
                    fraction = classifications[i + 1][1]
                    classifications[i][1] = str(extract_parsed_number(new_num)) + ' ' + str(fraction)
                    del classifications[i + 1]

                # Number
                else:
                    classifications[i][1] = str(extract_parsed_number(term))

            # FRACTION
            elif compare_type(i, classifications, TERM_TYPE.FRACTION):
                classifications[i][0] = TERM_TYPE.NUMBER

            # DOLLAR_NUMBER
            elif compare_type(i, classifications, TERM_TYPE.DOLLAR_NUMBER):
                # $Number + WordNumber
                if compare_type(i + 1, classifications, TERM_TYPE.WORD_NUMBER):
                    word = classifications[i + 1][1]
                    new_num = extract_number(term) * self.word_numbers[word]

                    classifications[i][0] = TERM_TYPE.NUMBER
                    classifications[i][1] = extract_parsed_number(new_num)
                    classifications[i + 1][0] = TERM_TYPE.DOLLARS
                    classifications[i + 1][1] = 'dollars'

                else:
                    new_num = extract_number(term)
                    classifications[i][0] = TERM_TYPE.NUMBER
                    classifications[i][1] = extract_parsed_number(new_num)

                    classifications.insert(i + 1, [TERM_TYPE.DOLLARS, 'dollars'])

            # DOLLAR_NUMBER_COMMA
            elif compare_type(i, classifications, TERM_TYPE.DOLLAR_NUMBER_COMMA):
                # $Number (with commas) + WordNumber
                if compare_type(i + 1, classifications, TERM_TYPE.WORD_NUMBER):
                    word = classifications[i + 1][1]
                    new_num = extract_number(term) * self.word_numbers[word]
                    new_num_with_commas = extract_number_with_commas(new_num)

                    classifications[i][0] = TERM_TYPE.DOLLAR_NUMBER_COMMA
                    classifications[i][1] = new_num_with_commas
                    classifications[i + 1][0] = TERM_TYPE.DOLLARS
                    classifications[i + 1][1] = 'dollars'

                else:
                    new_num_with_commas = extract_number_with_commas(term)

                    classifications[i][0] = TERM_TYPE.DOLLAR_NUMBER_COMMA
                    classifications[i][1] = new_num_with_commas

                    classifications.insert(i + 1, [TERM_TYPE.DOLLARS, 'dollars'])

            i += 1

        ##############################################################################
        #   STEP 3: Combine the type units according to the patterns in the rules    #
        ##############################################################################
        i = 0
        while i < len(classifications):
            classification, term = classifications[i]

            if classification is TERM_TYPE.NONE:
                pass
            # WORD
            elif classification is TERM_TYPE.WORD:
                # Word + '-' + Number
                # Word + '-' + Word
                if compare_type(i + 1, classifications, TERM_TYPE.HYPHEN) and \
                        (compare_type(i + 2, classifications, TERM_TYPE.NUMBER) or
                         compare_type(i + 2, classifications, TERM_TYPE.WORD)):
                    # Word + '-' + Word + '-' + Word
                    if compare_type(i + 3, classifications, TERM_TYPE.HYPHEN) and \
                            compare_type(i + 4, classifications, TERM_TYPE.WORD):
                        parse_results.append((term + '-' + classifications[i + 2][1] + '-' + classifications[i + 4][1]).lower())
                        del classifications[i + 1]
                        del classifications[i + 1]
                        del classifications[i + 1]
                        del classifications[i + 1]
                    else:
                        parse_results.append((term + '-' + classifications[i + 2][1]).lower())
                        del classifications[i + 1]
                        del classifications[i + 1]

                # plain word
                elif self.stem and term[0].upper() == term[0]:
                    parse_results.append(self.stemmer.stemWord(term))
                else:
                    parse_results.append(term)

            # WORD_NUMBER
            elif classification is TERM_TYPE.WORD_NUMBER:
                parse_results.append(term)

            # MONTH
            elif classification is TERM_TYPE.MONTH:
                if compare_type(i + 1, classifications, TERM_TYPE.NUMBER):
                    num = extract_int(classifications[i + 1][1])

                    if num:
                        # month and day
                        if 1 <= num <= 31:
                            parse_results.append(self.months[term] + '-' + str("%02d" % (num,)))
                            del classifications[i + 1]
                        # month and year
                        elif num > 0:
                            parse_results.append(str("%04d" % (num,)) + '-' + self.months[term])
                            del classifications[i + 1]
                else:
                    parse_results.append(term)

            # BETWEEN
            elif classification is TERM_TYPE.BETWEEN:
                if compare_type(i + 1, classifications, TERM_TYPE.NUMBER) and \
                        compare_type(i + 2, classifications, TERM_TYPE.AND) and \
                        compare_type(i + 3, classifications, TERM_TYPE.NUMBER):
                    parse_results.append((classifications[i + 1][1] + '-' + classifications[i + 3][1]).lower())
                    del classifications[i + 1]
                    del classifications[i + 1]
                    del classifications[i + 1]
                else:
                    parse_results.append(term)

            # NUMBER
            elif classification is TERM_TYPE.NUMBER:
                # PRICE:
                # Number + Dollars
                if compare_type(i + 1, classifications, TERM_TYPE.DOLLARS):
                    # price over million
                    if 'B' in term or 'M' in term:
                        amount = term[-1]
                        term = term[:-1]
                        n = float(term)
                        if amount == 'M':
                            parse_results.append('{0:g}'.format(np.round(n, 2)) + ' M ' + 'Dollars')
                        elif amount == 'B':
                            parse_results.append('{0:g}'.format(np.round(n * 1000, 2)) + ' M ' + 'Dollars')
                    else:
                        parse_results.append(term + ' ' + 'Dollars')

                    del classifications[i + 1]

                # Number + U.S. + Dollars
                elif compare_type(i + 1, classifications, TERM_TYPE.US) and \
                        compare_type(i + 2, classifications, TERM_TYPE.DOLLARS):
                    parse_results.append(term + ' ' + 'Dollars')
                    del classifications[i + 1]
                    del classifications[i + 1]

                # Number + PERCENT
                elif compare_type(i + 1, classifications, TERM_TYPE.PERCENT):
                    parse_results.append(term + '%')
                    del classifications[i + 1]

                # Number + '-' + Number
                # Number + '-' + Word
                elif compare_type(i + 1, classifications, TERM_TYPE.HYPHEN) and \
                     (compare_type(i + 2, classifications, TERM_TYPE.NUMBER) or
                      compare_type(i + 2, classifications, TERM_TYPE.WORD)):
                    try:
                        parse_results.append((term + '-' + classifications[i + 2][1]).lower())
                        del classifications[i + 1]
                        del classifications[i + 1]
                    except:
                        pass

                # Number + Month
                elif compare_type(i + 1, classifications, TERM_TYPE.MONTH):
                    day_num = extract_int(term)
                    if day_num:
                        # day + month
                        if day_num and 1 <= day_num <= 31:
                            parse_results.append(self.months[classifications[i + 1][1]] + '-' + str("%02d" % (day_num,)))

                        del classifications[i + 1]

                # NUMBER
                parse_results.append(str(term))

            # $NUMBER (with commas)
            elif classification is TERM_TYPE.DOLLAR_NUMBER_COMMA:
                parse_results.append(str(term) + ' ' + 'Dollars')
                del classifications[i + 1]

            i += 1

        return parse_results

    def classify_terms(self, terms):
        classifications = []
        for term in terms:
            if len(term) > 0 and (term[-1] == '.' or term[-1] == ','):
                term = term[:-1]
            term_length = len(term)
            term_lower = term.lower()

            if term_length > 0 and term_lower not in self.stop_words:
                pair = self.extract_basic(term)
                if pair:
                    classifications.append(pair)

                # OTHER
                elif '-' in term:
                    split = term.split('-')
                    if 2 <= len(split) <= 3 and '' not in split:
                        all_basic = [self.extract_basic(t) for t in split]
                        if None not in all_basic:
                            for b in all_basic[:-1]:
                                classifications.append(b)
                                classifications.append((TERM_TYPE.HYPHEN, '-'))
                            classifications.append(all_basic[-1])

                # $Number
                elif term[0] == '$' and len(term) > 1:
                    n = term[1:]
                    b = self.extract_basic(n)
                    if b and b[0] is TERM_TYPE.NUMBER and ',' in n and is_number_with_commas(n):
                        classifications.append([TERM_TYPE.DOLLAR_NUMBER_COMMA, b[1]])
                    elif b and b[0] is TERM_TYPE.NUMBER:  # or b[0] is TERM_TYPE.FRACTION):
                        classifications.append([TERM_TYPE.DOLLAR_NUMBER, b[1]])

                elif term[-1] == '%' and len(term) > 1:
                    b = self.extract_basic(term[:-1])
                    if b and (b[0] is TERM_TYPE.NUMBER or b[0] is TERM_TYPE.FRACTION):
                        classifications.append([TERM_TYPE.NUMBER, b[1]])
                        classifications.append([TERM_TYPE.PERCENT, 'percent'])

                # extra rule 1: Number+th will be saved as a Number
                elif term[-2:] == 'th' and len(term) > 2:
                    b = self.extract_basic(term[:-2])
                    if b and (b[0] is TERM_TYPE.NUMBER):
                        classifications.append([TERM_TYPE.NUMBER, b[1]])

                # extra rule 2: #Number will be saved as a Number
                elif term[0] == '#' and len(term) > 1:
                    b = self.extract_basic(term[1:])
                    if b and (b[0] is TERM_TYPE.NUMBER):
                        classifications.append([TERM_TYPE.NUMBER, b[1]])

                else:
                    classifications.append((TERM_TYPE.NONE, 'None'))

        return classifications

    def extract_basic(self, term):
        # WORD
        if is_alpha(term):
            term_lower = term.lower()

            # recognized word
            if term_lower in self.alpha:
                return [self.alpha[term_lower], term_lower]

            # Month
            elif term_lower in self.months:
                return [TERM_TYPE.MONTH, term_lower]

            # Word Number (million, billion, etc.)
            elif term_lower in self.word_numbers:
                return [TERM_TYPE.WORD_NUMBER, term_lower]

            # other word
            else:
                return [TERM_TYPE.WORD, term]
        # U.S.
        elif term.lower() == 'u.s.':
            return [TERM_TYPE.US, term]

        # NUMBER
        else:
            if term[-1] in ['.', ',']:
                term = term[0:-1]

            num = extract_number(term)
            fraction = is_fraction(term)

            if num:
                return [TERM_TYPE.NUMBER, num]
            elif fraction:
                return [TERM_TYPE.FRACTION, term]
            elif is_number_with_commas(term):
                return [TERM_TYPE.NUMBER, int(term.replace(',', ""))]

        return None

    def init_months(self):
        self.months['january'] = '01'
        self.months['jan'] = '01'
        self.months['february'] = '02'
        self.months['feb'] = '02'
        self.months['march'] = '03'
        self.months['mar'] = '03'
        self.months['april'] = '04'
        self.months['apr'] = '04'
        self.months['may'] = '05'
        self.months['june'] = '06'
        self.months['jun'] = '06'
        self.months['july'] = '07'
        self.months['jul'] = '07'
        self.months['august'] = '08'
        self.months['aug'] = '08'
        self.months['september'] = '09'
        self.months['sep'] = '09'
        self.months['october'] = '10'
        self.months['oct'] = '10'
        self.months['november'] = '11'
        self.months['nov'] = '11'
        self.months['december'] = '12'
        self.months['dec'] = '12'

    def init_word_numbers(self):
        self.word_numbers['thousand'] = 1000
        self.word_numbers['million'] = 1000000
        self.word_numbers['m'] = 1000000
        self.word_numbers['billion'] = 1000000000
        self.word_numbers['bn'] = 1000000000
        self.word_numbers['trillion'] = 1000000000000
        self.word_numbers['tr'] = 1000000000000

# if __name__ == '__main__':
#     parser = Parser(0, '/Users/rina/Documents')
#     print(parser.parse({'text': '1 m dollars'}))