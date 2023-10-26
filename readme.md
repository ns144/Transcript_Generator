# Transcript Generator

## Installation

### Download and install _Python for Windows_ (>3.9.5).

Normally, when opening a Command Shell in Windows and typing

> python

it should kick in and install Python via the Windows App Store.

Manually: https://www.python.org/downloads/

### Download and install _Git for Windows_

> winget install --id Git.Git -e --source winget

### Clone the repository via git into a folder

### Run the install.bat file

This will install the required dependencies.

### Initial use

When running the Transcript Generator for the first time you need to launch it with admin privileges to download the pretrained model from huggingface for the speaker diarization.

### UI

![Showcase of the User Interface](ui.png)

After adding files to the queue you can select whether you want to generate a DOCX file as well or just a SRT File.
To use the translation feature you will need to enter a Deepl API key.
