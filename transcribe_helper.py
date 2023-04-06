import re

def condenseSegments(segments:list, sentences:int=1, inprecise:bool=True):
    segments_count = len(segments)
    summarized_segments = []
    tmp_text = ""
    score = 0
    new_id = 0
    new_start = True
    
    for index, segment in enumerate(segments):
        
        last_line = index >= segments_count
        
        #when start save start of segment
        if(new_start):    
            starttime = segment['start']
            new_start = False
        
        #add segment to text
        tmp_text += segment['text']
        
        #search for the last fullstop, questionmark, exclamation mark in the text
        #ATTENTION: for this we reverse the string
        match = re.search(r"[\.!?]", segment['text'][::-1])
        
        #if we have a match => add score because we finished one sentence
        if (match != None):
            score += 1
        
        #if sentence completed or end of text reached
        if (score >= sentences or last_line):
            #note end time
            endtime = segment['end']
            
            #save segment
            new_segment = dict(id=new_id, start=starttime, end=endtime, text=tmp_text)
            summarized_segments.append(new_segment)
            new_id =+ 1
            
            #reset
            score = 0
            new_start = True
            tmp_text = ""      
            
    return summarized_segments

