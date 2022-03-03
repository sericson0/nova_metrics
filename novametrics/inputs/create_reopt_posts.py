"""creates REopt input json files from inputs from Excel sheet `inputs_file_name`

`create_reopt_posts` batch creates posts for all scenarios while 
`create_single_reopt_post` creates post for a single scenario

"""
import os 
import pandas as pd
import numpy as np
import json
import copy
# import collections.abc
import pathlib
# import novametrics.apiquery.find_urdb as Find_URDB
from novametrics.support.utils import load_post, not_none
from novametrics.inputs.reopt_post_support_functions import get_pv_prod_factor
from novametrics.inputs.ochre_support_functions import load_ochre_outputs, wh_post, hvac_post
#%%

def create_reopt_posts(inputs_folder, inputs_file_name, default_values_file, main_output_folder, by_building = False, add_pv_prod_factor = True, solar_profile_folder = "/.", pv_watts_api_key = "",
                       ochre_controls = {}):
    """
    Create reopt json posts from input excel sheet in `inputs_folder`/`inputs_file_name`.

    Use default_values_file json as template, and updates values based on input values. 
    Saves posts to `main_output_folder` and specified subfolder. 
    If `add_pv_prod_factor` is True, then searches for pv factor csv in `solar_profile_folder` 
    and downloads from PV watts https://developer.nrel.gov/docs/solar/pvwatts/v6/ if needed.
    Optional ability to load load profiles from OCHRE model outputs.      

    Parameters
    ----------
    input_folder : str
        Path to folder which cointains default json and inputs Excel file.
    inputs_file_name : str
        Name of inputs Excel file.
    default_values_file : str
        Name of default json template.
    main_output_folder : str
        folder path where REopt posts are saved.
    add_pv_prod_factor : bool
        if True, then adds pv factors to post.
    by_building : bool
        if True, then creates posts for each building type in OCHRE output folder.
    solar_profile_folder : str
        path to folder where solar profiles are saved.
    pv_watts_api_key : str
        key to download solar proviles from PV watts.
    ochre_controls_dict : dict
        optional dictionary of OCHRE building model output values (such as folder path).
    """
    pathlib.Path(solar_profile_folder).mkdir(parents=True, exist_ok=True)
    
    inputs_df = pd.read_excel(os.path.join(inputs_folder, inputs_file_name), sheet_name='REopt Posts')
    defaults = load_post(inputs_folder, default_values_file)
    
    for i, input_vals in inputs_df.iterrows():
        ochre_controls["use_ochre_outputs"] = False
        
        if not ochre_controls.get("ochre_outputs_main_folder"):
            ochre_controls["ochre_outputs_main_folder"] = "OCHRE"
        if by_building:
            ochre_controls["use_ochre_outputs"] = True
            buildings = os.listdir(ochre_controls["ochre_outputs_main_folder"])
            for b in buildings:
                ochre_controls["ochre_outputs_subfolder"] = b
                input_vals["output_subfolder"] = b
                create_single_reopt_post(defaults, input_vals, main_output_folder, add_pv_prod_factor, solar_profile_folder, pv_watts_api_key, ochre_controls)
        else:
            if ("ochre_folder" in input_vals) and not_none(input_vals["ochre_folder"]):
                ochre_controls["use_ochre_outputs"] = True
                ochre_controls["ochre_outputs_subfolder"] = input_vals["ochre_folder"]
            create_single_reopt_post(defaults, input_vals, main_output_folder, add_pv_prod_factor, solar_profile_folder, pv_watts_api_key, ochre_controls)
            
      
#%%
def create_single_reopt_post(defaults, input_vals, main_output_folder, add_pv_prod_factor = True, solar_profile_folder = "./", 
                             pv_watts_api_key = "", ochre_controls = {}):
    """
    Create single reopt json posts using `defaults` as template and adding `input_vals`

    Parses `inputs_vals` and adds values to defaults to create REopt post.
    Saves post to `main_output_folder`/`optional_subfolder` where the subfolder can be defined in `inputs_vals`. 
    
    Saves posts to `main_output_folder` and specified subfolder. 
    If `add_pv_prod_factor` is True, then searches for pv factor csv in `solar_profile_folder` 
    and downloads from PV watts https://developer.nrel.gov/docs/solar/pvwatts/v6/ if needed.
    Optional ability to load load profiles from OCHRE model outputs.      

    Parameters
    ----------
    defaults : dict
        Dictionary of template of default inputs. Unspecified values default to REopt defaults
    input_vals : pandas DataFrame row
        Row slice from pandas DataFrame Inputs
    main_output_folder : str
        folder path where REopt posts are saved.
    add_pv_prod_factor : bool
        if True, then adds pv factors to post.
    solar_profile_folder : str
        path to folder where solar profiles are saved.
    pv_watts_api_key : str
        key to download solar proviles from PV watts.
    ochre_controls : dict
        optional dictionary of OCHRE building model output values (such as folder path).
    """
    print(f"Creating REopt post {input_vals['post_name']}")
    pathlib.Path(main_output_folder).mkdir(parents=True, exist_ok=True)
    
    post = copy.deepcopy(defaults)
    file_name = input_vals["post_name"] + ".json"
    
    if add_pv_prod_factor:
        post["Scenario"]["Site"]["PV"]["prod_factor_series_kw"] = get_pv_prod_factor(input_vals, solar_profile_folder, post, pv_watts_api_key)
        
    #Add load profile
    if ("load_file" in input_vals) and not_none(input_vals["load_file"]):
        if "LoadProfile" not in post["Scenario"]["Site"]:
            post["Scenario"]["Site"]["LoadProfile"] = {}
        post['Scenario']['Site']['LoadProfile']['loads_kw'] = list(pd.read_csv(input_vals["load_file"], header=None).iloc[:,0])

    #Load ochre outputs
    if ochre_controls["use_ochre_outputs"]:
        ochre_outputs = load_ochre_outputs(ochre_controls)
        #If OCHRE run fails then ochre_outputs will be []. In this case don't add OCHRE values
        if ochre_outputs != []:
            parsed_prop, a_matrix, b_matrix, hourly_inputs, a_matrix_wh, b_matrix_wh = ochre_outputs
            
            if "LoadProfile" not in post["Scenario"]["Site"]:
                post["Scenario"]["Site"]["LoadProfile"] = {}
            post['Scenario']['Site']['LoadProfile']['loads_kw'] = list(hourly_inputs.loc[:, 'Total Electric Power (kW)'])
            
            if "WH" in input_vals and not_none(input_vals["WH"]):
                wh_post(post, ochre_outputs, ochre_controls) # wh_lower_bound, wh_upper_bound, wh_comfort_limit)
            if "HVAC" in input_vals and not_none(input_vals["WH"]):
                hvac_post(post, ochre_outputs, ochre_controls) #hvac_lower_bound, hvac_upper_bound, hvac_comfort_lower_bound, hvac_comfort_upper_bound)
        else:
            print(f"OCHRE outputs failed for {input_vals['post_name']}")
            return None
                
    #Output subfolder allows for folder structure for REopt posts
    if "output_subfolder" in input_vals and not_none(input_vals["output_subfolder"]):
        output_folder = os.path.join(main_output_folder, input_vals["output_subfolder"])
        pathlib.Path(output_folder).mkdir(parents=True, exist_ok=True)
    else:
        output_folder = main_output_folder
    
    for name, val in input_vals.iteritems():
        update_post(post, name, val)
        
    with open(os.path.join(output_folder, file_name), "w") as fp:
        json.dump(post, fp, indent = 2)
        
    
def update_post(post, name, val):
    """Parses input value to REopt post"""

    if val != val:   #Checks if is nan
        pass
    else:
        if type(val) is np.int64:
            val = int(val)
        if name in ["post_name", "output_subfolder", "ochre_folder", "load_file", "solar_production_factor_file", "WH", "HVAC"]:
            pass
        elif "ScenarioLevel|" in name:
            name_sub = name.replace("ScenarioLevel|", "")
            post["Scenario"][name_sub] = val
        elif "|" in name:
            upper_level, lower_variable = name.split("|")
            if upper_level not in post["Scenario"]["Site"]:
                post["Scenario"]["Site"][upper_level] = {}
            post["Scenario"]["Site"][upper_level][lower_variable] = val
        else:
            post["Scenario"][name] = val