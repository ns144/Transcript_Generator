import json
import os

# Writes the content of a python dictionary into a json file
def write_json(dictionary, filename):
    with open(filename, "w") as outfile:
        json.dump(dictionary, outfile)
        
# Retrieves the content of a json file
def read_json(filename):
    # check if file exists
    if(os.path.isfile(filename)):
        with open(filename, 'r') as openfile:
        
            # Reading from json file
            json_object = json.load(openfile)
    
            #print(json_object)
            #print(type(json_object))
            return json_object
        
    else:
        return []
