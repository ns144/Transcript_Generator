import json
import os
 
def write_json(dictionary, filename):
    with open(filename, "w") as outfile:
        json.dump(dictionary, outfile)
        

def read_json(filename):
    if(os.path.isfile(filename)):
        with open(filename, 'r') as openfile:
        
            # Reading from json file
            json_object = json.load(openfile)
    
            #print(json_object)
            #print(type(json_object))
            return json_object
        
    else:
        return []
#
#rL = ['C:/Users/NikolasS/Documents/Drone/DJI_0262.MP4', 'C:/Users/NikolasS/Documents/Drone/DJI_0263.MP4', 'C:/Users/NikolasS/Documents/Drone/DJI_0264-001.MP4', 'C:/Users/NikolasS/Documents/Drone/DJI_0265.MP4', 'C:/Users/NikolasS/Documents/Drone/DJI_0266-002.MP4', 'C:/Users/NikolasS/Documents/Drone/DJI_0267.MP4']
#
#write_json(rL, 'sample.json')
#
#
#print(read_json('sample.json'))
#