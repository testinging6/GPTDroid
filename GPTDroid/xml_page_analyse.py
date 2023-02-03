import lxml
from lxml import etree
from lxml.etree import Element, SubElement, ElementTree
import collections
import json
import re


doc = '''
<html>
 <head>
  <base href='http://example.com/' />
  <title>Example website</title>
 </head>
 <body>
  <div id='images'>
   <a href='image1.html' id="xxx">Name: My image 1 <br /><img src='image1_thumb.jpg' /></a>
   <h5>test</h5>
   <a href='image2.html'>Name: My image 2 <br /><img src='image2_thumb.jpg' /></a>
   <a href='image3.html'>Name: My image 3 <br /><img src='image3_thumb.jpg' /></a>
   <a href='image4.html'>Name: My image 4 <br /><img src='image4_thumb.jpg' /></a>
   <a href='image5.html' class='li li-item' name='items'>Name: My image 5 <br /><img src='image5_thumb.jpg' /></a>
   <a href='image6.html' name='items'><span><h5>test</h5></span>Name: My image 6 <br /><img src='image6_thumb.jpg' /></a>
  </div>
 </body>
</html>
'''


def get_edittext_xpath(doc):
    # doc = doc.replace('<?xml version="1.0" encoding="UTF-8"?>', "")
    doc = re.sub(r"<\?xml version=['\"]1\.0['\"] encoding=['\"]UTF-8['\"].*?>", "", doc)
    xml_parser = etree.XML(doc)
    tree = xml_parser.getroottree()
    all_nodes = xml_parser.xpath('//*')
    edittext_xpath = []
    for node in all_nodes:
        node_tag = node.tag
        node_type = node_tag.split(".")[-1]
        if node_type[-8:].lower() == "edittext":
            xpath = tree.getpath(node)
            edittext_xpath.append(xpath)
    return edittext_xpath


def get_all_clickable_view(doc):
    # doc = doc.replace('<?xml version="1.0" encoding="UTF-8"?>', "")
    doc = re.sub(r"<\?xml version=['\"]1\.0['\"] encoding=['\"]UTF-8['\"].*?>", "", doc)
    xml_parser = etree.XML(doc)
    tree = xml_parser.getroottree()
    all_nodes = xml_parser.xpath('//*')
    edittexts = {}
    clickable_views = {}
    for node in all_nodes:
        node_tag = node.tag
        node_type = node_tag.split(".")[-1]
        if "clickable" not in node.attrib.keys():
            continue

        node_clickable = (node.attrib["clickable"] == 'true') or (node.attrib["long-clickable"] == 'true')
        if node_clickable:
            xpath = tree.getpath(node)
            copy_dict = dict(node.attrib)
            bounds_str = copy_dict["bounds"]
            bounds_str = "[" + bounds_str.replace("][", "],[") + "]"
            bounds_arr = eval(bounds_str)
            copy_dict["bounds"] = bounds_arr
            copy_dict.setdefault("xpath", xpath)
            if node_type[-8:].lower() == "edittext":
                copy_dict.setdefault("child_text", [])
                copy_dict.setdefault("event_view_words", "")
                edittexts.setdefault(xpath, copy_dict)
            else:
                child_text = []
                get_child_text(child_text, node)
                copy_dict.setdefault("child_text", child_text)
                event_view_words = ""
                if "text" in copy_dict.keys() and len(copy_dict["text"]) > 0:
                    event_view_words = copy_dict["text"]
                elif len(child_text) > 0:
                    event_view_words = "\n".join(child_text)
                elif "resource-id" in copy_dict.keys() and len(copy_dict["resource-id"]) > 0:
                    event_view_words = copy_dict["resource-id"]
                copy_dict.setdefault("event_view_words", event_view_words)
                clickable_views.setdefault(xpath, copy_dict)
    return edittexts, clickable_views


def get_target_by_text(doc, target_text: str):
    # doc = doc.replace('<?xml version="1.0" encoding="UTF-8"?>', "")
    doc = re.sub(r"<\?xml version=['\"]1\.0['\"] encoding=['\"]UTF-8['\"].*?>", "", doc)
    xml_parser = etree.XML(doc)
    all_nodes = xml_parser.xpath('//*')
    target_text = target_text.lower().strip()
    for node in all_nodes:
        if "text" not in node.attrib.keys() or "bounds" not in node.attrib.keys():
            continue
        node_text = node.attrib["text"]
        if node_text == None or len(node_text.strip()) == 0:
            continue
        clean_node_text = node_text.lower().strip()
        if clean_node_text == target_text:
            bounds_str = node.attrib["bounds"]
            bounds_str = "[" + bounds_str.replace("][", "],[") + "]"
            bounds_arr = eval(bounds_str)
            target_x = (bounds_arr[0][0] + bounds_arr[1][0]) // 2
            target_y = (bounds_arr[0][1] + bounds_arr[1][1]) // 2
            return (target_x, target_y)
    return (0, 0)


def get_child_text(child_text: list, node):
    if node.attrib["text"] != "":
        child_text.append(node.attrib["text"])
    for child_node in node:
        get_child_text(child_text, child_node)


def get_id2xpath(xml_page):
    # xml_page = xml_page.replace('<?xml version="1.0" encoding="UTF-8"?>', "")
    xml_page = re.sub(r"<\?xml version=['\"]1\.0['\"] encoding=['\"]UTF-8['\"].*?>", "", xml_page)
    xml_parser = etree.XML(xml_page)
    tree = xml_parser.getroottree()
    all_nodes = xml_parser.xpath('//*')
    id2xpath = {}
    xpath = []
    for node in all_nodes:
        xpath.append(tree.getpath(node))
    for node, path in zip(all_nodes, xpath):
        node_id = int(node.attrib["id"])
        id2xpath.setdefault(node_id, path)
    return id2xpath


def gen_xml():
    state_file_path = "../Data/RecDroid/DroidBotRes/1.newsblur_s/states/state_2021-12-13_161908.json"
    state_detail = json.load(open(state_file_path, "r", encoding="UTF-8"))
    id2class = {}
    child_dict = {}
    # loop 1: map temp_id to view
    for view in state_detail["views"]:
        id2class.setdefault(view["temp_id"], view["class"])
        child_dict.setdefault(view["temp_id"], {"text_children": [], "children": view["children"]})

    root_ele = Element("hierarchy", attrib={'id': '-1'})
    gen_xml_recursive(id2class, child_dict, root_ele, 0)
    tree = ElementTree(root_ele)
    tree_text = etree.tostring(tree, encoding='utf8', method='xml', pretty_print=True)
    tree_text = str(tree_text, encoding="utf-8")
    get_id2xpath(tree_text)


def gen_xml_recursive(id2class, child_dict, parent, cur_id):
    cur_class = id2class[cur_id]
    cur_ele = SubElement(parent, cur_class, attrib={'id': str(cur_id)})
    for child_id in child_dict[cur_id]["children"]:
        gen_xml_recursive(id2class, child_dict, cur_ele, child_id)


def has_scroll_view(doc):
    # doc = doc.replace('<?xml version="1.0" encoding="UTF-8"?>', "")
    doc = re.sub(r"<\?xml version=['\"]1\.0['\"] encoding=['\"]UTF-8['\"].*?>", "", doc)
    xml_parser = etree.XML(doc)
    all_nodes = xml_parser.xpath('//*')
    for node in all_nodes:
        if "class" not in node.attrib.keys() or "scrollable" not in node.attrib.keys():
            continue
        flag_1 = node.attrib["scrollable"] == "true"
        if flag_1:
            print(node.attrib)
        flag_2 = "RecyclerView" in node.attrib["class"] or "Layout" in node.attrib["class"] or "ListView" in node.attrib["class"]
        if flag_1 and flag_2:
            # print(node.attrib)
            return True
    return False


if __name__ == '__main__':
    # test_doc = open("save_xml.xml", "r").read()
    # get_all_clickable_view(test_doc)
    # gen_xml()
    doc1 = open("../Temp/mydata_6_1.xml", "r").read()
    print(has_scroll_view(doc1))
