# GPTDroid

We propose GPTDroid, asking LLM to chat with the mobile apps by passing the GUI page information to LLM to elicit testing scripts, and executing them to keep passing the app feedback to LLM, iterating the whole process. 

GPTDroid demo video

![Demo video](https://github.com/testinging6/GPTDroid/blob/main/GPTDroid-demo.gif) 

We provide demo video as shown in below video for helping the understanding. The video link is: https://youtu.be/xvPURrLIr_w


We give source code (./GPTDroid/)

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

Use the gpt-3 as follows.

1.We recommend using our OpenAI command-line interface (CLI). To install this, run
`pip install --upgrade openai`

2.(The following instructions work for version 0.9.4 and up. Additionally, the OpenAI CLI requires python 3.)

Set your OPENAI_API_KEY environment variable by adding the following line into your shell initialization script (e.g. .bashrc, zshrc, etc.) or running it in the command line:

`export OPENAI_API_KEY="<OPENAI_API_KEY>"`
  
 `
import openai
openai.Completion.create(
    model=MODEL,
    prompt=YOUR_PROMPT)`

Since the API of gpt-3 contains personal information, we will give our API key after the double-blind review. You can also use your personal API key.

