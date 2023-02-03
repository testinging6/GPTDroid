# GPTDroid

We propose GPTDroid, asking LLM to chat with the mobile apps by passing the GUI page information to LLM to elicit testing scripts, and executing them to keep passing the app feedback to LLM, iterating the whole process. 

GPTDroid demo video

![Demo video](https://github.com/testinging6/GPTDroid/blob/main/GPTDroid-demo.gif) 

We provide demo video as shown in below video for helping the understanding. The video link is: https://youtu.be/xvPURrLIr_w


We give source code (./source code/)

You can get the code through our source-code.

#### Requirements
* Android emulator
* Ubuntu or Windows
* Appium Desktop Client: [link](https://github.com/appium/appium-desktop/releases/tag/v1.22.3-4)
* Python 3.7
  * apkutils==0.10.2
  * Appium-Python-Client==1.3.0
  * Levenshtein==0.18.1
  * lxml==4.8.0
  * opencv-python==4.5.5.64
  * sentence-transformers==1.0.3
  * torch==1.6.0
  * torchvision==0.7.0

Fine tune your gpt-3 as follows, and the effect is the same.

1.We recommend using our OpenAI command-line interface (CLI). To install this, run
`pip install --upgrade openai`

2.(The following instructions work for version 0.9.4 and up. Additionally, the OpenAI CLI requires python 3.)

Set your OPENAI_API_KEY environment variable by adding the following line into your shell initialization script (e.g. .bashrc, zshrc, etc.) or running it in the command line before the fine-tuning command:

`export OPENAI_API_KEY="<OPENAI_API_KEY>"`

3.Prepare training data

Training data is how you teach GPT-3 what you'd like it to say.
Your data must be a JSONL document, where each line is a prompt-completion pair corresponding to a training example. You can use CLI data preparation tool to easily convert your data into this file format.

`{"prompt": "<prompt text>", "completion": "<ideal generated text>"}`

4. CLI data preparation tool
We developed a tool which validates, gives suggestions and reformats your data:

`openai tools fine_tunes.prepare_data -f <LOCAL_FILE>`

5. Create a fine-tuned model

`openai api fine_tunes.create -t <TRAIN_FILE_ID_OR_PATH> -m Curie`

6. After you've started a fine-tune job, it may take some time to complete. Your job may be queued behind other jobs on our system, and training our model can take minutes or hours depending on the model and dataset size. If the event stream is interrupted for any reason, you can resume it by running:

`openai api fine_tunes.follow -i <YOUR_FINE_TUNE_JOB_ID>`

7. Use a fine-tuned model

`openai api completions.create -m <FINE_TUNED_MODEL> -p <YOUR_PROMPT>`

`curl https://api.openai.com/v1/completions \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"prompt": YOUR_PROMPT, "model": FINE_TUNED_MODEL}'`
  
 `
import openai
openai.Completion.create(
    model=FINE_TUNED_MODEL,
    prompt=YOUR_PROMPT)`

Since the API of gpt-3 contains personal information, we will give our fine tuned API after the double-blind review.
