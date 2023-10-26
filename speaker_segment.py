# Class to store data for the speaker segmentation
class speaker_segment:
    speaker:str
    in_point:str
    out_point:str

    def __init__(self, speaker, in_point, out_point):
        self.speaker = speaker
        self.in_point = in_point
        self.out_point = out_point

# Class to store data for transcribed segments of a speaker
class transcribed_segment:
    speaker:str
    def __init__(self, speaker, segments):
        self.speaker = speaker
        self.segments = segments
