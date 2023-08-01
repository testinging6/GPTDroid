import pickle
import time
from transformers import AutoModelForSequenceClassification, AutoTokenizer, AutoConfig
import numpy as np
import logging
import os
from typing import Dict, Type, Callable, List
import transformers
import torch
import math
from torch import nn
from torch.optim.optimizer import Optimizer
from torch.utils.data import DataLoader
from tqdm.autonotebook import tqdm, trange
from sentence_transformers import SentenceTransformer, util
from sentence_transformers.evaluation import SentenceEvaluator
from Model.visualCrossEncoder import VisualCrossEncoder
from datetime import datetime
from Model.load_data import ViewMatchDataset, RecdroidDataset
from Model.evaluator import MyCERerankingEvaluator

logger = logging.getLogger(__name__)


class ViewMatcher():
    def __init__(self, checkpoint_dir: str = None):
        if checkpoint_dir == None:
            self.tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
            tokens = ['[type]', '[text]', '[content_desc]', '[hint]', '[resource_id]', '[abs_location]',
                      '[neighbor_text]', '[sibling_text]', '[child_text]', '[parent_text]']
            self.tokenizer.add_tokens(tokens, special_tokens=True)
            self.model = VisualCrossEncoder()
            self.model.distilbert.resize_token_embeddings(len(self.tokenizer))
        else:
            print("load model from dir:", checkpoint_dir)
            self.tokenizer = AutoTokenizer.from_pretrained(checkpoint_dir)
            self.model = VisualCrossEncoder()
            self.model.load(checkpoint_dir)
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self._target_device = torch.device(device)
        self.num_labels = 1
        self.max_length = 256
        self.default_activation_function = nn.Sigmoid()

    def smart_batching_collate(self, batch):
        texts = [[], []]
        images = []
        labels = []

        for example in batch:
            texts[0].append(example[0].strip())
            texts[1].append(example[1].strip())
            images.append(example[2])
            labels.append(example[3])

        tokenized = self.tokenizer(texts[0], texts[1], padding=True, truncation='longest_first', return_tensors="pt",
                                   max_length=self.max_length)
        # input_ids = tokenized["input_ids"].to(self._target_device)
        # attention_mask = tokenized["attention_mask"].to(self._target_device)
        # images = torch.stack(images).to(self._target_device)
        # labels = torch.tensor(labels, dtype=torch.float if self.num_labels == 1 else torch.long).to(self._target_device)
        input_ids = tokenized["input_ids"]
        attention_mask = tokenized["attention_mask"]
        images = torch.stack(images)
        labels = torch.tensor(labels, dtype=torch.float if self.num_labels == 1 else torch.long)
        return input_ids, attention_mask, images, labels

    def smart_batching_collate_text_only(self, batch):
        texts = [[], []]
        images = []

        for example in batch:
            texts[0].append(example[0].strip())
            texts[1].append(example[1].strip())
            images.append(example[2])

        tokenized = self.tokenizer(texts[0], texts[1], padding=True, truncation='longest_first', return_tensors="pt",
                                   max_length=self.max_length)
        # input_ids = tokenized["input_ids"].to(self._target_device)
        # attention_mask = tokenized["attention_mask"].to(self._target_device)
        # images = torch.stack(images).to(self._target_device)
        input_ids = tokenized["input_ids"]
        attention_mask = tokenized["attention_mask"]
        images = torch.stack(images)
        return input_ids, attention_mask, images

    def _eval_during_training(self, evaluator, output_path, save_best_model, epoch, steps, callback):
        """Runs evaluation during the training"""
        if evaluator is not None:
            score = evaluator(self, output_path=output_path, epoch=epoch, steps=steps)
            if callback is not None:
                callback(score, epoch, steps)
            if score > self.best_score:
                self.best_score = score
                if save_best_model:
                    self.model.save(output_path)
                    self.tokenizer.save_pretrained(output_path)

    def fit(self,
            train_dataloader: DataLoader,
            evaluator: SentenceEvaluator = None,
            epochs: int = 1,
            loss_fct=None,
            activation_fct=nn.Identity(),
            scheduler: str = 'WarmupLinear',
            warmup_steps: int = 10000,
            optimizer_class: Type[Optimizer] = transformers.AdamW,
            optimizer_params: Dict[str, object] = {'lr': 2e-5},
            weight_decay: float = 0.01,
            evaluation_steps: int = 0,
            output_path: str = None,
            save_best_model: bool = True,
            max_grad_norm: float = 1,
            use_amp: bool = False,
            callback: Callable[[float, int, int], None] = None,
            ):
        """
        Train the model with the given training objective
        Each training objective is sampled in turn for one batch.
        We sample only as many batches from each objective as there are in the smallest one
        to make sure of equal training with each dataset.

        :param train_dataloader: DataLoader with training InputExamples
        :param evaluator: An evaluator (sentence_transformers.evaluation) evaluates the model performance during training on held-out dev data. It is used to determine the best model that is saved to disc.
        :param epochs: Number of epochs for training
        :param loss_fct: Which loss function to use for training. If None, will use nn.BCEWithLogitsLoss() if self.config.num_labels == 1 else nn.CrossEntropyLoss()
        :param activation_fct: Activation function applied on top of logits output of model.
        :param scheduler: Learning rate scheduler. Available schedulers: constantlr, warmupconstant, warmuplinear, warmupcosine, warmupcosinewithhardrestarts
        :param warmup_steps: Behavior depends on the scheduler. For WarmupLinear (default), the learning rate is increased from o up to the maximal learning rate. After these many training steps, the learning rate is decreased linearly back to zero.
        :param optimizer_class: Optimizer
        :param optimizer_params: Optimizer parameters
        :param weight_decay: Weight decay for model parameters
        :param evaluation_steps: If > 0, evaluate the model using evaluator after each number of training steps
        :param output_path: Storage path for the model and evaluation files
        :param save_best_model: If true, the best model (according to evaluator) is stored at output_path
        :param max_grad_norm: Used for gradient normalization.
        :param use_amp: Use Automatic Mixed Precision (AMP). Only for Pytorch >= 1.6.0
        :param callback: Callback function that is invoked after each evaluation.
                It must accept the following three parameters in this order:
                `score`, `epoch`, `steps`
        """
        train_dataloader.collate_fn = self.smart_batching_collate
        self.model.to(self._target_device)

        if output_path is not None:
            os.makedirs(output_path, exist_ok=True)

        self.best_score = -9999999
        num_train_steps = int(len(train_dataloader) * epochs)

        # Prepare optimizers
        param_optimizer = list(self.model.named_parameters())

        no_decay = ['bias', 'LayerNorm.bias', 'LayerNorm.weight']
        optimizer_grouped_parameters = [
            {'params': [p for n, p in param_optimizer if not any(nd in n for nd in no_decay)],
             'weight_decay': weight_decay},
            {'params': [p for n, p in param_optimizer if any(nd in n for nd in no_decay)], 'weight_decay': 0.0}
        ]

        optimizer = optimizer_class(optimizer_grouped_parameters, **optimizer_params)

        if isinstance(scheduler, str):
            scheduler = SentenceTransformer._get_scheduler(optimizer, scheduler=scheduler, warmup_steps=warmup_steps,
                                                           t_total=num_train_steps)

        if loss_fct is None:
            loss_fct = nn.BCEWithLogitsLoss() if self.num_labels == 1 else nn.CrossEntropyLoss()

        skip_scheduler = False
        for epoch in trange(epochs, desc="Epoch"):
            training_steps = 0
            self.model.zero_grad()
            self.model.train()

            for (input_ids, attention_mask, images, labels) in tqdm(train_dataloader, desc="Iteration", smoothing=0.05):
                input_ids = input_ids.to(self._target_device)
                attention_mask = attention_mask.to(self._target_device)
                images = images.to(self._target_device)
                labels = labels.to(self._target_device)
                model_predictions = self.model(input_ids=input_ids, attention_mask=attention_mask, images=images,
                                               return_dict=True)
                logits = activation_fct(model_predictions)
                if self.num_labels == 1:
                    logits = logits.view(-1)
                loss_value = loss_fct(logits, labels)
                loss_value.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_grad_norm)
                optimizer.step()

                optimizer.zero_grad()

                if not skip_scheduler:
                    scheduler.step()

                training_steps += 1

                if evaluator is not None and evaluation_steps > 0 and training_steps % evaluation_steps == 0:
                    self._eval_during_training(evaluator, output_path, save_best_model, epoch, training_steps, callback)

                    self.model.zero_grad()
                    self.model.train()

            if evaluator is not None:
                self._eval_during_training(evaluator, output_path, save_best_model, epoch, -1, callback)

    def predict(self, sentences: torch.utils.data.Dataset,
                batch_size: int = 16,
                show_progress_bar: bool = None,
                num_workers: int = 8,
                activation_fct=None,
                apply_softmax=False,
                convert_to_numpy: bool = True,
                convert_to_tensor: bool = False
                ):
        """
        Performs predicts with the CrossEncoder on the given sentence pairs.

        :param sentences: A list of sentence pairs [[Sent1, Sent2], [Sent3, Sent4]]
        :param batch_size: Batch size for encoding
        :param show_progress_bar: Output progress bar
        :param num_workers: Number of workers for tokenization
        :param activation_fct: Activation function applied on the logits output of the CrossEncoder. If None, nn.Sigmoid() will be used if num_labels=1, else nn.Identity
        :param convert_to_numpy: Convert the output to a numpy matrix.
        :param apply_softmax: If there are more than 2 dimensions and apply_softmax=True, applies softmax on the logits output
        :param convert_to_tensor:  Conver the output to a tensor.
        :return: Predictions for the passed sentence pairs
        """
        input_was_string = False
        if isinstance(sentences[0], str):  # Cast an individual sentence to a list with length 1
            sentences = [sentences]
            input_was_string = True

        inp_dataloader = DataLoader(sentences, batch_size=batch_size, collate_fn=self.smart_batching_collate_text_only,
                                    num_workers=num_workers, shuffle=False)

        if show_progress_bar is None:
            show_progress_bar = (
                    logger.getEffectiveLevel() == logging.INFO or logger.getEffectiveLevel() == logging.DEBUG)

        iterator = inp_dataloader
        if show_progress_bar:
            iterator = tqdm(inp_dataloader, desc="Batches")

        if activation_fct is None:
            activation_fct = self.default_activation_function

        pred_scores = []
        self.model.eval()
        self.model.to(self._target_device)
        with torch.no_grad():
            for (input_ids, attention_mask, images) in iterator:
                input_ids = input_ids.to(self._target_device)
                attention_mask = attention_mask.to(self._target_device)
                images = images.to(self._target_device)
                model_predictions = self.model(input_ids=input_ids, attention_mask=attention_mask, images=images,
                                               return_dict=True)
                logits = activation_fct(model_predictions)

                if apply_softmax and len(logits[0]) > 1:
                    logits = torch.nn.functional.softmax(logits, dim=1)
                # print(logits)
                pred_scores.extend(logits)

        if self.num_labels == 1:
            pred_scores = [score[0] for score in pred_scores]

        if convert_to_tensor:
            pred_scores = torch.stack(pred_scores)
        elif convert_to_numpy:
            pred_scores = np.asarray([score.cpu().detach().numpy() for score in pred_scores])

        if input_was_string:
            pred_scores = pred_scores[0]
        return pred_scores

    def run(self):
        train_batch_size = 16
        num_epochs = 2
        model_save_path = 'out/training_stsbenchmark-' + datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        train_samples = ViewMatchDataset()
        # We wrap train_samples (which is a List[InputExample]) into a pytorch DataLoader
        train_dataloader = DataLoader(train_samples, shuffle=True, batch_size=train_batch_size, num_workers=8)
        # We add an evaluator, which evaluates the performance during training
        evaluator = MyCERerankingEvaluator(name='train-eval')
        # Configure the training
        warmup_steps = math.ceil(len(train_dataloader) * num_epochs * 0.1)  # 10% of train data for warm-up
        logger.info("Warmup-steps: {}".format(warmup_steps))

        # Train the model
        self.fit(train_dataloader=train_dataloader,
                 evaluator=evaluator,
                 epochs=num_epochs,
                 warmup_steps=warmup_steps,
                 evaluation_steps=50000,
                 output_path=model_save_path)

    def predict_on_recdroid_all(self):
        recdroid_dir = "recdroid_view"
        res = {}
        for apk_dir in os.listdir(recdroid_dir):
            data_dir = os.path.join(recdroid_dir, apk_dir)
            print("run on dir:", data_dir)
            cur_dataset = RecdroidDataset(data_dir)
            cur_scores = self.predict(cur_dataset, convert_to_numpy=True, num_workers=0)
            print(cur_scores.shape)
            res.setdefault(apk_dir, cur_scores)
        save_pkl = open("recdroid_score.pkl", "wb")
        pickle.dump(res, save_pkl)

        # data_dir = "recdroid_view/1.newsblur_s"
        # print("run on dir:", data_dir)
        # cur_dataset = RecdroidDataset(data_dir)
        # cur_scores = self.predict(cur_dataset, convert_to_numpy=True)

    def predict_on_recdroid(self, data_dir):
        print("run on dir:", data_dir)
        start_time = time.time()
        cur_dataset = RecdroidDataset(data_dir)
        print("load data time:", time.time()-start_time)
        start_time = time.time()
        cur_scores = self.predict(cur_dataset, convert_to_numpy=True, num_workers=0)
        print("predict time:", time.time() - start_time)
        return cur_scores

        # print(cur_scores.shape)
        # res.setdefault(data_dir, cur_scores)
        # save_pkl = open("recdroid_score.pkl", "wb")
        # pickle.dump(res, save_pkl)

        # data_dir = "recdroid_view/1.newsblur_s"
        # print("run on dir:", data_dir)
        # cur_dataset = RecdroidDataset(data_dir)
        # cur_scores = self.predict(cur_dataset, convert_to_numpy=True)


if __name__ == '__main__':
    # train_obj = ViewMatcher()
    # train_obj.run()

    predict_obj = ViewMatcher("out/training_stsbenchmark-2022-03-14_09-38-31")
    predict_obj.predict_on_recdroid_all()
    predict_obj.predict_on_recdroid("test data")
