from pathlib import Path
from configparser import ConfigParser
import subprocess
import whisper
from whisper.utils import get_writer
from transcribe_helper import condenseSegments
from transcribe_helper import translateSegments
from script_helper import transcriptToDoc 
from script_helper import speakersToDoc
from speaker_segment import speaker_segment
from speaker_segment import transcribed_segment
import torch
import os
from pyannote.audio import Pipeline
import copy
from pydub import AudioSegment
import numpy as np

# Function to create the transcription
def generate_transcript(sourcefile:str, lang='en', complex=False, createDOCX=False, speakerDiarization=False, num_speakers=2, write_srt=False, translate=False, translateTargetLanguage="de", deeplKey=""):
    
    # Check if a CUDA capable GPU is available
    # This will improve the performance significantly
    print("GPU: " + str(torch.cuda.is_available()))
    print("Torch version:" + str(torch.__version__))

    path = Path(sourcefile)

    # speaker diarization = seperation of the audio in speaker segments
    if speakerDiarization:
        print("SPEAKER DIARIZATION")
        # convert the input file to a wav file
        # additionally a normalization of the file is performed this will improve the transcription and the speaker diarization
        subprocess.call(['ffmpeg', '-i', sourcefile,"-filter:a", "loudnorm=I=-20:LRA=4","-ac", "1","-ar","48000", 'audio.wav', '-y', '-loglevel', "quiet"])
        sourcefile_norm = 'audio.wav'

        # run speaker diarization
        speaker_segments = speaker_diarization(sourcefile_norm)
        # speaker parts are combined where multiple segments of a speaker are not interrupted by another speaker 
        speaker_segments = condenseSpeakers(speaker_segments)
        # transcription of the condensed segments
        transcribed_segments = render_segments(sourcefile_norm, speaker_segments, lang)

        # save SRT file
        targetfile = path.with_suffix('.srt')
        name = targetfile.name
        directory = targetfile.parent
        print("Saving SRT: " + str(targetfile))
        translated_segments = copy.deepcopy(transcribed_segments)

        srt_segments = []
        # check if translation is required
        if translate:
            # translation 
            translated_segments = translateSegments(translated_segments, translateTargetLanguage=translateTargetLanguage, deeplKey=deeplKey)
            for segment in translated_segments:
                for s in segment.segments:
                    srt_segments.append(s)
        else:
            for segment in transcribed_segments:
                for s in segment.segments:
                    srt_segments.append(s)


        segments_as_dict = dict()
        segments_as_dict["segments"] = srt_segments

        options = dict()
        options["max_line_width"] = None
        options["max_line_count"] = None
        options["highlight_words"] = False
        writer = get_writer("srt", directory)
        try:
            writer(segments_as_dict, targetfile, options)
        except:
            print("Attempting to use an older Version of Whisper")
            writer(segments_as_dict, targetfile)
        print("DONE writing SRT: " + str(targetfile))

        # create DOCX file
        if createDOCX:
            scriptFilename = str(path.with_suffix('.docx'))
            print("Writing Script DOCX: " + str(scriptFilename))
            scriptFilename = speakersToDoc(speaker_segments=transcribed_segments, translated_segments=translated_segments, scriptFilename=scriptFilename, sourcefile=sourcefile, translated=translate)
            print("DONE writing script DOCX: " + scriptFilename)

    print("SPEAKER DIARIZATION done...")

# speaker diarization = seperation of the audio in speaker segments
def speaker_diarization(sourcefile):
  
  # usage of pyannote pretrained model for speaker diarization
  pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization@2.1", use_auth_token="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")
  # check if CUDA capable GPU is available
  try:
      print("Attempting to use CUDA capable GPU")
      pipeline.to(torch.device("cuda"))
  except:
      print("Using CPU instead")
      pipeline.to(torch.device("cpu"))
      
  # sourcefile = 'audio.wav'
  # apply the pipeline to an audio file
  diarization = pipeline(sourcefile, min_speakers=2, max_speakers=8)

  speaker_segments = []
  
  for speech_turn, track, speaker in diarization.itertracks(yield_label=True):
    print(f"{speech_turn.start:4.1f} {speech_turn.end:4.1f} {speaker}")
    speaker_segments.append(speaker_segment(speaker,speech_turn.start,speech_turn.end))
  return speaker_segments

# Transcription of the individual segments 
def render_segments(sourcefile, speaker_segments, lang):
    print("TRANSCRIBING SEGMENTS")
    #load compact model if possible
    if (not complex):
        model = whisper.load_model("base")
    else:
        model = whisper.load_model("medium")

    transcribed_segments = []

    languages = {}

    # load audio 
    audio = AudioSegment.from_file(sourcefile,format="wav")

    for segment in speaker_segments:
        print("Transcription of Audio from: ", str(segment.in_point)+" to: "+str(segment.out_point))

        # Slice Audio with pydup
        segment_in = int(segment.in_point*1000)
        segment_out = int(segment.out_point*1000)
        segmentAudio = audio[segment_in:segment_out]

        ## convert to expected format
        if segmentAudio.frame_rate != 16000: # 16 kHz
            segmentAudio = segmentAudio.set_frame_rate(16000)
        if segmentAudio.sample_width != 2:   # int16
            segmentAudio = segmentAudio.set_sample_width(2)
        if segmentAudio.channels != 1:       # mono
            segmentAudio = segmentAudio.set_channels(1)        
        arr = np.array(segmentAudio.get_array_of_samples())
        arr = arr.astype(np.float32)/32768.0
        
        # analyze which language the individual speakers speak
        if not segment.speaker in languages:
            languages[segment.speaker] = get_language(arr, model, lang)
        
        # transcription using OpenAI Whisper
        result = model.transcribe(arr, language=languages[segment.speaker])
        summarized_segments = condenseSegments(result['segments'], 1)

        timecode_corrected_segments = []

        for s in summarized_segments:
            timecode_corrected_segments.append({'id':s['id'],'start':segment.in_point + s['start'], 'end': segment.in_point+s['end'], 'text': s['text']})

        transcribed_segments.append(transcribed_segment(segment.speaker, timecode_corrected_segments))
        print("DONE RENDERING SPEAKER SEGMENT")

        languages = {}

    return transcribed_segments

# Returns the language spoken in a segment
def get_language(segmentName, model, lang):
    audio = whisper.pad_or_trim(segmentName)

    # make log-Mel spectrogram and move to the same device as the model
    mel = whisper.log_mel_spectrogram(audio).to(model.device)

    # detect the spoken language
    _, probs = model.detect_language(mel)
    # check which of the given languages is the most propable
    languages = {"en":probs['en'],"de":probs['de'], lang:probs[lang]}
    print(languages)
    print(max(languages, key=languages.get))
    #print(f"Detected language: {max(probs, key=probs.get)}")
    # return the most propable language
    return max(languages, key=languages.get)

# speaker parts are combined where multiple segments of a speaker are not interrupted by another speaker 
def condenseSpeakers(speaker_segments):
    condensedSpeakers = []

    latest_timestamp = 0
    
    for segment in speaker_segments:

        if len(condensedSpeakers) !=0:

            if condensedSpeakers[-1].out_point > latest_timestamp:
                latest_timestamp = condensedSpeakers[-1].out_point

            if segment.in_point > latest_timestamp:

                if condensedSpeakers[-1].speaker == segment.speaker and condensedSpeakers[-1].out_point == latest_timestamp:
                    latest_segment = condensedSpeakers[-1]
                    latest_segment.out_point = segment.out_point

                    condensedSpeakers[-1] = latest_segment

                else:
                    condensedSpeakers.append(segment)

            else:
                condensedSpeakers.append(segment)

        else:
            condensedSpeakers.append(segment)


    return condensedSpeakers