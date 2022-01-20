#!/usr/bin/env python
# coding: utf-8
import os 
import pandas as pd
from nova_metrics.support.utils import not_none
from nova_metrics.apiquery.download_pv_watts import download_pv_watts
# import collections.abc

#%%
# def load_ochre_outputs(file_path_name, ochre_controls):
#     """
#     Return list of OCHRE building model output results.
    
#     `file_path_name` is path to OCHRE output folder relative to OCHRE main folder. 
#     `ochre_controls` is a dictionary which can contain specifications for string to match filenames.
#     OCHRE output folder filenames default to:
#         properties_file - .properties
#         envelope_matrixA - _Envelope_matrixA.csv
#         envelope_matrixB - _Envelope_matrixB.csv
#         hourly_inputs - _hourly.csv
#         water_tank_matrixA - _Water Tank_matrixA.csv
#         water_tank_matrixB - _Water Tank_matrixB.csv

#     Returns a list of [parsed_prop, a_matrix, b_matrix, hourly_inputs, a_matrix_wh, b_matrix_wh]
#     """
#     if ochre_controls.get("ochre_outputs_main_folder"):
#         ochre_output_file_path = os.path.join(ochre_controls["ochre_outputs_main_folder"], file_path_name)
#     else:
#         ochre_output_file_path = file_path_name
        
#     if ochre_controls.get("ochre_inputs_main_folder"):
#         ochre_input_file_path = os.path.join(ochre_controls["ochre_inputs_main_folder"], file_path_name)
#     else:
#         ochre_input_file_path = file_path_name
    
#     properties_file_key = get_dictionary_value(ochre_controls, "properties_file", ".properties")
#     envelope_matrixA_key = get_dictionary_value(ochre_controls, "envelope_matrixA", "_Envelope_matrixA.csv")
#     envelope_matrixB_key = get_dictionary_value(ochre_controls, "envelope_matrixB", "_Envelope_matrixB.csv")
#     hourly_inputs_key = get_dictionary_value(ochre_controls, "hourly_inputs", "_hourly.csv")
#     water_tank_matrixA_key = get_dictionary_value(ochre_controls, "water_tank_matrixA", "_Water Tank_matrixA.csv")
#     water_tank_matrixB_key = get_dictionary_value(ochre_controls, "water_tank_matrixB", "_Water Tank_matrixB.csv")
    
    
#     properties_file = get_filename(ochre_input_file_path, properties_file_key)           
#     parsed_prop = parse_properties(os.path.join(ochre_input_file_path, properties_file))
    
#     a_matrix_file = get_filename(ochre_output_file_path, envelope_matrixA_key)
#     b_matrix_file = get_filename(ochre_output_file_path, envelope_matrixB_key)
#     hourly_inputs_file = get_filename(ochre_output_file_path, hourly_inputs_key)
#     a_matrix_wh_file = get_filename(ochre_output_file_path, water_tank_matrixA_key)
#     b_matrix_wh_file = get_filename(ochre_output_file_path, water_tank_matrixB_key)

#     a_matrix = pd.read_csv(os.path.join(ochre_output_file_path, a_matrix_file), index_col=0)
#     b_matrix = pd.read_csv(os.path.join(ochre_output_file_path, b_matrix_file), index_col=0)
#     hourly_inputs = pd.read_csv(os.path.join(ochre_output_file_path, hourly_inputs_file))
#     a_matrix_wh = pd.read_csv(os.path.join(ochre_output_file_path, a_matrix_wh_file), index_col=0)
#     b_matrix_wh = pd.read_csv(os.path.join(ochre_output_file_path, b_matrix_wh_file), index_col=0)
    
#     return [parsed_prop, a_matrix, b_matrix, hourly_inputs, a_matrix_wh, b_matrix_wh]

#%%
def get_pv_prod_factor(input_vals, solar_profile_folder, post, pv_watts_api_key):
    """
    Returns list of pv production factors and if needed downloads factors from PV Watts
    
    First looks for `solar_production_factor_file` in input values for csv file path.
    If not there then looks for csv in `solar_profile_folder`. Uses file name of 
    PVproductionFactor_{latitude}_{longitude}.csv for site latitude and longitude.
    If no solar profile found then downloads from PV watts using `pv_watts_api_key`

    Parameters
    ----------
    input_vals : pandas data frame row slice
        Single row of pandas data frame of inputs.
    solar_profile_folder : str
        string to solar_profile_folder location relatvie to main folder.
    post : dict
        Dictionary of REopt post (only used to get default lat long).
    pv_watts_api_key : str
        PV Watts api key (NREL developer key).

    Returns
    -------
    list
        List of solar production factors.

    """
    if "solar_production_factor_file" in input_vals and not_none(input_vals["solar_production_factor_file"]):
        return list(pd.read_csv(input_vals["solar_production_factor_file"], header=None).iloc[:,0]) 
    
    else:
        if "latitude" in input_vals:
            latitude = input_vals["latitude"]
            longitude = input_vals["longitude"]
        else:
            latitude = post["Scenario"]["Site"]["latitude"]
            longitude = post["Scenario"]["Site"]["longitude"]
            
        pv_prod_factor_csv_file_path = os.path.join(solar_profile_folder, f"PVproductionFactor_{latitude}_{longitude}.csv")
        
        if not os.path.isfile(pv_prod_factor_csv_file_path):
            download_pv_watts(pv_prod_factor_csv_file_path, pv_watts_api_key, latitude, longitude)
            
        return list(pd.read_csv(pv_prod_factor_csv_file_path, header=None).iloc[:,0]) 
