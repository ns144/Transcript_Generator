from pathlib import Path
from configparser import ConfigParser
import subprocess
import whisper
from whisper.utils import get_writer
from transcribe_helper import condenseSegments
from script_helper import transcriptToDoc 
from script_helper import speakersToDoc
from speaker_segment import speaker_segment
from speaker_segment import transcribed_segment
import torch
import os

def generate_transcript(sourcefile:str, lang='en', complex=False, createDOCX=False, speakerDiarization=False, num_speakers=2, write_srt=False):
    
    print("GPU: " + str(torch.cuda.is_available()))
    print("Torch version:" + str(torch.__version__))
    #print("Why tough? "+ str(torch.zeros(1).cuda()))

    path = Path(sourcefile)

    if write_srt:
        #load compact model if possible
        if (not complex):
            #if English, we can load the smaller model
            if (lang=='en'): 
                model = whisper.load_model("base.en")    
            else:
                model = whisper.load_model("base")
        else:
                model = whisper.load_model("medium")

        result = model.transcribe(sourcefile, language=lang)

        #In order to make translation better and make work easier for the editors we should group more segments into one segment.
        summarized_segments = condenseSegments(result['segments'], 1)

        #save SRT
        targetfile = path.with_suffix('.srt')
        name = targetfile.name
        directory = targetfile.parent
        print("Saving SRT: " + str(targetfile))

        segments_as_dict = dict()
        segments_as_dict["segments"] = summarized_segments
        writer = get_writer("srt", directory)
        writer(segments_as_dict, targetfile)

        print("SRT done...")

    #del model
    #torch.cuda.empty_cache()
    #print("IMPROVING WORD TIMESTAMPS")
    # Improve Timestamps
    #resultwhisperx = improve_timestamps(result, sourcefile)

    if speakerDiarization:
      print("SPEAKER DIARIZATION")
      #speaker_diarization(result["segments"], sourcefile, num_speakers)
      speaker_segments = speaker_diarization(sourcefile)
      print(speaker_segments)
      speaker_segments = condenseSpeakers(speaker_segments)
      print(speaker_segments)
      transcribed_segments = render_segments(sourcefile, speaker_segments, lang)

      for segment in transcribed_segments:
          print("This segment was spoken by: "+segment.speaker)
          print("And this is what he said: "+ str(segment.segments))

      scriptFilename = str(path.with_suffix('.docx'))
      print("Writing Script DOCX: " + str(scriptFilename))
      scriptFilename = speakersToDoc(transcribed_segments, [], scriptFilename, sourcefile)
      print("DONE writing script DOCX: " + scriptFilename)

    print("SPEAKER DIARIZATION done...")
    
    #if createDOCX:
    #    #save DOCX
    #    scriptFilename = str(path.with_suffix('.docx'))
    #    print("Writing Script DOCX: " + str(scriptFilename))
#
    #    scriptFilename = transcriptToDoc(summarized_segments, [], scriptFilename, sourcefile)
    #    print("DONE writing script DOCX...")



#def improve_timestamps(whisper_result, sourcefile):
#    device = "cpu"
#    alignment_model, metadata = whisperx.load_align_model(language_code=whisper_result["language"], device=device)
#    result_aligned = whisperx.align(whisper_result["segments"], alignment_model, metadata, sourcefile, device)
#
#    # clear gpu vram
#    del alignment_model
#    torch.cuda.empty_cache()
#
#    return result_aligned

def speaker_diarization(sourcefile):
  from pyannote.audio import Pipeline
  pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization@2.1", use_auth_token="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")

  if sourcefile[-3:] != 'wav':
      subprocess.call(['ffmpeg', '-i', sourcefile,"-ac", "1", 'audio.wav', '-y'])
      sourcefile = 'audio.wav'

  # sourcefile = 'audio.wav'
  # apply the pipeline to an audio file
  diarization = pipeline(sourcefile, min_speakers=2, max_speakers=8)

  #print(diarization)

  speaker_segments = []

  for speech_turn, track, speaker in diarization.itertracks(yield_label=True):
    print(f"{speech_turn.start:4.1f} {speech_turn.end:4.1f} {speaker}")
    speaker_segments.append(speaker_segment(speaker,speech_turn.start,speech_turn.end))

  #print(speaker_segments[0].in_point)
  return speaker_segments

  # dump the diarization output to disk using RTTM format
  #with open("audio.rttm", "w") as rttm:
  #  diarization.write_rttm(rttm)

def render_segments(sourcefile, speaker_segments, lang):
    print("TRANSCRIBING SEGMENTS")
    model = whisper.load_model("base")

    transcribed_segments = []

    languages = {}

    for segment in speaker_segments:
        segmentName = "segment_" + str(segment.in_point) + ".wav"
        subprocess.call(['ffmpeg', '-i', sourcefile, '-ss', str(segment.in_point), '-to', str(segment.out_point), segmentName, '-y'])
        
        if not segment.speaker in languages:
            languages[segment.speaker] = get_language(segmentName, model, lang)
        
        result = model.transcribe(segmentName, language=languages[segment.speaker])
        summarized_segments = condenseSegments(result['segments'], 1)

        timecode_corrected_segments = []

        for s in summarized_segments:
            timecode_corrected_segments.append({'id':s['id'],'start':segment.in_point + s['start'], 'end': segment.in_point+s['end'], 'text': s['text']})

        #print("Original: " +str(summarized_segments))
        #print(segment.speaker + " said: "+ str(timecode_corrected_segments))
        transcribed_segments.append(transcribed_segment(segment.speaker, timecode_corrected_segments))
        os.remove(segmentName)
        print("DONE RENDERING SPEAKER SEGMENT")

        languages = {}

    return transcribed_segments

def get_language(segmentName, model, lang):
    audio = whisper.load_audio(segmentName)
    audio = whisper.pad_or_trim(audio)

    # make log-Mel spectrogram and move to the same device as the model
    mel = whisper.log_mel_spectrogram(audio).to(model.device)

    # detect the spoken language
    _, probs = model.detect_language(mel)
    languages = {"en":probs['en'],"de":probs['de'], lang:probs[lang]}
    print(languages)
    print(max(languages, key=languages.get))
    #print(f"Detected language: {max(probs, key=probs.get)}")
    return max(languages, key=languages.get)
    
def condenseSpeakers(speaker_segments):
    condensedSpeakers = []
    for segment in speaker_segments:
        if len(condensedSpeakers) !=0 and condensedSpeakers[-1].speaker == segment.speaker:
            latest_segment = condensedSpeakers[-1]
            latest_segment.out_point = segment.out_point

            condensedSpeakers[-1] = latest_segment

        else:
            condensedSpeakers.append(segment)

    return condensedSpeakers

#def speaker_diarization(segments, sourcefile, num_speakers):
#    import pyannote.audio
#    from pyannote.audio.pipelines.speaker_verification import PretrainedSpeakerEmbedding
#    from pyannote.audio import Audio
#    from pyannote.core import Segment
#
#    import wave
#    import contextlib
#
#    from sklearn.cluster import AgglomerativeClustering
#    import numpy as np
#    embedding_model = PretrainedSpeakerEmbedding( "speechbrain/spkrec-ecapa-voxceleb", device=torch.device("cpu"))
#
#    if sourcefile[-3:] != 'wav':
#        subprocess.call(['ffmpeg', '-i', sourcefile, 'audio.wav', '-y'])
#        sourcefile = 'audio.wav'
#
#    with contextlib.closing(wave.open(sourcefile,'r')) as f:
#        frames = f.getnframes()
#        rate = f.getframerate()
#        duration = frames / float(rate)
#
#    audio = Audio()
#
#    def segment_embedding(segment):
#      start = segment["start"]
#      # Whisper overshoots the end timestamp in the last segment
#      end = min(duration, segment["end"])
#      clip = Segment(start, end)
#      waveform, sample_rate = audio.crop(sourcefile, clip)
#      return embedding_model(waveform[None])
#    
#    embeddings = np.zeros(shape=(len(segments), 192))
#
#    for i, segment in enumerate(segments):
#      embeddings[i] = segment_embedding(segment)
#
#    embeddings = np.nan_to_num(embeddings)
#
#    clustering = AgglomerativeClustering(num_speakers).fit(embeddings)
#    labels = clustering.labels_
#    for i in range(len(segments)):
#      segments[i]["speaker"] = 'SPEAKER ' + str(labels[i] + 1)
#
#    def time(secs):
#        return datetime.timedelta(seconds=round(secs))
#
#    f = open("transcript.txt", "w")
#
#    for (i, segment) in enumerate(segments):
#      if i == 0 or segments[i - 1]["speaker"] != segment["speaker"]:
#        f.write("\n" + segment["speaker"] + ' ' + str(time(segment["start"])) + '\n')
#      f.write(segment["text"][1:] + ' ')
#    f.close()