import random
import re
from nltk.corpus import wordnet as wn


def get_candi_verb(obj_type):
    if obj_type == "BUTTON" or obj_type == "IMAGEBUTTON" or obj_type == "IMAGEVIEW" or obj_type == "TEXTVIEW":
        return ['click', 'tap', 'choose', 'press', 'select', 'launch', 'open', 'click on']
    if obj_type == "CHECKBOX":
        return ['click', 'tap', 'select', 'click on']
    if obj_type == "EDITTEXT":
        return ['type', 'write', 'enter', 'input', 'put']
    if obj_type == "RADIOBUTTON":
        return ['click', 'tap', 'select', 'click on', 'turn on', 'turn off']
    if obj_type == "SWITCH":
        return ['turn', 'swipe', 'switch', "enable", "disable"]
    return ['click', 'tap', 'choose', 'press', 'select', 'open', 'click on']


def get_obj_article_word():
    object_article_words = ['', 'the']
    return random.choice(object_article_words)


def get_obj_name(obj_name):
    obj_name = re.sub("[^a-z0-9]", " ", obj_name.lower())
    obj_name = re.sub(r"\s+", " ", obj_name).strip()
    obj_tokens = obj_name.split(" ")
    ran_num = random.random()
    if len(obj_tokens) >= 3:
        if ran_num < 0.2:
            # 20% do remove
            remove_pos = random.randint(0, len(obj_tokens) - 1)
            obj_tokens.pop(remove_pos)
        elif ran_num < 0.4:
            #  20% do replace with synonym
            my_synonym = {"more options": "menu", "more option": "menu"}
            if obj_name.lower() in my_synonym.keys():
                obj_tokens = my_synonym[obj_name.lower()].split()
            else:
                replace_pos = random.randint(0, len(obj_tokens) - 1)
                synonym = get_synonyms(obj_tokens[replace_pos])
                # print("synonym", obj_tokens[replace_pos], synonym)
                obj_tokens[replace_pos] = synonym
        else:
            # 60% keep and do nothing
            pass
    obj_name = " ".join(obj_tokens)
    obj_name = re.sub(r"\s+", " ", obj_name).strip()
    quotation_mark = ["", "'", "\""]
    choose_quotation = random.choice(quotation_mark)
    return choose_quotation + obj_name + choose_quotation


def get_obj_abs_location(obj_bounds):
    abs_location = [["the top left corner", "the top", "the top right corner"], ["the left", "the center", "the right"],
                    ["the bottom left corner", "the bottom", "the bottom right corner"]]
    obj_posx = (obj_bounds[0] + obj_bounds[2]) / 2
    obj_posy = (obj_bounds[1] + obj_bounds[3]) / 2
    width_idx = min(int((3 * obj_posx) // 1440), 2)
    height_idx = min(int((3 * obj_posy) // 2560), 2)
    abs_location_desc = random.choice(["at ", "on ", "in "]) + abs_location[height_idx][width_idx]
    return random.choice(["", abs_location_desc])


def get_view_refer_name(view_info):
    # Priority 1: text from self
    if view_info["text"] != "none":
        # print("Priority 1: text from self, text")
        return view_info["text"].lower()
    if view_info["content_desc"] != "none":
        # print("Priority 1: text from self, content_desc")
        return view_info["content_desc"].lower()
    if view_info["hint"] != "none":
        # print("Priority 1: text from self, hint")
        return view_info["hint"].lower()
    # Priority 2: case layout, text from child
    if view_info["class"][-6:].lower() == "layout" and len(view_info["child_text"]) > 0:
        # print("Priority 2: case layout, text from child")
        return view_info["child_text"][0][0].lower()
    # Priority 3: return not none sibling text
    if len(view_info["sibling_text"]) > 0:
        for sibling_text in view_info["sibling_text"]:
            if sibling_text != "none":
                # print("Priority 3: return not none sibling text")
                return sibling_text.lower()
    # Priority 4: return only one child_text
    if len(view_info["child_text"]) == 1 and view_info["child_text"][0] != "none":
        # print("Priority 4: return only one child_text")
        return view_info["child_text"][0][0].lower()
    # Priority 5: return neighbor text
    # print("Priority 5: return neighbor text")
    return view_info["neighbor_text"].lower()


def get_action_desc(clickable_view):
    rand_num = random.random()
    if rand_num < 0.2:
        view_refer_name = get_view_refer_name(clickable_view)
        obj_name = get_obj_name(view_refer_name)
        if obj_name[0] == "\"" or obj_name[0] == "\'":
            obj_name = obj_name[1:-1]
        return obj_name
    else:
        view_class = str(clickable_view["class"])
        view_type = view_class.split(".")[-1].upper()
        candi_verb = get_candi_verb(view_type)
        use_verb = random.choice(candi_verb)
        article_word = get_obj_article_word()
        view_refer_name = get_view_refer_name(clickable_view)
        obj_name = get_obj_name(view_refer_name)
        abs_position = get_obj_abs_location(clickable_view["bounds"])
        desc_str = " ".join([use_verb, article_word, obj_name, abs_position])
        desc_str = re.sub("\s+", " ", desc_str)
        return desc_str


def get_synonyms(word):
    synonyms = set()
    for syn in wn.synsets(word):
        for l in syn.lemmas():
            synonym = l.name().replace("_", " ").replace("-", " ").lower()
            synonym = "".join([char for char in synonym if char in ' qwertyuiopasdfghjklzxcvbnm'])
            synonyms.add(synonym)
    if word in synonyms:
        synonyms.remove(word)
    synonyms = list(synonyms)
    synonyms = [synonym for synonym in synonyms if len(synonym.split(" ")) <= 2]
    if len(synonyms) > 0:
        return random.choice(synonyms)
    else:
        return word


def clean_change_line(text: str):
    return text.replace("\n", "").replace("\r", "")


def gen_view_str(view):
    view_tokens = []
    view_tokens.extend(["[type]", view["type"]])
    view_tokens.extend(["[text]", view["text"]])
    view_tokens.extend(["[content_desc]", view["content_desc"]])
    view_tokens.extend(["[hint]", view["hint"]])
    view_tokens.extend(["[resource_id]", view["resource_id"]])
    view_tokens.extend(["[abs_location]", view["abs_location"]])
    view_tokens.extend(["[neighbor_text]", view["neighbor_text"]])
    # view_tokens.extend(["[sibling_text]", view["process_sibling_text"]])
    process_sibling_text = [t.strip().lower() for t in view["sibling_text"] if t != "none" and len(t.split(" ")) < 10 and len(t) < 50]
    if len(process_sibling_text) != 0:
        process_sibling_text = " , ".join(process_sibling_text)
    else:
        process_sibling_text = "none"
    view_tokens.extend(["[sibling_text]", process_sibling_text])

    # view_tokens.extend(["[child_text]", view["process_child_text"]])
    process_child_text = [t[0].lower() for t in view["child_text"] if t[0] != "none" and len(t[0].split(" ")) < 10 and len(t[0]) < 50]
    if len(process_child_text) != 0:
        process_child_text = " , ".join(process_child_text)
    else:
        process_child_text = "none"
    view_tokens.extend(["[child_text]", process_child_text])
    view_tokens.extend(["[parent_text]", view["parent_text"]])
    view_str = " ".join(view_tokens)
    view_str = re.sub(r"\s+", " ", view_str).strip()
    return clean_change_line(view_str)

if __name__ == '__main__':
    # print("view_class.split('.')[-1].lower()".upper())
    # print(10 // 3)
    print(random.random())