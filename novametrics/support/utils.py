import os
import json
import pickle
import numpy as np
import pandas as pd 

def not_none(val):
    """Returns False if val is None"""
    if val == val:
        return True
    else:
         return False


def parse_properties(properties_file, **kwargs):
    # Assumes initial file structure, e.g. "city          = CA_RIVERSIDE-MUNI"
    out = {}
    # Open file and parse
    with open(properties_file, 'r') as prop_file:
        for line in prop_file:
            if line[0] == '#' or ' = ' not in line:
                # line doesn't include a property
                continue
            line_split = line.split(' = ')
            key = line_split[0].strip()
            if len(line_split) == 2:
                # convert to string, float, or list
                val = line_split[1].strip()
                try:
                    out[key] = eval(val)
                except (NameError, SyntaxError):
                    out[key] = val
            elif len(line_split) > 2:
                # convert to dict (all should be floats)
                line_list = '='.join(line_split[1:]).split('   ')
                line_list = [tuple(s.split('=')) for s in line_list]
                out[key] = {k.strip(): float(v.strip()) for (k, v) in line_list}
    # vol = out['building length (m)'] * out['building width (m)'] * out['ceiling height (m)'] * out['num stories']
    # out['building volume (m^3)'] = vol
    return out


def get_filename(path, end_conditions):
    if type(end_conditions) == list:
        end_condition_list = end_conditions
    else:
        end_condition_list = [end_conditions]
        
    for end_condition in end_condition_list:
        filename = [f for f in os.listdir(path) if f.endswith(end_condition)]
        if len(filename) == 1:
            return filename[0]
        elif len(filename) > 1:
            print(f"Warning! Multiple names {filename} match the end condition {end_condition}. Using {filename[0]}")
            return filename[0]
        else:
            continue

    raise Exception(f"Error in get_filename. No filenames in {path} matched any of the end conditions in {end_condition_list}. Filenames are {os.listdir(path)}")
    
    return filename


def load_post(path, filename):
    # Load a json into a python dictionary
    with open(os.path.join(path, filename), 'r') as fp:
        post = json.load(fp)
    return post


def save_post(post, path, filename):
    with open(os.path.join(path, filename), 'w') as fp:
        json.dump(post, fp, indent = 2)

 
def save_api_results(api_response, path, filename):
    with open(os.path.join(path, filename + '.pickle'), 'wb') as handle:
        pickle.dump(api_response, handle, protocol=pickle.HIGHEST_PROTOCOL)
      
    
def load_api_results(path, filename):
    with open(os.path.join(path, filename + '.pickle'), 'rb') as handle:
        api_response = pickle.load(handle)
    return api_response


def get_dictionary_value(d, name, default = ""):
    if name in d and not_none(d[name]):
        return d[name]
    else:
        return default