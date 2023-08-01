import torch
from torch import nn
from transformers import AutoModel
import logging
import os
import torchvision
from Model.load_data import ViewMatchDataset, smart_batching_collate
from torch.utils.data import DataLoader

logger = logging.getLogger(__name__)


class VisualCrossEncoder(nn.Module):

    def __init__(self, load_path: str = None, image_encoder_hidden: int = 256):
        super(VisualCrossEncoder, self).__init__()
        if load_path == None:
            self.distilbert = AutoModel.from_pretrained("distilbert-base-uncased")
        else:
            self.distilbert = AutoModel.from_pretrained(load_path)
        self.num_labels = 1
        self.pre_classifier = nn.Linear(768, 768)
        self.image_encoder = EncoderCNN(image_encoder_hidden)
        self.classifier = nn.Linear(768 + image_encoder_hidden, self.num_labels)
        self.dropout = nn.Dropout(0.2)
        # device = "cuda" if torch.cuda.is_available() else "cpu"
        # logger.info("Use pytorch device: {}".format(device))
        # self._target_device = torch.device(device)

    def forward(self, input_ids=None, attention_mask=None, head_mask=None, inputs_embeds=None,
                output_attentions=None, output_hidden_states=None, images=None, return_dict=None):
        distilbert_output = self.distilbert(input_ids=input_ids,
                                            attention_mask=attention_mask,
                                            head_mask=head_mask,
                                            inputs_embeds=inputs_embeds,
                                            output_attentions=output_attentions,
                                            output_hidden_states=output_hidden_states,
                                            return_dict=return_dict)
        image_feature = self.image_encoder(images) # (bs, image_encoder_hidden)
        hidden_state = distilbert_output[0]  # (bs, seq_len, dim)
        # print(hidden_state.shape)
        pooled_output = hidden_state[:, 0]  # (bs, dim)
        pooled_output = self.pre_classifier(pooled_output)  # (bs, dim)
        pooled_output = nn.ReLU()(pooled_output)  # (bs, dim)
        pooled_output = self.dropout(pooled_output)  # (bs, dim)
        fuze_feature = torch.cat([pooled_output, image_feature], dim=1)
        # logits = self.classifier(pooled_output)  # (bs, num_labels)
        logits = self.classifier(fuze_feature)  # (bs, num_labels)
        return logits

    def save(self, save_dir):
        self.distilbert.save_pretrained(save_dir)
        torch.save(self.pre_classifier.state_dict(), os.path.join(save_dir, "pre_classifier.pt"))
        torch.save(self.classifier.state_dict(), os.path.join(save_dir, "classifier.pt"))
        torch.save(self.image_encoder.state_dict(), os.path.join(save_dir, "image_encoder.pt"))

    def load(self, save_dir):
        self.distilbert = AutoModel.from_pretrained(save_dir)
        self.pre_classifier.load_state_dict(torch.load(os.path.join(save_dir, "pre_classifier.pt")))
        self.classifier.load_state_dict(torch.load(os.path.join(save_dir, "classifier.pt")))
        self.image_encoder.load_state_dict(torch.load(os.path.join(save_dir, "image_encoder.pt")))


class EncoderCNN(nn.Module):
    def __init__(self, hidden_size):
        """Load the pretrained ResNet and replace top fc layer."""
        super(EncoderCNN, self).__init__()
        self.hidden_size = hidden_size
        resnet = torchvision.models.resnet18(pretrained=True)
        num_ftrs = resnet.fc.in_features
        resnet.fc = nn.Linear(num_ftrs, 98)
        resnet.load_state_dict(torch.load("../Model/out/models/icon_image_classifier.pkl", map_location='cuda:0'))
        resnet.fc = nn.Linear(num_ftrs, 256)
        self.resnet = resnet
        self.linear = nn.Linear(256, self.hidden_size)
        self.bn = nn.BatchNorm1d(self.hidden_size, momentum=0.01)

    def forward(self, images):
        """Extract feature vectors from input images."""
        with torch.no_grad():
            features = self.resnet(images)
        features = features.reshape(features.size(0), -1)
        features = self.bn(self.linear(features))
        return features

if __name__ == '__main__':
    model = VisualCrossEncoder()
    print(model)
    save_dir = "test"
    # model.save(save_dir)
    # model.load(save_dir)
    dataset = ViewMatchDataset()
    print("get dataset finish")
    data_loader_train = DataLoader(dataset, batch_size=5, shuffle=True, num_workers=4)
    data_loader_train.collate_fn = smart_batching_collate
    # i_batch的多少根据batch size和def __len__(self)返回的长度确定
    # batch_data返回的值根据def __getitem__(self, index)来确定
    # 对训练集：(不太清楚enumerate返回什么的时候就多print试试)
    for i_batch, (input_ids, attention_mask, images, labels) in enumerate(data_loader_train):
        print("input:", input_ids.shape, images.shape, attention_mask.shape)
        image_features = model(input_ids=input_ids, attention_mask=attention_mask, images=images)
        print("output:", image_features.shape)
        if i_batch > 10:
            break