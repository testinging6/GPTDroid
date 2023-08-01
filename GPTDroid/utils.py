import os
import re
import subprocess
import time
import openai
import cv2

save_path = r"xxx"
# 
appname = "AmazeFileManager"
# 
click_idx = 0

pic_index = 1



def subprocess_getoutput(stmt):
    """
    :param stmt: 
    :return: 
    """
    result = subprocess.getoutput(stmt)
    # 
    return result  # 


def get_back():
    """
    
    """
    cmd = r"adb shell input keyevent 4"
    print("run command: {}".format(cmd))
    os.system(cmd)


def get_running_info():
    """
    """
    cmd = r"adb shell dumpsys activity activities | findstr mControlTarget=Window"
    res = subprocess_getoutput(cmd)
    real_res = res.split('\n')[0].strip()
    p1 = re.compile(r'[{](.*?)[}]', re.S)
    arr = re.findall(p1, real_res)
    final_ans = arr[0].split()[-1].split('/')
    if len(final_ans) < 2:
        return
    app_name = final_ans[0]
    activity_name = final_ans[1][len(app_name) + 1: -1]
    return {'app': app_name, 'activity': activity_name}



def getAllComponents(jsondata: dict):
    """
    
    """

    root = jsondata['hierarchy']

    queue = [root]
    res = []
    # 
    node_cnt = 0
    while queue:
        currentNode = queue.pop(0)
        # 
        if ('@resource-id' in currentNode and 'com.android.systemui' in currentNode['@resource-id']) or ('@package' in currentNode and 'com.android.systemui' in currentNode['@package']):
            continue
        node_cnt += 1
        # 
        if 'node' in currentNode:
            # 
            if '@clickable' in currentNode and currentNode['@clickable'] == 'true':
                # 
                if type(currentNode['node']).__name__ == 'dict':
                    currentNode['node']['@clickable'] = 'true'
                else:
                    for e in currentNode['node']:
                        e['@clickable'] = 'true'
            # 
            if type(currentNode['node']).__name__ == 'dict':
                queue.append(currentNode['node'])
            else:
                for e in currentNode['node']:
                    queue.append(e)
        else:
            res.append(currentNode)

    return res


def getOutput(question: str):
    """
    """
    openai.api_key = "XXXX"

    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=question + "\nA:",
        temperature=0.5,
        max_tokens=50,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        stop=["\n"]
    )

    return response.choices[0].text


def get_bounds(bounds):
    """

    """
    res = []
    bounds = bounds.split(',')
    res.append(bounds[0].replace('[', ''))
    mid = bounds[1].split('][')
    res.append(mid[0])
    res.append(mid[1])
    res.append(bounds[2].replace(']', ''))
    res = [int(e) for e in res]
    return res


def screen_shot(index: int, bounds):
    """
    """
    cmd = r"adb shell /system/bin/screencap -p /sdcard/screenshot-" + str(index) + ".png"
    print("run command: {}".format(cmd))
    os.system(cmd)
    cmd = r"adb pull /sdcard/screenshot-" + str(index) + ".png " + save_path
    print("run command: {}".format(cmd))
    os.system(cmd)
    image = cv2.imread(save_path + "screenshot-" + str(index) + ".png")
    cv2.rectangle(image, (bounds[0], bounds[1]), (bounds[2], bounds[3]), (0, 0, 255), 4)
    cv2.imwrite(save_path + "screenshot-" + str(index) + ".png", image)


def screen_shot_end(index: int):
    """
    """
    cmd = r"adb shell /system/bin/screencap -p /sdcard/screenshot-" + str(index) + ".png"
    print("run command: {}".format(cmd))
    os.system(cmd)
    cmd = r"adb pull /sdcard/screenshot-" + str(index) + ".png " + save_path
    print("run command: {}".format(cmd))
    os.system(cmd)


def click(text_name: str, all_components: list):
    """
    :param text_name:
    :param all_components:
    :return:
    """
    time.sleep(0.5)
    global pic_index
    is_clicked = False
    for e_component in all_components:
        if e_component['@desc'] == text_name:
            bounds = e_component['@bounds']
            res = get_bounds(bounds)
            screen_shot(pic_index, res)
            pic_index += 1
            cmd = "adb shell input tap {x} {y}"
            cmd = cmd.replace('{x}', str((res[0] + res[2]) / 2)).replace('{y}', str((res[1] + res[3]) / 2))
            print("run command: {}".format(cmd))
            os.system(cmd)
            is_clicked = True
            break
    if is_clicked:
        print(text_name + " is clicked.")
    else:
        print(text_name + " is not found.")


def rename_duplicate(alist):
    """
    :param alist:
    :param print_result:
    :return:
    """
    new_list = [v + str(alist[:i].count(v) + 1) if alist.count(v) > 1 else v for i, v in enumerate(alist)]
    return new_list


def input_text(content: str, bounds):
    """
    """
    global pic_index
    res = get_bounds(bounds)
    screen_shot(pic_index, res)
    pic_index += 1

    cmd = "adb shell input tap {x} {y}"

    cmd = cmd.replace('{x}', str((res[0] + res[2]) / 2)).replace('{y}', str((res[1] + res[3]) / 2))
    print("run command: {}".format(cmd))
    os.system(cmd)

    content = content.replace(' ', '\ ')

    cmd = "adb shell input text " + content
    os.system(cmd)


def get_common_desc(e: dict):
    """
    :param e: 
    :return: 
    """
    text = e['@text']
    content = e['@content-desc']
    rid = e['@resource-id']
    bounds = e['@bounds']
    desc = ""
    if text != "":
        desc = text
    elif content != "":
        desc = content
    elif rid != "":
        desc = rid.split('/')[-1]
        desc = desc.replace('_', ' ')
    else:
        desc = ""
    return {"desc": desc, "bounds": bounds}


def get_quote(content: str):
    """
    :param content: 
    :return: 
    """
    return re.findall(r'["](.*?)["]', content)


def long_click(text_name: str, all_components: list):
    """
    :param text_name: 
    :param all_components: 
    :return:
    """
    time.sleep(0.5)
    global pic_index
    is_clicked = False
    for e_component in all_components:
        if e_component['desc'] == text_name:
            bounds = e_component['bounds']
            res = get_bounds(bounds)
            screen_shot(pic_index, res)
            pic_index += 1
            cmd = "adb shell input swipe {} {} {} {} {}".format(str((res[0] + res[2]) / 2), str((res[1] + res[3]) / 2), str((res[0] + res[2]) / 2 + 1), str((res[1] + res[3]) / 2 + 1), 500)
            print("run command: {}".format(cmd))
            os.system(cmd)
            is_clicked = True
            break
    if is_clicked:
        print(text_name + " is clicked.")
    else:
        print(text_name + " is not found.")

def split_page(all_components: list):
    """
    :param components:
    :return:
    """
    size_str = subprocess_getoutput("adb shell wm size")
    size_str = size_str.split(' ')[-1]
    size_str = size_str.split('x')
    width = int(size_str[0])
    height = int(size_str[1])

    up_half = []
    down_half = []

    for e in all_components:
        bounds = e['@bounds']
        res = get_bounds(bounds)
        y = (res[1] + res[3]) / 2
        if y < height / 2:
            up_half.append(e)
        else:
            down_half.append(e)

    return up_half, down_half