from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer
from nltk.corpus import wordnet as WN
import re
import os

stop_words = stopwords.words('english')
all_stop_words = stop_words.copy()
all_stop_words.extend(["button", "long", "like", "long"])
snowball_stemmer = SnowballStemmer("english")

verbs = ['select', 'choose', 'swipe', 'press', 'type', 'enter', 'change', 'switch', 'enable', 'open', 'clicking',
         'disable', 'launch', 'set', 'tap', 'click', 'go', 'turn', 'write', 'input', 'put', "crash"]
stem_verbs = [snowball_stemmer.stem(w) for w in verbs]


def clean_irrelevant_word(step_str: str):
    if "\t" in step_str:
        step_str = step_str.split("\t")[1]
    step_str = step_str.replace("e.g.", " ").lower()
    step_str = re.sub("[^a-z]", " ", step_str)
    step_str = re.sub(r"\s+", " ", step_str)
    relevant_word = []
    for word in step_str.split():
        stem_word = snowball_stemmer.stem(word)
        if word == "settings":
            relevant_word.append(word)
        if stem_word not in stem_verbs and stem_word not in all_stop_words:
            relevant_word.append(word)
    return relevant_word


def show_all_step():
    data_dir = "recdroid_view"
    for dir in os.listdir(data_dir):
        step_file = data_dir + "/" + dir + "/val_desc.tsv"
        step_lines = open(step_file, "r").readlines()
        step_lines = [l.split("\t")[1].strip() for l in step_lines]
        for line in step_lines:
            print(line)
            print(clean_irrelevant_word(line))
            print("")


def check_is_in_dict(word: str):
    if not WN.synsets(word) and word not in stop_words:
        print("not in dict:", word)
        for i in range(1, len(word)):
            sub_word1 = word[:i]
            sub_word1_in_dict = WN.synsets(sub_word1) or sub_word1 in stop_words
            sub_word2 = word[i:]
            sub_word2_in_dict = WN.synsets(sub_word2) or sub_word2 in stop_words
            if sub_word1_in_dict and sub_word2_in_dict:
                print("joint word:", word, ":", sub_word1, sub_word2)
                return False
        return True
    else:
        return False


if __name__ == '__main__':
    show_all_step()
