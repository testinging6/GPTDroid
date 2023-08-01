import json
from pprint import pprint
import xmltodict
from utils import *
import uiautomator2 as u2
from loguru import logger

last_step = ""

few_shot = """
Now that you are an automated testing program for Android software, \
what you have to do is test the functionality of the software as completely as possible \
and check for any problems. I will tell you the information of the current program interface \
by asking questions, and you will tell me the next step of the test by answering.

When you encounter components with similar names, you can look at them as the same category and test one or more of them. When you encounter many operation options, you tend to click on them from smallest to largest, and tend to click on the component with "menu button" in its name.

Now that you are an automated testing program for Android software, what you have to do is test the functionality of the software as completely as possible and check for any problems. I will tell you the information of the current program interface by asking questions, and you will tell me the next step of the test by answering.

"""

start = True


def next(is_start: bool, step: int):
    """
    :param is_start: 
    :param step:
    :return:
    """
    global last_step
    global start

    logger.info("A new turn ...")

    start = False
    logger.info('reload the page...')
    d = u2.connect()
    print(d.info)
    page_source = d.dump_hierarchy(compressed=True, pretty=True)
    xml_file = open(save_path + 'hierarchy.xml', 'w', encoding='utf-8')
    xml_file.write(page_source)
    xml_file.close()
    xml_file = open(save_path + 'hierarchy.xml', 'r', encoding='utf-8')
    logger.info('reading hierarchy tree xml file...')
    data_dict = xmltodict.parse(xml_file.read())
    data_str = json.dumps(data_dict)
    json_file = open(save_path + 'hierarchy.json', 'w', encoding='utf-8')
    json_file.write(data_str)
    json_file.close()
    
    all_components = getAllComponents(data_dict)
    logger.info("There is {} components on current page.".format(str(len(all_components))))

    running_info = get_running_info()
    # ActivityName
    activity_name = running_info['activity'].replace('.', ' ').split(' ')[-1].replace('Activit', '')
    print("activity_name: {}".format(activity_name))

    jsonfile = open(r'./json/{}.json'.format(appname), 'r')
    jsondata = json.load(jsonfile)
    pprint(jsondata)

    logger.info('searching for describable components...')
    components_list = []
    for e_component in all_components:
        info = get_common_desc(e_component)
        desc = info['desc']
        if desc != "":
            e_component['@desc'] = desc
            components_list.append(e_component)


    origin_list = [e["@desc"] for e in components_list]
    renamed_list = rename_duplicate(origin_list)

    for i, e in enumerate(renamed_list):
        components_list[i]["@desc"] = e

    logger.info('searching for clickable components...')
    clickable_list = []

    for e_component in components_list:
        if e_component['@clickable'] == 'true':
            info = {"desc": e_component["@desc"], "bounds": e_component["@bounds"]}
            clickable_list.append(info)

    logger.info('searching for editable components...')
    edit_list = []
    for e_component in components_list:
        if '@class' in e_component and (e_component['@class'] == 'android.widget.EditText' or
                                        e_component['@class'] == 'android.widget.AutoCompleteTextView'):
            edit_list.append(e_component)


    print("--- There are describable components: ---")
    for e in components_list:
        print(e)
    print("----------------------------------------")

    print("--- There are clickable components: ---")
    for e in clickable_list:
        print(e)
    print("----------------------------------------")

    print("--- There are editable components: ---")
    for e in edit_list:
        print(e)
    print("----------------------------------------")


    up_half, down_half = split_page(components_list)

    up_half = [e["@desc"] for e in up_half]
    down_half = [e["@desc"] for e in down_half]

    print("up half: {}".format(up_half))
    print("down half: {}".format(down_half))

    # WidgetC WidgetID/WidgetT WidgetAct WidgetV
    widget_list = []
    for e in components_list:
        temp = {}
        # 
        temp["WidgetC"] = e["@class"].split(".")[-1]
        # 
        if e["@text"] == "" and e["@content-desc"] == "":
            temp["widgetID"] = e["@desc"]
        else:
            temp["widgetT"] = e["@desc"]
        # 
        temp["WidgetAct"] = "none"
        if "@clickable" in e and e["@clickable"] == "true":
            temp["WidgetAct"] = "Click"
        # 
        temp["WidgetV"] = "0"
        widget_list.append(temp)
    pprint(widget_list)

    jsondata["Page information attribute"] = [{
        "ActivityName": activity_name,
        "Widgets": [e["@desc"] for e in components_list],
        "Layouts": [
            {
                "Upper half": up_half,
                "Lower half": down_half
            }
        ]
        # "VisitTime": "1",
        # "Duplicate": "0"
    }]
    jsondata["Widget information attribute"] = [{}]
    for i, e in enumerate(widget_list):
        jsondata["Widget information attribute"][0]["Widget_{}".format(str(i + 1))] = [e]

    print("json data:")
    pprint(jsondata)

    jsonstr = json.dumps(jsondata)
    f = open('./json/{}-step{}.json'.format(appname, str(step + 1)), 'w')
    f.write(jsonstr)
    f.close()


    prompt = "We want to test the {} App, which has {} main function pages, namely: ".format(appname, str(len(jsondata["Global information attribute"][0]["Activities"])))

    for e in jsondata["Global information attribute"][0]["Activities"]:
        prompt += '"{}", '.format(e)
    prompt = prompt[:-2]

    prompt += '.\nThe recommended test sequence is: '

    for e in jsondata["Global information attribute"][0]["Priority"]:
        prompt += '"{}", '.format(e)
    prompt = prompt[:-2]

    prompt += '.\nThe function UI page we are currently testing is "{}".\n'.format(activity_name)

    prompt += 'The number of expoloration recorded on the current page is {}.\n'.format(jsondata["Page information attribute"][0]["VisitTime"])

    prompt += "Now we can do these:\n"

    opt_id = 1
    for e in clickable_list:
        prompt += '{}. click "{}"\n'.format(str(opt_id), e["desc"])
        opt_id += 1
    prompt += "{}. return to previous page\n".format(str(opt_id))
    prompt += "What do you choose to do? Please answer directly with one of the options. \n"
    print(prompt)

    res = getOutput(few_shot + prompt)

    print(res)

    if res.lower().find("click") != -1:
        # 
        target = get_quote(res)[0]
        click(target, components_list)
        last_step = 'click "{}"'.format(target)

    # 
    if res.lower().find("return to previous page") != -1:
        get_back()
        last_step = "return to previous page"

    print(last_step)

    # 
    new_running_info = get_running_info()
    # 
    new_activity_name = new_running_info['activity'].replace('.', ' ').split(' ')[-1].replace('Activit', '')
    print("new activity_name: {}".format(new_activity_name))

    # 
    if is_start:
        g_file = open('./gragh/{}.txt'.format(appname), 'w', encoding='utf-8')
        g_file.close()

    # 
    if not os.path.exists('./gragh/{}.txt'.format(appname)):
        g_file = open('./gragh/{}.txt'.format(appname), 'w', encoding='utf-8')
        g_file.close()
    g_file = open('./gragh/{}.txt'.format(appname), 'r', encoding='utf-8')
    lines = len(g_file.readlines())
    g_file.close()
    # 
    g_file = open('./gragh/{}.txt'.format(appname), 'a', encoding='utf-8')
    g_file.write("Step {}: {} <- {} -> {}\n".format(str(lines + 1), activity_name, res, new_activity_name))

    is_start = False


if __name__ == '__main__':
    for step in range(5):
        next(start, step)