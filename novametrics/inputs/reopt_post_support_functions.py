#!/usr/bin/env python
# coding: utf-8
import os 
import pandas as pd
from novametrics.support.utils import not_none
from novametrics.apiquery.download_pv_watts import download_pv_watts

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
