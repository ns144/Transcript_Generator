class speaker_segment:
    speaker:str
    in_point:str
    out_point:str

    def __init__(self, speaker, in_point, out_point):
        self.speaker = speaker
        self.in_point = in_point
        self.out_point = out_point


class transcribed_segment:
    speaker:str
    def __init__(self, speaker, segments):
        self.speaker = speaker
        self.segments = segments
