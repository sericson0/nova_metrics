# import sys
# sys.path.insert(1, './ochre/ochre')
import os
import sys
import shutil
# import pandas as pd
import datetime as dt
# from ochre import Dwelling
from pathlib import Path
# os.chdir(os.path.dirname(__file__))
from ochre import Dwelling
from ochre.FileIO import default_input_path
from novametrics.support.utils import get_dictionary_value, get_filename
# from nova_metrics.apiquery.download_nsrdb import download_nsrdb
#%%
def run_ochre(ochre_controls):
    """
    Runs OCHRE model for each building in `inputs_folder` and saves results to `results_folder`, both of which can be specified in `ochre_controls` dictionary. 
    
    Results saved in same subfolder structure as inputs.
    """
    input_main_folder = get_dictionary_value(ochre_controls, "ochre_inputs_main_folder", "OCHRE Inputs")
    output_main_folder = get_dictionary_value(ochre_controls, "ochre_outputs_main_folder", "OCHRE Outputs")
    ochre_weather_file = get_dictionary_value(ochre_controls, "weather_file_path", "https://data.nrel.gov/system/files/156/BuildStock_TMY3_FIPS.zip")
    properties_ext = get_dictionary_value(ochre_controls, "properties_file", "in.xml")
    schedule_ext = get_dictionary_value(ochre_controls, "schedule_inputs", "schedules.csv")
    if "default_inputs" in ochre_controls:
        default_inputs = ochre_controls["default_inputs"]
    else:
        default_inputs = default_input_path 
    #    
    input_path_list = [Path(f[0]) for f in os.walk(input_main_folder) if len(f[2]) > 0] #Gets subdirectories which contain files
    relative_path_list = [path.relative_to(input_main_folder) for path in input_path_list]  
    output_path_list = [os.path.join(output_main_folder, p) for p in relative_path_list]
    for i in range(len(input_path_list)):
        input_path = input_path_list[i]
        output_path = output_path_list[i]
        Path(output_path).mkdir(parents=True, exist_ok=True)
        
        ##TODO setup optional download from nsrdb
        # download_nsrdb(ochre_weather_file, location_vals["latitude"], location_vals["longitude"], api_keys["nrel_api_key"])
        
        properties_file = os.path.abspath(os.path.join(input_path, get_filename(input_path, properties_ext)))
        properties_yaml_name = properties_file.rsplit(".", 1)[0] + ".yaml"
        
        schedule_file = os.path.abspath(os.path.join(input_path, get_filename(input_path, schedule_ext)))
        simulation_name = "OCHRE_Run"

        # ochre_rate_file = os.path.join(location_inputs_folder, building, ' Rate.csv')
        # ochre_water_draw_file = os.path.join(location_inputs_folder, building, building + "_water_file.csv")
        # print(f"properties_file: {properties_file}, schedule_file: {schedule_file}, weather file: {ochre_weather_file}, default_inputs: {default_inputs}, outputs: {output_path}")
        try:
            run_ochre_single_case(simulation_name, properties_file, schedule_file, ochre_weather_file, default_inputs, output_path)
            shutil.move(properties_yaml_name, output_path)
        except Exception as e:
            print(f"OCHRE run {input_path} failed. Error {sys.exc_info()[0]} {e}.")
            shutil.rmtree(output_path)
        
        

def run_ochre_single_case(simulation_name, properties_file, schedule_file, weather_path, default_input_path, output_folder):
    """
    Run single ochre simulation and save outputs to `output_folder`

    Parameters
    ----------
    simulation_name : str
        String added to results files.
    properties_file : str
        Path to OCHRE property file.
    schedule_file : str
        Path to OCHRE schedule file.
    weather_path : str
        Path to zipped weather file.
    default_input_path : str 
        Path to OCHRE default inputs. Generally taken from default OCHRE paths.
    output_folder : str
        Path to folder where outputs will be saved.
    """
    
    dwelling_args = {
    # Timing parameters
    'start_time': dt.datetime(2018, 1, 1, 0, 0),  # year, month, day, hour, minute
    'time_res': dt.timedelta(minutes=60),
    'duration': dt.timedelta(days=365),
    'initialization_time': dt.timedelta(days=1),

    # Input parameters - Sample building
    # 'input_path': default_input_path,
    # 'properties_file': os.path.join(default_input_path, 'Properties Files', 'sample_resstock_house.xml'),
    # 'schedule_file': os.path.join(default_input_path, 'Schedule Files', 'sample_resstock_schedule.csv'),

    # Input parameters - ResStock
    'input_path': default_input_path,
    'properties_file': properties_file, 
    'schedule_file': schedule_file,
    'weather_path': weather_path,

    # Output parameters
    'save_results': True,
    'output_path': output_folder,
    # 'export_res': dt.timedelta(days=61),
    'verbosity': 9,  # verbosity of results file (1-9)

    # 'ext_time_res': dt.timedelta(minutes=15),
    'save_matrices': True,
    'show_eir_shr': True,
    }
    dwelling = Dwelling(simulation_name, **dwelling_args)
    df, metrics, hourly = dwelling.simulate()

# run_ochre_single_case(simulation_name, os.path.join(main_path, "in.xml"), os.path.join(main_path, "schedules.csv"), "C:/Users/sean/BuildStock_TMY3_FIPS", default_input_path, main_path)
