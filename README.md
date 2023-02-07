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

Use the gpt-3 as follows, and the effect is the same.

1.We recommend using our OpenAI command-line interface (CLI). To install this, run
`pip install --upgrade openai`

2.(The following instructions work for version 0.9.4 and up. Additionally, the OpenAI CLI requires python 3.)

Set your OPENAI_API_KEY environment variable by adding the following line into your shell initialization script (e.g. .bashrc, zshrc, etc.) or running it in the command line:

`export OPENAI_API_KEY="<OPENAI_API_KEY>"`
  
 `
import openai
openai.Completion.create(
    model=FINE_TUNED_MODEL,
    prompt=YOUR_PROMPT)`

Since the API of gpt-3 contains personal information, we will give our API key after the double-blind review.



We give experiment dataset (./Effectiveness evaluation; ./Usefulness evaluation/)

## Effectiveness evaluation (./Effectiveness evaluation/)
The experimental dataset for effectiveness evaluation 

The first is the apks from effectiveness evaluation, which contains 66 + 20 (20 from Themis benchmark) apps, the 66 apps information as shown in table.

The 20 apps from Themis benchmark，you can find in the Themis benchmark.

Because the storage space of GitHub is limited to 2GB, and Google Play requires that individuals cannot upload apk without permission. You can download them on Google play through the information in the table.


**ID** | **Version** | **Category** | **Download** |
 :-: | :-: | :-: | :-: 
1 | American Air | 16.2 | travel | 10M+
2 | Librera Reader | 8.5.21 | book | 10M+
3 | Trip | 7.56.3 | travel | 10M+
4 | Photo Albums | 5.3.10 | photography | 10M+
5 | Expedia | 22.26.0 | travel | 10M+
6 | Trainline | 211.0.0 | travel | 10M+
7 | neutriNote | 4.1.7 | Productivity | 10M+
8 | OsmAnd | 4.2.6  | Navigation | 5M+
9 | Gallery Pro | 6.23.12 | photography | 1M+
10 | MPlayer | 5.12.0 | music | 1M+
11 | MyExp | 3.4.1 | Finance | 1M+
12 | MyTransit | 3.12.5.14 | maps | 1M+
13 | Kkday | 2.21.0 | travel | 1M+
14 | Status | 1.19. | Finance | 1M+
15 | Moonlight | 10.5 | Game | 1M+
16 | Game Collection | 12.3 | Game | 500K+
17 | SMS | 5.14.4  | System | 500K+
18 | AndBible | 4.0.649 | books | 500K+
19 | Homegate | 12.8.2 | travel | 500K+
20 | Element | 1.4.25 | social | 500K+
21 | LoL Builds | 1.3.1 | Game | 500K+
22 | VoiceRecorder | 5.8.2 | System| 500K+
23 | Web Opac | 6.4.6 | education | 100K+
24 | List planner | 6.12.3 | System | 100K+
25 | Stopwatch | 5.8.1 | System | 100K+
26 | Infinity Reddit | 5.2.1 | social | 100K+
27 | Kinoko | 4.3.2 | Tool | 100K+
28 | GAMEYE | 4.16.10 | Game | 100K+
29 | Tutanota | 3.98.4 | Productivity | 100K+
30 | Markor | 2.9.0 | Productivity | 100K+
31 | SBW | 2.4.27 | Finance | 100K+
32 | openHAB | 2.20.15 | Internet | 100K+
33 | Collins Dictionary | 1.4.5 | education | 100K+
34 | NewPipe | 0.23.1 | Multimedia | 100K+
35 | Odysee | 0.0.53 | video | 100K+
36 | Crypto Widget |  8.2.4 | Finance | 100K+
37 | MHWorld |  2.1.1 | Game | 100K+
38 | Mule | 34 | entertainment | 100K+
39 | Tasks | 12.7 | writing | 100K+
40 | Airline Ticket | 4.4 | travel | 100K+
41 | Mumla | 3.6.3 | communication | 100K+
42 | Vespucci | 17.1.3.0  | maps | 100K+
43 | Stash | 1.27.1 | Game | 100K+
44 | Retro | 1.2.68 | Game | 100K+
45 | Shader Editor |  2.24.0 | Tool | 100K+
46 | StreetComplete | 45 | navigation | 100K+
47 | Invoice Ninja | 5.0.87 | Business | 100K+
48 | GitNex | 4.4.0 | productivity | 100K+
49 | BitAC | 1.1.2 | Finance | 100K+
50 | Migraine Log | 0.8.1 | health | 100K+
51 | FHCode | 1.1 | Tool | 100K+
52 | CTU Menza | 1.2.0 | food | 100K+
53 | Podverse | 4.5.11 | music | 100K+
54 | OpenTracks | 4.0.3 | health | 50K+
55 | Kotatsu | 3.3.2 | Tool | 50K+
56 | Converter  | 3.1.2 | education | 50K+
57 | Watermark | 2.8.2  | Tool | 50K+
58 | Romania | 2.5.2 | music  | 50K+
59 | Radio Romania | 2.5.2 | music | 50K+
60 | Petals | 2.5.0 | health  | 50K+
61 | Money Tracker | 2.1.5 | Finance | 50K+
63 | Antispam | 1.15.1 | Productivity | 50K+
64 | Droid-ify | 0.4.5 | System | 50K+
65 | Unstoppable  | 0.25.3 | Finance | 50K+
66 | Funkwhale |  0.1.5 | music | 50K+

## Usefulness evaluation (./Usefulness evaluation/)

The second is the apks confirmed or fixed from usefulness evaluation, the app information as shown in table.

Because the storage space of GitHub is limited to 2GB, and Google Play requires that individuals cannot upload apk without permission. You can download them on Google play through the information in the table.

**ID** | **Version** | **Category** | **Download** | **Status**
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
48 | PicardScanner | Media & | 10K+ |  pending

