# import sys
# sys.path.insert(1, './ochre/ochre')
import os
# from shutil import copyfile
# import pandas as pd
# import datetime as dt
# from ochre import Dwelling
from pathlib import Path
os.chdir(os.path.dirname(__file__))
# from nova_metrics.apiquery.download_nsrdb import download_nsrdb
#%%
def run_ochre(inputs_folder, results_folder, properties_ext = '_rc_model.properties', schedule_ext = '_schedule.properties'):
    """
    Runs OCHRE model for each building in `inputs_folder` and saves results to `results_folder`
    
    Results saved in same subfolder structure as inputs.

    Parameters
    ----------
    post_folder : str
        Path to main folder for OCHRE input subfolders. 
    results_folder : str
        Path to main folder for OCHRE outputs.
        Seconds between poll query
    """
    folder_paths = [f[0] for f in os.walk(inputs_folder) if len(f[2]) > 0] #Gets subdirectories which contain files
    
    for location_path in folder_paths:
        ochre_weather_file = "https://data.nrel.gov/system/files/156/BuildStock_TMY3_FIPS.zip"
        ##TODO setup optional download from nsrdb
        
        # download_nsrdb(ochre_weather_file, location_vals["latitude"], location_vals["longitude"], api_keys["nrel_api_key"])
        
        properties_file = os.path.join(location_path, properties_ext)
        schedule_file = os.path.join(location_path, schedule_ext)


        ochre_rate_file = os.path.join(location_inputs_folder, building, ' Rate.csv')
        ochre_water_draw_file = os.path.join(location_inputs_folder, building, building + "_water_file.csv")
        
        
        
        
        
        
        
        post_dir = os.path.join(post_folder, directory)
        results_dir = os.path.join(results_folder, directory)
        results_file = os.path.join(results_folder, directory, post_name)
        
        Path(results_dir).mkdir(parents=True, exist_ok=True)

        if not os.path.isfile(results_file):
            print("Running REopt for", post_name)
            post = load_post(post_dir, post_name)
            reopt_results = reo_optimize(post, api_key, root_url=root_url, poll_interval=poll_interval)
            save_post(reopt_results, results_dir, post_name)





inputs_folder = "C:/Users/sean/Dropbox/NREL Work/Year 2020/NOVA/Coding Framework/V0.1/Testing Runs/OCHRE Inputs"









list(Path("C:/Users/sean/Dropbox/NREL Work/Year 2020/NOVA/Coding Framework/V0.1/Testing Runs/OCHRE Inputs").glob("**"))





def run_ochre(main_folder, inputs, api_keys = {}, overwrite_files = False):
    for location in inputs["Locations"]:
        print("Creating OCHRE outputs for", location)
        for building in inputs["Locations"][location]["Buildings"]:
            run_ochre_case(main_folder, inputs, location, building, api_keys, overwrite_files)
                                                                                                       
#%%

def run_ochre_case(main_folder, inputs, location, building, api_keys = {}, overwrite_files = False):
    #Converts relative path to absolute path
    # main_folder = pathlib.Path(main_folder).resolve()
    # location_inputs_folder = os.path.join(main_folder, 'OCHRE Inputs', location)

    if "ochre" in inputs["Locations"][location]["Buildings"][building]:
        building_vals = inputs["Locations"][location]["Buildings"][building]["ochre"]
    else:
        building_vals = {}
    #Download weather file. Currently name, email, affiliation, and reason for download are dummies. Check if these need to be acutal values
    ochre_weather_file = os.path.join(location_inputs_folder, location + " Weather File")
    if os.path.isfile(ochre_weather_file+ ".epw"):
        ochre_weather_file = ochre_weather_file + ".epw"
    else:
        ochre_weather_file = ochre_weather_file + ".csv"
        if not os.path.isfile(ochre_weather_file):
            print("Downloading weather file for ", location)
            download_nsrdb(ochre_weather_file, location_vals["latitude"], location_vals["longitude"], api_keys["nrel_api_key"])
    # case_folder = os.path.join(main_folder, 'OCHRE Inputs', location + ' Case Study', *case_sub_folders)
    properties_file = os.path.join(location_inputs_folder, building, building + '_rc_model.properties')
    schedule_file = os.path.join(location_inputs_folder, building, building + '_schedule.properties')
    # eplus_file = os.path.join(location_inputs_folder, building, building + '_EnergyPlus_Hourly.csv')
    ochre_rate_file = os.path.join(location_inputs_folder, building, ' Rate.csv')
    ochre_water_draw_file = os.path.join(location_inputs_folder, building, building + "_water_file.csv")
    
    output_folder = os.path.join(main_folder, "OCHRE Outputs", location, building)    
    
    pathlib.Path(output_folder).mkdir(parents=True, exist_ok=True)
    
    if "time_res" in building_vals:
        time_res = building_vals["time_res"]
    else:
        time_res = 10
        
    if "equipment" in building_vals:
        equip = building_vals["equipment"]
    else:
        equip = {}
    
    if "add_costs" in building_vals:
        add_costs = building_vals["add_costs"]
    else:
        add_costs = False   
    
    dwelling_args = {
        # Timing parameters
        'start_time': dt.datetime(2019, 1, 1, 0, 0),  # year, month, day, hour, minute
        'time_res': dt.timedelta(minutes=time_res),  # Note: OR WH cases run at 1 minute resolution, rest at 10 minute
        'duration': dt.timedelta(days=365),
        'initialization_time': dt.timedelta(days=7),
    
        # Input parameters
        'output_path': output_folder,
        'properties_file': properties_file,
        'schedule_file': schedule_file,
        'weather_file': ochre_weather_file,
        'water_draw_file': ochre_water_draw_file,
    
        # Output parameters
        'export_res': dt.timedelta(days=61),
        'verbosity': 9,  # verbosity of results file (1-9)
        'metrics_verbosity': 9,  # verbosity of metrics file (0-9)
    
        # Other parameters
        'assume_equipment': True,
        # 'ext_time_res': dt.timedelta(minutes=15),
        'save_matrices': True,
        'save_matrices_time_res': dt.timedelta(hours=1),
        'show_eir_shr': True,
        # 'reduced_min_accuracy': 1,
        # 'Indoor Thermal Mass Multiplier': 1,
    }
    equipment = equip
    
    # Load E+ files
    # eplus = Analysis.load_eplus_file(eplus_file)
    
    # only keep a few days - note, datetime slicing is inclusive
    # start = dwelling_args['start_time']
    # end = start + dwelling_args['duration'] - dwelling_args['time_res']
    # eplus = eplus.loc[start: end]

    copyfile(os.path.join(location_inputs_folder, building, building + '_rc_model.properties'),
              os.path.join(output_folder, building + '_rc_model.properties'))

    if overwrite_files or len(os.listdir(output_folder)) == 0:
        dwelling = Dwelling(building, equipment, **dwelling_args)
        ochre_exact, ochre_metrics, ochre = dwelling.simulate()
        ochre = ochre_exact.resample(dt.timedelta(hours=1)).mean()
        ochre.reset_index().to_csv(dwelling.hourly_output_file, index=False)

        dwelling = Dwelling(building, equipment, **dwelling_args)
        ochre_exact, ochre_metrics, ochre = dwelling.simulate()
    
        # recreate hourly file with all states and inputs
        ochre = ochre_exact.resample(dt.timedelta(hours=1)).mean()
        ochre.reset_index().to_csv(dwelling.hourly_output_file, index=False)
    
        if add_costs:
            # add electric energy cost for Oregon cases
            rates = pd.read_csv(ochre_rate_file)['Utility Rate']
            if len(rates) == len(ochre.index):
                rates.index = ochre.index
                total_cost = (ochre['Total Electric Power (kW)'] * rates).sum()
                ochre_metrics['Total Electric Cost ($)'] = total_cost
        
            # re-save metrics file
            df = pd.DataFrame(ochre_metrics.items(), columns=['Metric', 'Value'])
            df.to_csv(os.path.join(output_folder, building + '_metrics.csv'))


#%%
        