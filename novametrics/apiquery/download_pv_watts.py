import pandas as pd
import os
import requests

#download_pv_watts returns a csv of pv production factors for a given longitude and latitude location.
#Takes in solar parameters:  tilt, azimuth, module_type, module_type, array_type, losses, dc_ac_ratio, and inv_eff 
#Takes in global parameters: latitude, longitude, pv_watts_key
#Returns solar production factor for each hour
def download_pv_watts(location_file_path, pv_watts_key, lat, lon, tilt = None, azimuth = 180, module_type = 0, array_type = 1, losses = 0.14, dc_ac_ratio = 1.2, inv_eff = 0.96):
    if tilt == None:
        tilt = lat

    url = ( f'https://developer.nrel.gov/api/pvwatts/v6.json?api_key={pv_watts_key}'
            f'&lat={lat}&lon={lon}&tilt={tilt}'
            f'&system_capacity=1&azimuth={azimuth}&module_type={module_type}'
            f'&array_type={array_type}&losses={round(losses*100, 3)}&dc_ac_ratio={dc_ac_ratio}'
            f'&gcr=0.4&inv_eff={inv_eff*100}&timeframe=hourly&dataset=nsrdb&radius=100')
    watt_data = requests.get(url).json()["outputs"]["ac"]
    	# print(url)
    prod_factor = [w/1000 for w in watt_data] #PV Watts returns value in Watts. Want kW
    
    pd.DataFrame(prod_factor).to_csv(location_file_path, index = False, header = False)



#Code to test function
# pv_watts_key = "gAfosXcQ9Ldfw3qXqvKVb7PxMEkYigozmC9R3mXQ"
# lat = 34.5376 
# lon = -82.6803
# tilt = 34.579
# azimuth =180.0
# module_type = 0 
# array_type = 1 
# losses = 0.14 
# dc_ac_ratio = 1.2
# inv_eff = 0.96
# download_pv_watts("../", pv_watts_key, lat, lon, tilt, azimuth, module_type, array_type, losses, dc_ac_ratio, inv_eff)

