import torch
import pickle
import torch.utils.data as data
import json
from PIL import Image
import random
import os
from add_click import gen_view_str, get_action_desc
import pandas as pd


def gen_dataset(dataset_type):
    sample_negative = 4 if dataset_type == "train" else 15
    view_idx = 0
    desc_idx = 0
    view_str_idx = 0
    all_views = {}
    all_descs = {}
    data_item = {"desc_idx": [], "view_idx": [], "label": [], "image": []}
    for pkl_idx in range(15):
        # for pkl_file in os.listdir("data/" + dataset_type + "_pkls/"):
        pkl_path = "data/" + dataset_type + "_pkls/rico_click_match_" + str(pkl_idx) + ".pkl"
        if not os.path.exists(pkl_path):
            continue
        datas = pickle.load(open(pkl_path, "rb"))
        for rico_idx, view_infos in datas.items():
            for view_info in view_infos:
                cur_view = view_info["view"]
                view_class = cur_view["class"]
                if view_class[-11:].lower() == "imagebutton" or view_class[-9:].lower() == "imageview":
                    copy_view = cur_view.copy()
                    copy_view['content_desc'] = "none"
                    cur_view_str = gen_view_str(copy_view)
                else:
                    cur_view_str = gen_view_str(cur_view)
                cur_view.setdefault("gen_view_str", cur_view_str)
                all_views.setdefault(view_idx, cur_view)
                view_idx += 1
    all_view_keys = list(all_views.keys())
    for cur_view_idx, view_info in all_views.items():
        for _ in range(3):
            use_negs = random.sample(all_view_keys, sample_negative)
            if view_idx in use_negs:
                use_negs.remove(cur_view_idx)
            cur_action_desc_idx = desc_idx
            action_desc = get_action_desc(view_info)
            all_descs.setdefault(cur_action_desc_idx, action_desc)
            desc_idx += 1
            # add positive
            data_item["desc_idx"].append(cur_action_desc_idx)
            data_item["view_idx"].append(cur_view_idx)
            data_item["label"].append(1.0)
            img_path = "/home/wongwuchiu/ATestReport/ViewMatch/view_image/" + str(view_info["view_image_idx"]) + ".jpg"
            data_item["image"].append(img_path)
            # add negative
            for neg in use_negs:
                data_item["desc_idx"].append(cur_action_desc_idx)
                data_item["view_idx"].append(neg)
                data_item["label"].append(0.0)
                img_path = "/home/wongwuchiu/ATestReport/ViewMatch/view_image/" + str(all_views[neg]["view_image_idx"]) + ".jpg"
                data_item["image"].append(img_path)
    all_views_lines = [str(view_key) + "\t" + view["gen_view_str"] for view_key, view in all_views.items()]
    all_views_file = open("data/" + dataset_type + "_views.tsv", "w", encoding="UTF-8")
    all_views_file.write("\n".join(all_views_lines))
    all_desc_lines = [str(desc_key) + "\t" + desc for desc_key, desc in all_descs.items()]
    all_desc_file = open("data/" + dataset_type + "_desc.tsv", "w", encoding="UTF-8")
    all_desc_file.write("\n".join(all_desc_lines))
    df = pd.DataFrame(data_item)
    df.to_csv("data/" + dataset_type + "_data.csv", index=False)


if __name__ == '__main__':
    # for dataset_type in ["train", "test", "val"]:
    #     gen_dataset(dataset_type)
    for dataset_type in ["train"]:
        gen_dataset(dataset_type)