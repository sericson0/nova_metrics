# import sys
# sys.path.insert(1, './ochre/ochre')
# import os
# from shutil import copyfile
# import pandas as pd
# import datetime as dt
# from ochre import Dwelling
# import pathlib

# from nova_metrics.apiquery.download_nsrdb import download_nsrdb
#%%
#run_ochre_case runs a single OCHRE file. 
# -If needed weather file is downloaded from NSRDB. 
# -runs OCHRE and saves to OCHRE Outputs folder
#
#main_folder: filepath to folder for batch runs. OCHRE Inputs must be a folder within main_folder
#Inputs is a dictionary of inputs 
#Location is character of locations, building is character of building type
#api_keys is a dictionary that needs nrel_api_key if weather file being downloaded 
#If overwrite == TRUE then all ochre files replaced, otherwise only load if not ochre files currently exist in folder


# def run_ochre_case(main_folder, inputs, location, building, api_keys = {}, overwrite_files = False):
#     #Converts relative path to absolute path
#     main_folder = pathlib.Path(main_folder).resolve()
#     location_inputs_folder = os.path.join(main_folder, 'OCHRE Inputs', location)
#     location_vals = inputs["Locations"][location]["Post Values"]

#     if "ochre" in inputs["Locations"][location]["Buildings"][building]:
#         building_vals = inputs["Locations"][location]["Buildings"][building]["ochre"]
#     else:
#         building_vals = {}
#     #Download weather file. Currently name, email, affiliation, and reason for download are dummies. Check if these need to be acutal values
#     ochre_weather_file = os.path.join(location_inputs_folder, location + " Weather File")
#     if os.path.isfile(ochre_weather_file+ ".epw"):
#         ochre_weather_file = ochre_weather_file + ".epw"
#     else:
#         ochre_weather_file = ochre_weather_file + ".csv"
#         if not os.path.isfile(ochre_weather_file):
#             print("Downloading weather file for ", location)
#             download_nsrdb(ochre_weather_file, location_vals["latitude"], location_vals["longitude"], api_keys["nrel_api_key"])
#     # case_folder = os.path.join(main_folder, 'OCHRE Inputs', location + ' Case Study', *case_sub_folders)
#     properties_file = os.path.join(location_inputs_folder, building, building + '_rc_model.properties')
#     schedule_file = os.path.join(location_inputs_folder, building, building + '_schedule.properties')
#     # eplus_file = os.path.join(location_inputs_folder, building, building + '_EnergyPlus_Hourly.csv')
#     ochre_rate_file = os.path.join(location_inputs_folder, building, ' Rate.csv')
#     ochre_water_draw_file = os.path.join(location_inputs_folder, building, building + "_water_file.csv")
    
#     output_folder = os.path.join(main_folder, "OCHRE Outputs", location, building)    
    
#     pathlib.Path(output_folder).mkdir(parents=True, exist_ok=True)
    
#     if "time_res" in building_vals:
#         time_res = building_vals["time_res"]
#     else:
#         time_res = 10
        
#     if "equipment" in building_vals:
#         equip = building_vals["equipment"]
#     else:
#         equip = {}
    
#     if "add_costs" in building_vals:
#         add_costs = building_vals["add_costs"]
#     else:
#         add_costs = False   
    
#     dwelling_args = {
#         # Timing parameters
#         'start_time': dt.datetime(2019, 1, 1, 0, 0),  # year, month, day, hour, minute
#         'time_res': dt.timedelta(minutes=time_res),  # Note: OR WH cases run at 1 minute resolution, rest at 10 minute
#         'duration': dt.timedelta(days=365),
#         'initialization_time': dt.timedelta(days=7),
    
#         # Input parameters
#         'output_path': output_folder,
#         'properties_file': properties_file,
#         'schedule_file': schedule_file,
#         'weather_file': ochre_weather_file,
#         'water_draw_file': ochre_water_draw_file,
    
#         # Output parameters
#         'export_res': dt.timedelta(days=61),
#         'verbosity': 9,  # verbosity of results file (1-9)
#         'metrics_verbosity': 9,  # verbosity of metrics file (0-9)
    
#         # Other parameters
#         'assume_equipment': True,
#         # 'ext_time_res': dt.timedelta(minutes=15),
#         'save_matrices': True,
#         'save_matrices_time_res': dt.timedelta(hours=1),
#         'show_eir_shr': True,
#         # 'reduced_min_accuracy': 1,
#         # 'Indoor Thermal Mass Multiplier': 1,
#     }
#     equipment = equip
    
#     # Load E+ files
#     # eplus = Analysis.load_eplus_file(eplus_file)
    
#     # only keep a few days - note, datetime slicing is inclusive
#     # start = dwelling_args['start_time']
#     # end = start + dwelling_args['duration'] - dwelling_args['time_res']
#     # eplus = eplus.loc[start: end]

#     copyfile(os.path.join(location_inputs_folder, building, building + '_rc_model.properties'),
#              os.path.join(output_folder, building + '_rc_model.properties'))

#     if overwrite_files or len(os.listdir(output_folder)) == 0:
#         dwelling = Dwelling(building, equipment, **dwelling_args)
#         ochre_exact, ochre_metrics, ochre = dwelling.simulate()
#         ochre = ochre_exact.resample(dt.timedelta(hours=1)).mean()
#         ochre.reset_index().to_csv(dwelling.hourly_output_file, index=False)

#         dwelling = Dwelling(building, equipment, **dwelling_args)
#         ochre_exact, ochre_metrics, ochre = dwelling.simulate()
    
#         # recreate hourly file with all states and inputs
#         ochre = ochre_exact.resample(dt.timedelta(hours=1)).mean()
#         ochre.reset_index().to_csv(dwelling.hourly_output_file, index=False)
    
#         if add_costs:
#             # add electric energy cost for Oregon cases
#             rates = pd.read_csv(ochre_rate_file)['Utility Rate']
#             if len(rates) == len(ochre.index):
#                 rates.index = ochre.index
#                 total_cost = (ochre['Total Electric Power (kW)'] * rates).sum()
#                 ochre_metrics['Total Electric Cost ($)'] = total_cost
        
#             # re-save metrics file
#             df = pd.DataFrame(ochre_metrics.items(), columns=['Metric', 'Value'])
#             df.to_csv(os.path.join(output_folder, building + '_metrics.csv'))


#%%
#run_ochre batch_runs run_ochre_cases
def run_ochre(main_folder, inputs, api_keys = {}, overwrite_files = False):
    pass
    #Will update once ResStock OCHRE connection is updated
    # print("Running OCHRE")
    # for location in inputs["Locations"]:
    #     print("Creating OCHRE outputs for", location)
    #     for building in inputs["Locations"][location]["Buildings"]:
    #         run_ochre_case(main_folder, inputs, location, building, api_keys, overwrite_files)
                                                                                                               