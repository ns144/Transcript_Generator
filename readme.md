## Installation

### Download and install *Python for Windows* (>3.9.5).

Normally, when opening a Command Shell in Windows and typing

>python

it should kick in and install Python via the Windows App Store.

Manually: https://www.python.org/downloads/

### Download and install *Git for Windows*

>winget install --id Git.Git -e --source winget

### Clone the repository via git into a folder 



### Download the current version of FFMPEG and place it in the folder

https://github.com/BtbN/FFmpeg-Builds/releases
You have to place the files ffmpeg.exe AND ffprobe.exe into the folder.

### Setup and activate a virtual environment

>python -m venv env \
>cd env\Scripts \
>activate

### Update PIP to most current version

It is necessary to run pip in the most current version, so 

>python.exe -m pip install --upgrade pip

#### Install dependencies

To install the dependencies use the requirements.txt file by using 

>pip install -r requirements.txt