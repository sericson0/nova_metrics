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
from nova_metrics.apiquery.download_pv_watts import download_pv_watts
# import nova_metrics.apiquery.find_urdb as Find_URDB
#TODO add water heater and HVAC inputs
from nova_metrics.support.utils import load_post 
from nova_metrics.inputs.reopt_post_support_functions import load_ochre_outputs
from nova_metrics.support.logger import log
#%%
def create_reopt_posts(inputs_folder, inputs_file_name, default_values_file, main_output_folder, add_pv_prod_factor = True, solar_profile_folder = "/.", pv_watts_api_key = "", ochre_output_main_folder = ""):
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
    solar_profile_folder : str
        path to folder where solar profiles are saved.
    pv_watts_api_key : str
        key to download solar proviles from PV watts.
    ocher_output_main_folder : str
        path to OCHRE building model output.
    """
    pathlib.Path(solar_profile_folder).mkdir(parents=True, exist_ok=True)
    
    inputs_df = pd.read_excel(os.path.join(inputs_folder, inputs_file_name), sheet_name='REopt Posts')
    defaults = load_post(inputs_folder, default_values_file)
    
    for i, input_vals in inputs_df.iterrows():
      create_single_reopt_post(defaults, input_vals, main_output_folder, add_pv_prod_factor, solar_profile_folder, pv_watts_api_key, ochre_output_main_folder)
      
#%%
def create_single_reopt_post(defaults, input_vals, main_output_folder, add_pv_prod_factor = True, solar_profile_folder = "./", pv_watts_api_key = "", ochre_output_main_folder = ""):
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
    ocher_output_main_folder : str
        path to OCHRE building model output.
    """
    post = copy.deepcopy(defaults)
    file_name = input_vals["post_name"] + ".json"

    
    if add_pv_prod_factor:
        if "latitude" in input_vals:
            latitude = input_vals["latitude"]
            longitude = input_vals["longitude"]
        else:
            latitude = post["Scenario"]["Site"]["latitude"]
            longitude = post["Scenario"]["Site"]["longitude"]
        pv_prod_factor_csv_file_path = os.path.join(solar_profile_folder, f"PVproductionFactor_{latitude}_{longitude}.csv")
        if not os.path.isfile(pv_prod_factor_csv_file_path):
            download_pv_watts(pv_prod_factor_csv_file_path, pv_watts_api_key, latitude, longitude)
            
        post["Scenario"]["Site"]["PV"]["prod_factor_series_kw"] = list(pd.read_csv(pv_prod_factor_csv_file_path, header=None).iloc[:,0])    
        
        
    #Load ochre outputs
    if ("ochre_folder" in input_vals) and (input_vals["ochre_folder"] == input_vals["ochre_folder"]):
        parsed_prop, a_matrix, b_matrix, hourly_inputs, a_matrix_wh, b_matrix_wh = load_ochre_outputs(os.path.join(ochre_output_main_folder, input_vals["ochre_folder"]))
        
        if "LoadProfile" not in post["Scenario"]["Site"]:
            post["Scenario"]["Site"]["LoadProfile"] = {}
        post['Scenario']['Site']['LoadProfile']['loads_kw'] = list(hourly_inputs.loc[:, 'Total Electric Power (kW)'])
                
    
    
    if "output_subfolder" in input_vals:
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
            
        if name in ["post_name", "output_subfolder"]:
            pass
        elif name == "description":
            post["Scenario"]["description"] = val
        elif name in ["latitude", "longitude", "address", "land_acres", "roof_squarefeet", "elevation_ft"]:
            post["Scenario"]["Site"][name] = val
        else:
            if "|" not in name:
                log.debug(f"{name} is in incorrect format. Please use form <upper level>|<variable>. Example of correct input is PV|max_kw")
            else:
                upper_level, lower_variable = name.split("|")
                if upper_level not in post["Scenario"]["Site"]:
                    post["Scenario"]["Site"][upper_level] = {}
                    
                post["Scenario"]["Site"][upper_level][lower_variable] = val
            
#%%
####Test Code
# pv_watts_api_key = "eb14ACcUKmGtJT8WeB4kuJayhFNhWTSxpLTonqZ7"
# inputs_folder = "../../Test"
# default_values_file = "default_post.json"
# defaults = load_post(inputs_folder, default_values_file)
# solar_profile_folder = "../../Test/Solar Factors"

# inputs_file = "Test_Inputs.xlsx"
# inputs_df = pd.read_excel(os.path.join(inputs_folder, inputs_file), sheet_name='REopt Posts')

# inputs_line = inputs_df.iloc[0]
# main_output_folder = inputs_folder
# create_single_reopt_post(defaults, inputs_line, main_output_folder)
# create_reopt_posts(inputs_folder, inputs_file, default_values_file, main_output_folder, add_pv_prod_factor = True, solar_profile_folder = solar_profile_folder, pv_watts_api_key = pv_watts_api_key)


# def get_additional_costs(location_vals, building_name, scenario_vals, scenario_type):
#     additional_costs = 0
#     if "additional_costs" in location_vals:
#         additional_costs += location_vals["additional_costs"]
        
#     if "additional_costs" in location_vals["Buildings"][building_name]:
#         additional_costs += location_vals["Buildings"][building_name]["additional_costs"]
#     for st in scenario_type:
#         if "additional_costs" in location_vals["Scenario_Types"][st]:
#             additional_costs += location_vals["Scenario_Types"][st]["additional_costs"]
        
#     if "additional_costs" in scenario_vals:
#         additional_costs += scenario_vals["additional_costs"]
#     return additional_costs
# #%%

# def create_inputs(location_name, location_vals, building_name, scenario_name, scenario_vals, scenario_type = [], main_folder_path = "./"):
#     update_key = "Post Values"
    
    
#     scenario_folder_list = [location_name, building_name] + scenario_type
#     # pathlib.Path("/".join(scenario_folder_list)).mkdir(parents=True, exist_ok=True) 
    
#     post_inputs = {"FilePaths":{}, "PostValues":{}}
#     post_inputs["DefaultPost"]= load_post(os.path.join(main_folder_path, "Inputs"), "default_post.json")
#     post_inputs["FilePaths"]["scenario_name"] = "-".join(scenario_folder_list) + "-" + scenario_name
    
#     post_inputs["FilePaths"]["save_post_folder"] = "Posts" + "/" + "/".join(scenario_folder_list) 
#     # post_inputs["FilePaths"]["ochre_save_post_folder"] = "/".join(scenario_folder_list) + "/REopt OCHRE Posts"
#     post_inputs["FilePaths"]["save_response_folder"] = "REopt Response" + "/".join(scenario_folder_list) 
#     post_inputs["FilePaths"]["ochre_folder_path"] = os.path.join("OCHRE Outputs", location_name, building_name) 
    
#     #Add location values    
#     post_values = copy.deepcopy(location_vals[update_key])
    
#     #Add building values
#     if update_key in location_vals["Buildings"][building_name]:
#         update_nested_dict(post_values, location_vals["Buildings"][building_name][update_key])

#     #Add scenario values
#     update_nested_dict(post_values, scenario_vals)

#     #Add scenario type values. Scenario type values overwrites other values 
#     for st in scenario_type:
#         if update_key in location_vals["Scenario_Types"][st]:
#             update_nested_dict(post_values, location_vals["Scenario_Types"][st][update_key])
#         if "ra_path" in location_vals["Scenario_Types"][st]:
#             add_ra_values(post_values, location_vals["Scenario_Types"][st]["ra_path"])
        
#     post_inputs["PV_prod_factor_series_kw"] = list(pd.read_csv(os.path.join(main_folder_path, "Posts", location_name, "pv_prod_factor_file.csv"), header=None).iloc[:,0])
    
#     post_inputs["PostValues"] = post_values
#     post_inputs["additional_costs"] = get_additional_costs(location_vals, building_name, scenario_vals, scenario_type)
#     return post_inputs

# #%%
# def make_and_save_post(inputs, main_folder, save_ochre_post = False):
#     post, ochre_outputs = get_REopt_post(inputs, main_folder)

#     save_post_folder =  os.path.join(main_folder, inputs["FilePaths"]["save_post_folder"])
    
#     pathlib.Path(save_post_folder).mkdir(parents=True, exist_ok=True)
#     scenario_name = inputs["FilePaths"]["scenario_name"] 
    
#     save_post(post, save_post_folder, scenario_name + ".json")
    
#     if save_ochre_post:
#         pathlib.Path(os.path.join(save_post_folder, "OCHRE posts")).mkdir(parents=True, exist_ok=True)
#         save_post(ochre_outputs, os.path.join(save_post_folder, "OCHRE posts"), scenario_name + "_OCHRE_post.json")
    
#     return post


#%%
# def add_default_tariff(location_vals, api_keys):
#     if "ElectricTariff" not in location_vals["Post Values"]:
#         location_vals["Post Values"]["ElectricTariff"] = {}
#     if "urdb_label" in location_vals["Post Values"]["ElectricTariff"]:
#         return None
#     elif "zipcode" in location_vals:
#         location_vals["Post Values"]["ElectricTariff"]["urdb_label"] = Find_URDB.get_default_urdb_label(api_keys["urdb_api_key"], zipcode = data[loc]["zipcode"])
#     elif "latitude" in location_vals["Post Values"]:
#        location_vals["Post Values"]["ElectricTariff"]["urdb_label"] = Find_URDB.get_default_urdb_label(api_keys["urdb_api_key"], lat = location_vals["Post Values"]["latitude"], lon = location_vals["Post Values"]["longitude"], google_api_key = api_keys["google_api_key"])
#     elif "utility_name" in location_vals:
#         location_val["Post Values"]["ElectricTariff"]["urdb_label"] = Find_URDB.get_default_urdb_label(api_keys["urdb_api_key"], utility_name = location_vals["utility_name"])

#%%
# def add_ra_values(post_values, ra_path):
#     ra_post_values = load_post(ra_path[0], ra_path[1])
#     update_nested_dict(post_values, {"ElectricTariff": ra_post_values})
# #%%
# def get_tech_scenarios(input_data):
#     techs = input_data["Techs"]
#     tech_scenarios = {}
#     for ts in input_data["Tech Scenarios"]:
#         tech_scenarios[ts] = {}
#         for i in input_data["Tech Scenarios"][ts]:
#             update_nested_dict(tech_scenarios[ts], techs[i])
#     return tech_scenarios
# #%%
# def create_reopt_posts(main_folder_path, input_data, api_keys, add_default_tariff_boolian = False, overwrite = False):
#     print("Creating REopt posts")
#     #Building basecases is used for generate metrics 
#     building_basecases = {}
#     # input_data = load_post(input_data_folder, input_data_name)
#     tech_scenarios = get_tech_scenarios(input_data)
#     #
#     for loc in input_data["Locations"]:
#         location_vals = input_data["Locations"][loc]
        
#         location_path = os.path.join(main_folder_path, "Posts", loc)
#         pathlib.Path(location_path).mkdir(parents=True, exist_ok=True)
#         print(loc)
#         if not os.path.isfile(os.path.join(location_path, "pv_prod_factor_file.csv")):
#             print("Downloading PV file for", loc)
#             #Uses default values for azimuth, losses, inv efficiency and ac to dc ratio. Tilt is set to latitude
#             Download_PV_Watts.download_pv_watts(location_path, api_keys["nrel_api_key"], location_vals["Post Values"]["latitude"], location_vals["Post Values"]["longitude"])
            
#         if add_default_tariff_boolian:
#             add_default_tariff(location_vals, api_keys)
            
#         for bldg in location_vals["Buildings"]:
#             if "basecase" in location_vals["Buildings"][bldg] and location_vals["Buildings"][bldg]["basecase"] == True:
#                 building_basecases[loc] = bldg
            
#             scenario_types = location_vals["Scenario_Types"]["categories"]
#             for sce_type in scenario_types:
#                 for sce in tech_scenarios:
#                     scenario_vals = tech_scenarios[sce]
#                     if overwrite or not os.path.isfile(os.path.join(main_folder_path, "Posts", loc, bldg, "/".join(sce_type), sce + ".json")):
#                         make_and_save_post(create_inputs(loc, location_vals, bldg, sce, scenario_vals, scenario_type = sce_type, main_folder_path = main_folder_path), main_folder_path)
#     return building_basecases
