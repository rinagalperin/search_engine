import locale
import numpy as np
from fractions import Fraction

# checks if a term contains only alpha-numeric characters
def is_alpha(word):
    try:
        return word.encode('ascii').isalpha()
    except:
        return

# checks if a term is a valid fraction
def is_fraction(term):
    try:
        num = Fraction(term)
        return num
    except:
        return

# checks if a term is a valid number with comma separations
def is_number_with_commas(str):
    num_str = str.replace(',', '')
    num = extract_number(num_str)

    if num:
        correct_commas = extract_number_with_commas(num)

        if correct_commas == str:
            return True

    return False

# formats a number with comma separations
def extract_number_with_commas(num):
    '{0:g}'.format(num)
    correct_commas = locale.format("%d", num, grouping=True)

    return correct_commas

# checks if a term is a valid number
def extract_number(term):
    try:
        num = float(term)
        return num
    except:
        return

# checks if a term is a valid integer.
def extract_int(term):
    try:
        num = int(term)
        return num
    except:
        return

# formats a number with corresponding K/B/M symbols
def extract_parsed_number(num):
    if '/' not in str(num):
        num_abs = abs(num)
        # smaller than a thousand
        if num_abs < 1000:
            return str('{0:g}'.format(np.round(num, 2)))

        # thousands
        elif 1000000 > num_abs >= 1000:
            return str('{0:g}'.format(np.round(num / 1000, 2))) + 'K'

        # millions
        elif 1000000000 > num_abs >= 1000000:
            return str('{0:g}'.format(np.round(num / 1000000, 2))) + 'M'

        # billions
        elif num_abs >= 1000000000:
            return str('{0:g}'.format(np.round(num / 1000000000, 2))) + 'B'
    else:
        return str(num)

# checks if a term in a certain index has a given classification
def compare_type(place, classifications, type):
    return place < len(classifications) and classifications[place][0] is type
