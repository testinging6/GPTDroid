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



We give experiment dataset (./Effectiveness evaluation; ./Usefulness evaluation/)

## Effectiveness evaluation (./Effectiveness evaluation/)
The experimental dataset for effectiveness evaluation 

The first is the apks from effectiveness evaluation, which contains 66 + 20 (20 from Themis benchmark) apps, the 66 apps information as shown in table.

The 20 apps from Themis benchmark，you can find in the Themis benchmark.

Because the storage space of GitHub is limited to 2GB, and Google Play requires that individuals cannot upload apk without permission. You can download them on Google play through the information in the table.


**ID** | **App name**  | **Category** | **Download** |
 :-: | :-: | :-: | :-: 
1 | American Air | travel | 10M+
2 | Librera Reader  | book | 10M+
3 | Trip  | travel | 10M+
4 | Photo Albums | photography | 10M+
5 | Expedia  | travel | 10M+
6 | Trainline  | travel | 10M+
7 | neutriNote  | Productivity | 10M+
8 | OsmAnd  | Navigation | 5M+
9 | Gallery Pro  | photography | 1M+
10 | MPlayer  | music | 1M+
11 | MyExp  | Finance | 1M+
12 | MyTransit  | maps | 1M+
13 | Kkday  | travel | 1M+
14 | Status  | Finance | 1M+
15 | Moonlight  | Game | 1M+
16 | Game Collection  | Game | 500K+
17 | SMS  | System | 500K+
18 | AndBible | books | 500K+
19 | Homegate  | travel | 500K+
20 | Element  | social | 500K+
21 | LoL Builds | Game | 500K+
22 | VoiceRecorder | System| 500K+
23 | Web Opac | education | 100K+
24 | List planner  | System | 100K+
25 | Stopwatch  | System | 100K+
26 | Infinity Reddit | social | 100K+
27 | Kinoko | Tool | 100K+
28 | GAMEYE  | Game | 100K+
29 | Tutanota | Productivity | 100K+
30 | Markor  | Productivity | 100K+
31 | SBW  | Finance | 100K+
32 | openHAB  | Internet | 100K+
33 | Collins Dictionary  | education | 100K+
34 | NewPipe | Multimedia | 100K+
35 | Odysee  | video | 100K+
36 | Crypto Widget | Finance | 100K+
37 | MHWorld  | Game | 100K+
38 | Mule  | entertainment | 100K+
39 | Tasks  | writing | 100K+
40 | Airline Ticket | travel | 100K+
41 | Mumla | communication | 100K+
42 | Vespucci  | maps | 100K+
43 | Stash  | Game | 100K+
44 | Retro  | Game | 100K+
45 | Shader Editor | Tool | 100K+
46 | StreetComplete | navigation | 100K+
47 | Invoice Ninja | Business | 100K+
48 | GitNex  | productivity | 100K+
49 | BitAC  | Finance | 100K+
50 | Migraine Log  | health | 100K+
51 | FHCode  | Tool | 100K+
52 | CTU Menza | food | 100K+
53 | Podverse  | music | 100K+
54 | OpenTracks | health | 50K+
55 | Kotatsu  | Tool | 50K+
56 | Converter  | education | 50K+
57 | Watermark  | Tool | 50K+
58 | Romania  | music  | 50K+
59 | Radio Romania  | music | 50K+
60 | Petals | health  | 50K+
61 | Money Tracker  | Finance | 50K+
63 | Antispam | Productivity | 50K+
64 | Droid-ify | System | 50K+
65 | Unstoppable   | Finance | 50K+
66 | Funkwhale | music | 50K+

## Usefulness evaluation (./Usefulness evaluation/)

The second is the apks confirmed or fixed from usefulness evaluation, the app information as shown in table.

Because the storage space of GitHub is limited to 2GB, and Google Play requires that individuals cannot upload apk without permission. You can download them on Google play through the information in the table.

**ID** | **App name** | **Category** | **Download** | **Status**
 :-: | :-: | :-: | :-: | :-: 
1 | PerfectPia | Music | 50M+ |  confirmed
2 | MusicPlayer | Music | 50M+ |  confirmed
3 | NoxSecu | Tool  | 10M+ | fixed
4 | Degoo| Tool | 10M+ | fixed
5 | Proxy | Tool | 10M+ |  confirmed
6 | Secure | Tool | 10M+  |  confirmed
7 | Thunder | Tool | 10M+  |  confirmed
8 | ApowerMir | Tool | 5M+  |  confirmed
9 | MediaFire | Product | 5M+  |  confirmed
10 | Postegro | Commun | 500K+ | fixed
11 | Deezer MP | Music | 500K+ | fixed
12 | MTG | Utilities | 500K+ | fixed
13 | OFF | Health | 500K+  |  confirmed
14 | Yucata | Tool | 500K+   |  confirmed
15 | ClassySha | Tool | 500K+   |  confirmed
16 | Linphone | Commun | 500K+   |  confirmed
17 | Paytm | Finance | 100K+  |  confirmed
18 | Transdroid | Tool | 100K+   |  confirmed
19 | Transistor | Music  | 10K+  | fixed
20 | Onkyo | Music  | 10K+  | fixed
21 | Democracy | News  | 10K+  |  confirmed
22 | NewPipe  | Media  | 10K+   |  confirmed
23 | LessPass | Product  | 10K+  |  confirmed
24 | CEToolbox |  Medical  | 10K+   |  confirmed
25 | OSM  | Health  | 10K+  |  confirmed
26 | AlarmClock | System | 1M+  |  pending
27 | AnotherMonitor | System | 1M+ |  pending
28 | Syncthing | Internet | 1M+  |  pending
29 | J2MELoader | Game | 1M+  |  pending
30 | Acrtions | Health | 1M+ |  pending
31 | Goodtime |Time | 500K+ |  pending
32 | PDFConverter | Media | 100K+ |  pending
33 | AppInt | Plugin |100K+ |  pending
34 | Commons | Internet | 50K+ |  pending
35 | Birday | Internet | 50K+ |  pending
36 | Openboard | System | 50K+ |  pending
37 | EVMap | Navig | 10K+ |  pending
38 | Hendroid | Reading | 10K+ |  pending
39 | Minesweep | Games | 10K+ |  pending
40 | Democracy | Media | 10K+ |  pending
41 | Easer | System | 10K+ |  pending
42 | AutoClicker | System | 10K+ |  pending
43 | Watomatic | Internet | 10K+ |  pending
44 | ChessClock | Games | 10K+ |  pending
45 | Look4Sat | Science | 10K+ |  pending
46 | Forecastie | Science | 10K+ |  pending
47 | Frost | Media | 10K+ |  pending
48 | PicardScanner | Media | 10K+ |  pending

