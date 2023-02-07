import torch
import pickle
import torch.utils.data as data
import json
from PIL import Image
from random import random
import os
from torchvision import transforms
from transformers import AutoTokenizer
import pandas as pd
from torch.utils.data import DataLoader
from sentence_transformers import InputExample
import time

test_tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")


class ViewMatchDataset(data.Dataset):
    def __init__(self, data_dir: str = "../Temp/current_views"):
        self.transform = transforms.Compose([
            transforms.Resize((256, 256)),
            transforms.CenterCrop(min(244, 256)),
            transforms.ToTensor(),
            transforms.Normalize((0.485, 0.456, 0.406),
                                 (0.229, 0.224, 0.225))])
        self.tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
        self.all_views = {}
        print("load train data from dir:", data_dir)
        data_keys = ["desc_idx", "view_idx", "label", "image"]
        with open(data_dir + "/train_views.tsv", 'r', encoding='utf8') as fIn1:
            for line in fIn1.readlines():
                view_id, view_str = line.strip().split("\t")
                self.all_views[int(view_id)] = view_str
        self.all_desc = {}
        with open(data_dir + "/train_desc.tsv", 'r', encoding='utf8') as fIn2:
            for line in fIn2.readlines():
                split_res = line.strip().split("\t")
                if len(split_res) == 1:
                    desc_id = split_res[0]
                    desc_str = "none"
                else:
                    desc_id, desc_str = line.strip().split("\t")
                self.all_desc[int(desc_id)] = desc_str
        df = pd.read_csv(data_dir + "/train_data.csv")
        self.datas = []
        for idx, row in df.iterrows():
            self.datas.append({"desc_idx": row["desc_idx"], "view_idx": row["view_idx"], "label": row["label"],
                               "image": row["image"]})

        # self.datas = []
        # data_lines = open(data_dir + "/train_data.csv", "r").readlines()
        # for line in data_lines:
        #     if len(line.strip()) == 0:
        #         continue
        #     cur_items = line.strip().split(",")
        #     cur_data = {data_key: data_item for (data_key, data_item) in zip(data_keys, cur_items)}
        #     self.datas.append(cur_data)
        # print(self.datas[0])
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self._target_device = torch.device(device)

    def __getitem__(self, index):
        """Returns one data pair (image and caption)."""
        data_info = self.datas[index]
        cur_desc = self.all_desc[data_info["desc_idx"]]
        cur_view = self.all_views[data_info["view_idx"]]
        # tokenize_res = self.tokenizer(cur_desc, cur_view)
        label = data_info["label"]
        image_path = data_info["image"]
        image = Image.open(image_path).convert('RGB')
        if self.transform is not None:
            image = self.transform(image)
        return cur_desc, cur_view, image, label

    def __len__(self):
        return len(self.datas)


def load_valid_samples(data_dir: str = "data"):
    all_views = {}
    print("load valid samples from:", data_dir)
    with open(data_dir + "/val_views.tsv", 'r', encoding='utf8') as fIn1:
        for line in fIn1.readlines():
            view_id, view_str = line.strip().split("\t")
            all_views[int(view_id)] = view_str
    all_desc = {}
    with open(data_dir + "/val_desc.tsv", 'r', encoding='utf8') as fIn2:
        for line in fIn2.readlines():
            split_res = line.strip().split("\t")
            if len(split_res) == 1:
                desc_id = split_res[0]
                desc_str = "none"
            else:
                desc_id, desc_str = line.strip().split("\t")
            all_desc[int(desc_id)] = desc_str
    df = pd.read_csv(data_dir + "/val_data.csv")
    # self.datas = []
    # for idx, row in df.iterrows():
    #     self.datas.append({"desc_idx": row["desc_idx"], "view_idx": row["view_idx"], "label": row["label"],
    #                        "image": row["image"]})
    datas = {}
    for _, row in df.iterrows():
        desc_idx = row["desc_idx"]
        if desc_idx not in datas.keys():
            if len(datas.keys()) > 2000:
                break
            else:
                cur_query = all_desc[desc_idx]
                datas.setdefault(desc_idx, {"query": cur_query, "pos": [], "neg": []})
        label = row["label"]
        if label > 0.5:
            # pos sample
            datas[desc_idx]["pos"].append({"view": all_views[row["view_idx"]], "image": row["image"]})
        else:
            # neg sample
            datas[desc_idx]["neg"].append({"view": all_views[row["view_idx"]], "image": row["image"]})
    return datas


class ValidDataset(data.Dataset):
    def __init__(self, example):
        self.transform = transforms.Compose([
            transforms.Resize((256, 256)),
            transforms.CenterCrop(min(244, 256)),
            transforms.ToTensor(),
            transforms.Normalize((0.485, 0.456, 0.406),
                                 (0.229, 0.224, 0.225))])
        # self.tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
        self.docs_and_image = []
        self.query = example["query"]
        self.docs_and_image.append([example["pos"][0]["view"], example["pos"][0]["image"]])
        for info in example["neg"]:
            self.docs_and_image.append([info["view"], info["image"]])

    def __getitem__(self, index):
        image_path = self.docs_and_image[index][1]
        image = Image.open(image_path).convert('RGB')
        if self.transform is not None:
            image = self.transform(image)
        return self.query, self.docs_and_image[index][0], image

    def __len__(self):
        return len(self.docs_and_image)


def smart_batching_collate(batch):
    texts = [[], []]
    images = []
    labels = []
    # print(batch[2])
    # print(type(batch[2]))
    # print(batch[2].shape)
    for example in batch:
        texts[0].append(example[0].strip())
        texts[1].append(example[1].strip())
        images.append(example[2])
        labels.append(example[3])

    tokenized = test_tokenizer(texts[0], texts[1], padding=True, truncation='longest_first', return_tensors="pt",
                               max_length=256)
    input_ids = tokenized["input_ids"]
    attention_mask = tokenized["attention_mask"]
    images = torch.stack(images)
    labels = torch.tensor(labels, dtype=torch.float)

    # for name in tokenized:
    #     tokenized[name] = tokenized[name].to(self._target_device)

    return input_ids, attention_mask, images, labels


class RecdroidDataset(data.Dataset):
    def __init__(self, data_dir: str = "../Temp/current_views"):
        self.transform = transforms.Compose([
            transforms.Resize((256, 256)),
            transforms.CenterCrop(min(244, 256)),
            transforms.ToTensor(),
            transforms.Normalize((0.485, 0.456, 0.406),
                                 (0.229, 0.224, 0.225))])
        self.tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
        self.all_views = {}
        print("load Recdroid data from dir:", data_dir)
        with open(data_dir + "/val_views.tsv", 'r', encoding='utf8', errors="ignore") as fIn1:
            for line in fIn1.readlines():
                view_id, view_str = line.strip().split("\t")
                self.all_views[int(view_id)] = view_str.lower()
        self.all_desc = {}
        with open(data_dir + "/val_desc.tsv", 'r', encoding='utf8') as fIn2:
            for line in fIn2.readlines():
                desc_id, desc_str = line.strip().split("\t")
                self.all_desc[int(desc_id)] = desc_str.lower()
        # df = pd.read_csv(data_dir + "/val_data.csv")
        # self.datas = []
        # for idx, row in df.iterrows():
        #     self.datas.append({"desc_idx": row["desc_idx"], "view_idx": row["view_idx"], "label": row["label"],
        #                        "image": row["image"]})
        self.datas = []
        data_keys = ["desc_idx", "view_idx", "label", "image"]
        data_lines = open(data_dir + "/val_data.csv", "r").readlines()
        for line in data_lines[1:]:
            if len(line.strip()) == 0:
                continue
            cur_items = line.strip().split(",")
            cur_data = {}
            cur_data.setdefault("desc_idx", int(cur_items[0]))
            cur_data.setdefault("view_idx", int(cur_items[1]))
            cur_data.setdefault("label", float(cur_items[2]))
            cur_data.setdefault("image", cur_items[3])
            self.datas.append(cur_data)
        print(self.datas[0])
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self._target_device = torch.device(device)

    def __getitem__(self, index):
        """Returns one data pair (image and caption)."""
        data_info = self.datas[index]
        cur_desc = self.all_desc[data_info["desc_idx"]]
        cur_view = self.all_views[data_info["view_idx"]]
        # tokenize_res = self.tokenizer(cur_desc, cur_view)
        image_path = data_info["image"]
        image = Image.open(image_path).convert('RGB')
        if self.transform is not None:
            image = self.transform(image)
        return cur_desc, cur_view, image

    def __len__(self):
        return len(self.datas)


if __name__ == '__main__':
    dataset = RecdroidDataset()
    # data_loader_train = DataLoader(dataset, batch_size=8, shuffle=True, num_workers=8)
    # data_loader_train.collate_fn = smart_batching_collate
    # # i_batch的多少根据batch size和def __len__(self)返回的长度确定
    # # batch_data返回的值根据def __getitem__(self, index)来确定
    # # 对训练集：(不太清楚enumerate返回什么的时候就多print试试)
    # start_time = time.time()
    # for i_batch, (input_ids, attention_mask, images, labels) in enumerate(data_loader_train):
    #     print(time.time() - start_time)
    #     start_time = time.time()

    # train_samples = []
    # for i in range(20):
    #     train_samples.append(InputExample(texts=["sample_" + str(i), "sample_" + str(i)], label=1))
    # data_loader_train = DataLoader(train_samples, batch_size=3, shuffle=True)
    # data_loader_train.collate_fn = smart_batching_collate
    # for i_batch, batch_data in enumerate(data_loader_train):
    #     print(batch_data)
    #     print(batch_data[0])
    #     print(batch_data[0].texts)

    # test1 = torch.tensor([1,2,3,4])
    # test2 = torch.tensor([1,2,3,4])
    # test3 = [test1, test2]
    # test= torch.stack(test3)
    # print(test.shape)

    # valid_samples = load_valid_samples()
    # for key, data in valid_samples.items():
    #     dataset = ValidDataset(data)
    #     data_loader_train = DataLoader(dataset, batch_size=5, shuffle=False)
    #     for i_batch, batch_data in enumerate(data_loader_train):
    #         # print(batch_data)
    #         # print(type(batch_data[0]))
    #         # print(batch_data[1])
    #         # print(batch_data[2])
    #         if i_batch > 3:
    #             break
