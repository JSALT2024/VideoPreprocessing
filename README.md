# Video preprocessing of YouTubeASL and H2S dataset

The repository of code utilized for the preprocessing of [YoutubeASL](https://arxiv.org/abs/2306.15162) dataset for SignLLaVA team at [JSALT 2024](https://www.clsp.jhu.edu/2024-tenth-jelinek-summer-workshop-on-speech-and-language-technology-schedule/) workshop.

## Repository Structure
<pre>
├── README.md                     # Description  
├── .gitignore                    # .gitignore file  
├── requirements.txt              # requirements file  
├── Trim_h2s/                     # Files for the How2Sign dataset trimming  
│   ├── csv_prep.py               # Script for the restructuralization of the original H2S metadata csv  
│   ├── script_trim.py            # Main How2Sign trim script  
│   ├── exec_trim.py              # Shell script to execute script_trim.py with PBS  
│   └── divide.py                 # Script to divide the metadata file  
├── Trim_yasl/                    # Files for the YouTubeASL dataset trimming  
│   ├── csv_prep.py               # Script for the restructuralization of the original YASL metadata csv  
│   ├── script_trim.py            # Main YASL trim script  
│   ├── exec_trim.py              # Shell script to execute script_trim.py with PBS  
│   └── vtt_sample.vtt            # A subtitle .vtt sample source file  
├── OCR/                          # Files for the Optical Character Recognition and inpaint of detected text in videos  
│   ├── ocr_script.py             # Main OCR script  
│   ├── ocr_pytesseract.py        # OCR test script using pytesseract library  
│   ├── ocr_script_local.py       # OCR script to run on a local machine for testing  
│   ├── processed_log_sample.csv  # Sample file with clip names and identifier if processed  
│   └── execute_ocr.sh            # Shell script to execute ocr_script.py with PBS  
├── transcribe_by_ocr/            # Files for the video subtitles transcription  
│   ├── ocr_transcribe.py         # Script for transcription of embedded subtitles in the video to a .csv file  
└───└── transcribed_sample.csv    # A sample of the output before post-processing  
</pre>

## Execution
Install package dependencies:

```
pip install -r requirements.txt
```

### How2Sign dataset trimming
- Execute _csv_prep.py_ with dataset metadata file expected as an input, outputs restructuralized .csv metadata file with 2 lines for given video clips, first line is a list of end and start frames for each clip, second line is a list of clip names.
- Execute _script_trim.py_ with _exec_trim.sh_ expecting path to the input videos, output logfile !metadata.csv path and path to the output clip folder. Parameters are described in the ArgumentParser.
- Trimmed clips are saved in the output clip folder.

### YouTubeASL dataset trimming
- Execute _csv_prep.py_ with dataset metadata file expected as an input, outputs restructuralized .csv metadata file with 1 line including end and start frame for each video clip.
- Execute _script_trim.py_ with _exec_trim.sh_ expecting path to the input videos and .vtt files in the same folder paired by names, output logfile !metadata.csv path and path to the output clip folder. Parameters are described in the ArgumentParser.
- Note that the input folder should include 2 files for each video.
    - the video file itself in .mp4 or .webm
    - the .vtt file with subtitle annotation and timeframes
- Trimmed clips are saved in the output clip folder.

### Video Optical Character Recognition
- Execute _ocr_script.py with _execute_ocr.sh_ expecting:
    - variable filenames as an output log file including information about clips to process and which files were already processed and which were not, the file should be prepared beforehand. See the sample format in the processed_log_sample.csv file. The default identifier is 0, identifier 1 marks processed clips, identifier 2 marks clips that were not found in the input directory, identifier 3 marks clips that were already found in the output directory and identifier 4 marks clips that were not readable.  
    - variable logfile as an output logfile  
    - variable input as a directory for the input videos  
    - variable output as a directory for the processed videos  
- Apply similar prerequisites for the scripts _ocr_pytesseract.py_ and _ocr_script_local.py_ with minor changes in paths and output log files (see in the scripts).  

### Optical Character Recognition embedded video subtitles transcription tool
- Execute _ocr_transcribe.py_ with the .mp4 video path with embedded subtitles as an input in the variable video_path.  
- Set up the subtitles region coordinates at lines 15-16.  
- See the .csv output in the csv_path variable directory.  
