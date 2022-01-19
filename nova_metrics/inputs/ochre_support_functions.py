import os
import numpy as np
import pandas as pd
import yaml
from nova_metrics.support.utils import load_post, not_none, get_dictionary_value, get_filename


def get_properties_file(file_path):
    # Assumes initial file structure, e.g. "city          = CA_RIVERSIDE-MUNI"
    d= {}
    # Open file and parse
    with open(file_path, 'r') as prop_file:
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
                    d[key] = eval(val)
                except (NameError, SyntaxError):
                    d[key] = val
            elif len(line_split) > 2:
                # convert to dict (all should be floats)
                line_list = '='.join(line_split[1:]).split('   ')
                line_list = [tuple(s.split('=')) for s in line_list]
                d[key] = {k.strip(): float(v.strip()) for (k, v) in line_list}
    out_vals = ['heating fuel', 'heating number of speeds', 'heating fan power (W/cfm)', 'heating airflow rate (cfm)',
                'heating capacity (W)', 'heating EIR', 'heating duct dse', 'cooling fuel', 'cooling number of speeds',
                'cooling fan power (W/cfm)', 'cooling airflow rate (cfm)', 'cooling capacity (W)', 'cooling EIR',
                'cooling duct dse', 'water heater fuel', 'rated input power (W)', 'water heater type']
    out = {key: d[key] for key in out_vals}
    
    return out


def get_yaml_file(file_path):
    with open(file_path) as f:
        properties = yaml.safe_load(f)
        
        ['heating fuel', 'heating number of speeds', 'heating fan power (W/cfm)', 'heating airflow rate (cfm)',
                    'heating capacity (W)', 'heating EIR', 'heating duct dse', 'cooling fuel', 'cooling number of speeds',
                    'cooling fan power (W/cfm)', 'cooling airflow rate (cfm)', 'cooling capacity (W)', 'cooling EIR',
                    'cooling duct dse', 'water heater fuel', 'rated input power (W)', 'water heater type']
    out = {}
    out['heating fuel'] = properties["HVAC Heating"]["Fuel"]
    out['heating number of speeds'] = properties["HVAC Heating"]["Number of Speeds (-)"]
    out['heating fan power (W/cfm)'] = properties["HVAC Heating"]["Fan Power (W/cfm)"]
    out['heating airflow rate (cfm)'] = properties["HVAC Heating"]["Airflow Rate (cfm)"]
    out['heating capacity (W)'] = properties["HVAC Heating"]["Capacity (W)"]
    out['heating EIR'] = properties["HVAC Heating"]["EIR (-)"]
    out['heating duct dse'] = properties["HVAC Heating"]["Duct DSE (-)"]
    out['cooling fuel'] = properties["HVAC Cooling"]["Fuel"]
    out['cooling number of speeds'] = properties["HVAC Cooling"]["Number of Speeds (-)"]
    out['cooling fan power (W/cfm)'] = properties["HVAC Cooling"]["Fan Power (W/cfm)"]
    out['cooling airflow rate (cfm)'] = properties["HVAC Cooling"]["Airflow Rate (cfm)"]
    out['cooling capacity (W)'] = properties["HVAC Cooling"]["Capacity (W)"]
    out['cooling EIR'] = properties["HVAC Cooling"]["EIR (-)"]
    out['cooling duct dse'] = properties["HVAC Cooling"]["Duct DSE (-)"]
    out['water heater fuel'] = properties["Water Heating"]["Fuel"]
    out['rated input power (W)'] = properties["Water Heating"]["Capacity (W)"]
    out['water heater type'] = properties["HVAC Heating"]["Equipment Name"]
    return out




def parse_properties(file_path):
    if file_path.endswith(".properties"):
        prop_values = get_properties_file(file_path)
    elif file_path.endswith(".yaml"):
        prop_values = get_yaml_file(file_path)
    else:
        #TODO work on better error message
        print("The properties file must be a .properties or .yaml extension")
        return {}
    
    out = {}
    out["heating fuel"] = prop_values["heating fuel"]
    out["cooling fuel"] = prop_values["cooling fuel"]
    heating_speed = prop_values["heating number of speeds"] -1 
    cooling_speed = prop_values["cooling number of speeds"] -1 

    out["hp_dse"] = prop_values['heating duct dse']
    out["hp_size_heat"] = prop_values['heating capacity (W)'][heating_speed] / 1000

    if prop_values['heating fuel'] in ['Electric', "Electricity"]:
        out["hp_size_kw"] = (prop_values['heating capacity (W)'][heating_speed] * 
                      prop_values['heating EIR'][heating_speed]) / 1000
        
        out["hp_fan_power_ratio"] = (prop_values['heating fan power (W/cfm)'] * prop_values['heating airflow rate (cfm)'][heating_speed]) / \
                             (prop_values['heating capacity (W)'][heating_speed] * prop_values['heating EIR'][heating_speed])

        
    else:
        out["hp_size_kw"] = (prop_values['heating capacity (W)'][heating_speed] / 
                      prop_values['heating EIR'][heating_speed]) / 1000
        
        out["hp_fan_power_ratio"] = 0
    
    ###                         
    out["ac_dse"] = prop_values['cooling duct dse']
    
    if prop_values['cooling fuel'] in ['Electric', "Electricity"]:
        out["ac_size_kw"] = (prop_values['cooling capacity (W)'][cooling_speed] *
                      prop_values['cooling EIR'][cooling_speed]) / 1000
        out["ac_size_heat"] = prop_values['cooling capacity (W)'][cooling_speed] / 1000
        
        out["ac_fan_power_ratio"] = (prop_values['cooling fan power (W/cfm)'] * prop_values['cooling airflow rate (cfm)'][cooling_speed]) / \
                             (prop_values['cooling capacity (W)'][cooling_speed] * prop_values['cooling EIR'][cooling_speed])
    else:
        print('ERROR: non-electric cooling!')
        out["ac_size_kw"] = 0
        out["ac_size_heat"] = 0
        out["ac_fan_power_ratio"] = 0
    
    ###
    # Determine the size of the WH
    out["erwh_size_kw"] = 0.0
    out["hpwh_size_kw"] = 0.0

    if prop_values['water heater fuel'] in ['Electric', "Electricity"]:
        out["erwh_size_kw"] = prop_values['rated input power (W)']/1000
    if prop_values['water heater type'] == 'Heatpump':
        out["hpwh_size_kw"] = 0.4
    return out

def load_ochre_outputs(file_path_name, ochre_controls):
    """
    Return list of OCHRE building model output results.
    
    `file_path_name` is path to OCHRE output folder relative to OCHRE main folder. 
    `ochre_controls` is a dictionary which can contain specifications for string to match filenames.
    OCHRE output folder filenames default to:
        properties_file - .properties
        envelope_matrixA - _Envelope_matrixA.csv
        envelope_matrixB - _Envelope_matrixB.csv
        hourly_inputs - _hourly.csv
        water_tank_matrixA - _Water Tank_matrixA.csv
        water_tank_matrixB - _Water Tank_matrixB.csv

    Returns a list of [parsed_prop, a_matrix, b_matrix, hourly_inputs, a_matrix_wh, b_matrix_wh]
    """
    if ochre_controls.get("ochre_outputs_main_folder"):
        ochre_output_file_path = os.path.join(ochre_controls["ochre_outputs_main_folder"], file_path_name)
    else:
        ochre_output_file_path = file_path_name
        
    if ochre_controls.get("ochre_inputs_main_folder"):
        ochre_input_file_path = os.path.join(ochre_controls["ochre_inputs_main_folder"], file_path_name)
    else:
        ochre_input_file_path = file_path_name
    
    properties_file_key = get_dictionary_value(ochre_controls, "properties_file", ".yaml")
    envelope_matrixA_key = get_dictionary_value(ochre_controls, "envelope_matrixA", "_Envelope_matrixA.csv")
    envelope_matrixB_key = get_dictionary_value(ochre_controls, "envelope_matrixB", "_Envelope_matrixB.csv")
    hourly_inputs_key = get_dictionary_value(ochre_controls, "hourly_inputs", "_hourly.csv")
    water_tank_matrixA_key = get_dictionary_value(ochre_controls, "water_tank_matrixA", "_Water Tank_matrixA.csv")
    water_tank_matrixB_key = get_dictionary_value(ochre_controls, "water_tank_matrixB", "_Water Tank_matrixB.csv")
    
    
    properties_file = get_filename(ochre_input_file_path, properties_file_key)           
    parsed_prop = parse_properties(os.path.join(ochre_input_file_path, properties_file))
    
    a_matrix_file = get_filename(ochre_output_file_path, envelope_matrixA_key)
    b_matrix_file = get_filename(ochre_output_file_path, envelope_matrixB_key)
    hourly_inputs_file = get_filename(ochre_output_file_path, hourly_inputs_key)
    a_matrix_wh_file = get_filename(ochre_output_file_path, water_tank_matrixA_key)
    b_matrix_wh_file = get_filename(ochre_output_file_path, water_tank_matrixB_key)

    a_matrix = pd.read_csv(os.path.join(ochre_output_file_path, a_matrix_file), index_col=0)
    b_matrix = pd.read_csv(os.path.join(ochre_output_file_path, b_matrix_file), index_col=0)
    hourly_inputs = pd.read_csv(os.path.join(ochre_output_file_path, hourly_inputs_file))
    a_matrix_wh = pd.read_csv(os.path.join(ochre_output_file_path, a_matrix_wh_file), index_col=0)
    b_matrix_wh = pd.read_csv(os.path.join(ochre_output_file_path, b_matrix_wh_file), index_col=0)
    
    return [parsed_prop, a_matrix, b_matrix, hourly_inputs, a_matrix_wh, b_matrix_wh]

def wh_post(post, ochre_outputs, ochre_controls):
    wh_injection_node_col = 'H_WH1'
    #Adds relevant post information for water heater dispatch
    parsed_prop, a_matrix, b_matrix, hourly_inputs, a_matrix_wh, b_matrix_wh = ochre_outputs
    erwh_size_kw = parsed_prop["erwh_size_kw"]
    hpwh_size_kw = parsed_prop["hpwh_size_kw"]
    
    wh_temperature_lower_bound = get_dictionary_value(ochre_controls, "wh_temperature_lower_bound", 30)
    wh_temperature_upper_bound = get_dictionary_value(ochre_controls, "wh_temperature_upper_bound", 60)
    wh_comfort_temp_limit = get_dictionary_value(ochre_controls, "wh_comfort_temp_limit", 43)
    
    if (erwh_size_kw + hpwh_size_kw) > 0.01:
        wh_load = list(hourly_inputs.loc[:, 'Water Heating Electric Power (kW)'])
        post['Scenario']['Site']['LoadProfile']['loads_kw'] = [post['Scenario']['Site']['LoadProfile']['loads_kw'][i] - wh_load[i] for i in range(len(wh_load))]

        init_temperatures_wh = hourly_inputs.loc[:, a_matrix_wh.keys()]
        init_temperatures_wh = list(init_temperatures_wh.iloc[0])
        if hpwh_size_kw > 0.01:
            hpwh_cop = list(hourly_inputs.loc[:, 'Water Heating Electric Power (kW)'])
            hpwh_prodfactor = list(hourly_inputs.loc[:, 'Water Heating Heat Pump Max Capacity (kW)'] / hpwh_size_kw)
        else:
            hpwh_cop = []
            hpwh_prodfactor = []
            init_temperatures_wh = []
            
        n_temp_nodes_wh = a_matrix_wh.shape[1]
        n_input_nodes_wh = b_matrix_wh.shape[1]
        wh_injection_node_num = b_matrix_wh.columns.get_loc(wh_injection_node_col) + 1
        water_node_num = a_matrix_wh.columns.get_loc('T_WH1') + 1
    
        u_inputs_wh = hourly_inputs.loc[:, b_matrix_wh.keys()]
        u_inputs_wh.loc[:, wh_injection_node_col] = u_inputs_wh.loc[:, wh_injection_node_col] - \
                                                    hourly_inputs.loc[:, 'Water Heating Delivered (kW)'] * 1000
                                                    
        a_matrix_wh = list(a_matrix_wh.T.stack().reset_index(name='new')['new'])
        b_matrix_wh = list(b_matrix_wh.T.stack().reset_index(name='new')['new'])
        u_inputs_wh = list(u_inputs_wh.T.stack().reset_index(name='new')['new'])
    else:
        a_matrix_wh = []
        b_matrix_wh = []
        u_inputs_wh = []
        
        
        
    #TODO check what this does
    # post['Scenario']['Site']['RC']['use_flexloads_model'] = False
    if 'HotWaterTank' not in post['Scenario']['Site']:
        post['Scenario']['Site']['HotWaterTank'] = {}
        
    post['Scenario']['Site']['HotWaterTank']['a_matrix'] = a_matrix_wh
    post['Scenario']['Site']['HotWaterTank']['b_matrix'] = b_matrix_wh
    
    post['Scenario']['Site']['HotWaterTank']['u_inputs'] = u_inputs_wh
    
    post['Scenario']['Site']['HotWaterTank']['init_temperatures_degC'] = init_temperatures_wh
    post['Scenario']['Site']['HotWaterTank']['n_temp_nodes'] = n_temp_nodes_wh
    post['Scenario']['Site']['HotWaterTank']['n_input_nodes'] = n_input_nodes_wh
    post['Scenario']['Site']['HotWaterTank']['injection_node'] = wh_injection_node_num
    post['Scenario']['Site']['HotWaterTank']['water_node'] = water_node_num
    post['Scenario']['Site']['HotWaterTank']['temperature_lower_bound_degC'] = wh_temperature_lower_bound
    post['Scenario']['Site']['HotWaterTank']['temperature_upper_bound_degC'] = wh_temperature_upper_bound
    post['Scenario']['Site']['HotWaterTank']['comfort_temp_limit_degC'] = wh_comfort_temp_limit
        
    if 'FlexTechERWH' not in post['Scenario']['Site']:
        post['Scenario']['Site']['FlexTechERWH'] = {}
        
    if 'FlexTechHPWH' not in post['Scenario']['Site']:
        post['Scenario']['Site']['FlexTechHPWH'] = {}
    
    post['Scenario']['Site']['FlexTechERWH']['size_kw'] = erwh_size_kw
    post['Scenario']['Site']['FlexTechHPWH']['size_kw'] = hpwh_size_kw
    post['Scenario']['Site']['FlexTechHPWH']['prod_factor_series_kw'] = hpwh_prodfactor
    post['Scenario']['Site']['FlexTechHPWH']['cop'] = hpwh_cop
    return None


def hvac_post(post, ochre_outputs, ochre_controls):
    n_timesteps = 8760
    hvac_injection_node_col = 'H_LIV'
    #Add relevant post information for HVAC dispatch
    parsed_prop, a_matrix, b_matrix, hourly_inputs, a_matrix_wh, b_matrix_wh = ochre_outputs
    
    
    hvac_temperature_lower_bound = get_dictionary_value(ochre_controls, "hvac_temperature_lower_bound", 19.56)
    hvac_temperature_upper_bound = get_dictionary_value(ochre_controls, "hvac_temperature_upper_bound", 25.6)
    hvac_comfort_temp_lower_bound = get_dictionary_value(ochre_controls, "hvac_comfort_temp_lower_bound", 0)
    hvac_comfort_temp_upper_bound = get_dictionary_value(ochre_controls, "hvac_comfort_temp_upper_bound", 40)
    
    hvac_load = hourly_inputs.loc[:, 'HVAC Heating Electric Power (kW)'] + hourly_inputs.loc[:, 'HVAC Cooling Electric Power (kW)']
    init_temperatures_hvac = hourly_inputs.loc[:, a_matrix.keys()]
    init_temperatures_hvac = list(init_temperatures_hvac.iloc[0])
    ac_shr = list(hourly_inputs.loc[:, 'HVAC Cooling SHR (-)'])

    
    if parsed_prop['heating fuel'] in ['Electric', "Electricity"]:
        hp_cop = list(hourly_inputs.loc[:, 'HVAC Heating COP (-)'])
        try:
            er_on = hourly_inputs.loc[:, 'HVAC Heating ER Power (kW)']
        except:
            print('No ER element.')
            er_on = pd.Series([-1]*n_timesteps)
    else:
        constant_heating_cop = get_fan_adjustment(hourly_inputs.loc[:, 'HVAC Heating Delivered (kW)'], hourly_inputs.loc[:, 'HVAC Heating Fan Power (kW)'])
        hp_cop = [constant_heating_cop/parsed_prop["ac_dse"]]*n_timesteps
        er_on = pd.Series([-1]*n_timesteps) 
        
    if parsed_prop['cooling fuel'] in ['Electric', "Electricity"]:
        ac_cop = list(hourly_inputs.loc[:, 'HVAC Cooling COP (-)'])
    else:
        print('ERROR: non-electric cooling!')
    
    # HVAC RC characteristics    
    n_temp_nodes_hvac = a_matrix.shape[1]
    n_input_nodes_hvac = b_matrix.shape[1]
    hvac_injection_node_num = b_matrix.columns.get_loc(hvac_injection_node_col) + 1
    space_node_num = a_matrix.columns.get_loc('T_LIV') + 1
    
    u_inputs = hourly_inputs.loc[:, b_matrix.keys()]
    u_inputs.loc[:, hvac_injection_node_col] = u_inputs.loc[:, hvac_injection_node_col] + \
                                                hourly_inputs.loc[:, 'HVAC Cooling Delivered (kW)'] * 1000 - \
                                                hourly_inputs.loc[:, 'HVAC Heating Delivered (kW)'] * 1000
    # Convert matrices to lists for API input
    a_matrix = list(a_matrix.T.stack().reset_index(name='new')['new'])
    b_matrix = list(b_matrix.T.stack().reset_index(name='new')['new'])
    u_inputs = list(u_inputs.T.stack().reset_index(name='new')['new'])                                                

    #    
    ac_prodfactor = hourly_inputs.loc[:, 'HVAC Cooling Max Capacity (kW)'] / parsed_prop["ac_size_heat"]
    hp_prodfactor = hourly_inputs.loc[:, 'HVAC Heating Max Capacity (kW)'] / parsed_prop["hp_size_heat"]

    # Zero out prodfactors where necessary to ensure heating and cooling cannot occur simultaneously
#        space_cond = u_inputs.loc[:, hvac_injection_node_col]
#        ac_prodfactor[space_cond < -500] = 0.01
#        hp_prodfactor[space_cond > 500] = 0.01
    hp_prodfactor[er_on > 0] = 5.0
    ac_prodfactor = list(ac_prodfactor)
    hp_prodfactor = list(hp_prodfactor)
#        print(max(ac_prodfactor), min(ac_prodfactor), max(hp_prodfactor), min(hp_prodfactor))
    

    if "RC" not in post['Scenario']['Site']:
        post['Scenario']['Site']["RC"] = {}
        
    if "FlexTechAC" not in post['Scenario']['Site']:
        post['Scenario']['Site']["FlexTechAC"] = {}
    if "FlexTechFP" not in post['Scenario']['Site']:
        post['Scenario']['Site']["FlexTechHP"] = {}
        
    post['Scenario']['Site']['LoadProfile']['loads_kw'] = [post['Scenario']['Site']['LoadProfile']['loads_kw'][i] - hvac_load[i] for i in range(len(hvac_load))]
    post['Scenario']['Site']['RC']['use_flexloads_model'] = True
    post['Scenario']['Site']['RC']['a_matrix'] = a_matrix
    post['Scenario']['Site']['RC']['b_matrix'] = b_matrix
    post['Scenario']['Site']['RC']['u_inputs'] = u_inputs
    post['Scenario']['Site']['RC']['init_temperatures'] = init_temperatures_hvac
    post['Scenario']['Site']['RC']['n_temp_nodes'] = n_temp_nodes_hvac
    post['Scenario']['Site']['RC']['n_input_nodes'] = n_input_nodes_hvac
    post['Scenario']['Site']['RC']['injection_node'] = hvac_injection_node_num
    post['Scenario']['Site']['RC']['space_node'] = space_node_num
    post['Scenario']['Site']['RC']['temperature_lower_bound'] = hvac_temperature_lower_bound
    post['Scenario']['Site']['RC']['temperature_upper_bound'] = hvac_temperature_upper_bound
    post['Scenario']['Site']['RC']['comfort_temp_lower_bound_degC'] = hvac_comfort_temp_lower_bound
    post['Scenario']['Site']['RC']['comfort_temp_upper_bound_degC'] = hvac_comfort_temp_upper_bound
    
    post['Scenario']['Site']['FlexTechAC']['min_kw'] = parsed_prop["ac_size_kw"]
    post['Scenario']['Site']['FlexTechAC']['max_kw'] = parsed_prop["ac_size_kw"]
    post['Scenario']['Site']['FlexTechAC']['shr'] = ac_shr
    post['Scenario']['Site']['FlexTechAC']['prod_factor_series_kw'] = ac_prodfactor
    post['Scenario']['Site']['FlexTechAC']['cop'] = ac_cop
    post['Scenario']['Site']['FlexTechAC']['dse'] = parsed_prop["ac_dse"]
    post['Scenario']['Site']['FlexTechAC']['fan_power_ratio'] = parsed_prop["ac_fan_power_ratio"]

    post['Scenario']['Site']['FlexTechHP']['min_kw'] = parsed_prop["hp_size_kw"]
    post['Scenario']['Site']['FlexTechHP']['max_kw'] = parsed_prop["hp_size_kw"]
    post['Scenario']['Site']['FlexTechHP']['prod_factor_series_kw'] = hp_prodfactor
    post['Scenario']['Site']['FlexTechHP']['cop'] = hp_cop
    post['Scenario']['Site']['FlexTechHP']['dse'] = parsed_prop["ac_dse"]
    post['Scenario']['Site']['FlexTechHP']['fan_power_ratio'] = parsed_prop["hp_fan_power_ratio"]
    return None
    

        
        

    
def get_fan_adjustment(fan_power_series, main_power_series):
    ratio=fan_power_series/main_power_series
    ratio=ratio.replace([np.inf, -np.inf], np.nan)
    ratio=ratio.dropna()
    if round(max(ratio),4) != round(min(ratio),4):
        print('Different fan power ratios:', max(ratio), min(ratio))
    return max(ratio)
 

# def get_hvac_inputs(parsed_prop, hourly_inputs, hp_cop_col, ac_cop_col, hp_delivered_col, hp_fan_power_col, hp_er_col, n_timesteps=8760, er_on_by_days=False):     
    
#     if parsed_prop['heating fuel'] == 'Electric':
#         hp_cop = list(hourly_inputs.loc[:, hp_cop_col])
#         heating_speed = parsed_prop['heating number of speeds']-1
#         hp_fan_power_ratio = (parsed_prop['heating fan power (W/cfm)'] * parsed_prop['heating airflow rate (cfm)'][heating_speed]) / \
#                              (parsed_prop['heating capacity (W)'][heating_speed] * parsed_prop['heating EIR'][heating_speed])
#         hp_dse = parsed_prop['heating duct dse']
        
#         try:
#             if er_on_by_days:
#                 er_on = hourly_inputs[[hp_er_col]].copy()
#                 er_on.index = pd.to_datetime(hourly_inputs['Time'])
                
#                 days = er_on.resample('1D').sum()
#                 cold_days = days[days[hp_er_col]>0].index
                
#                 for cold_day in cold_days:
#                     er_on[er_on.index.date == cold_day] = 10
                    
#                 er_on.index = range(n_timesteps)
#                 er_on = er_on[hp_er_col]
#             else:
#                 er_on = hourly_inputs.loc[:, hp_er_col]
#         except:
#             print('No ER element.')
#             er_on = pd.Series([-1]*n_timesteps)
#     else:
#         hp_dse = parsed_prop['heating duct dse']
#         constant_heating_cop = get_fan_adjustment(hourly_inputs.loc[:, hp_delivered_col], hourly_inputs.loc[:, hp_fan_power_col])
#         hp_cop = [constant_heating_cop/hp_dse]*n_timesteps
#         hp_fan_power_ratio = 0
#         er_on = pd.Series([-1]*n_timesteps) 
        
#     if parsed_prop['cooling fuel'] == 'Electric':
#         ac_cop = list(hourly_inputs.loc[:, ac_cop_col])
#         cooling_speed = parsed_prop['cooling number of speeds']-1
#         ac_fan_power_ratio = (parsed_prop['cooling fan power (W/cfm)'] * parsed_prop['cooling airflow rate (cfm)'][cooling_speed]) / \
#                              (parsed_prop['cooling capacity (W)'][cooling_speed] * parsed_prop['cooling EIR'][cooling_speed])
#         ac_dse = parsed_prop['cooling duct dse']
#     else:
#         print('ERROR: non-electric cooling!')
    
#     return ac_cop, hp_cop, ac_fan_power_ratio, hp_fan_power_ratio, ac_dse, hp_dse, er_on
        

# def get_properties(properties_file):
#     with open(properties_file) as f:
#         properties = yaml.safe_load(f)
        
#     heating_speed = properties["HVAC Heating"]["Number of Speeds (-)"]-1 #Not sure if the minus 1 is needed
#     cooling_speed = properties["HVAC Heating"]["Number of Speeds (-)"]-1 #Not sure if the minus 1 is needed

#     if properties['HVAC Heating']["Fuel"] == 'Electric':
#         hp_size_kw = (properties["HVAC Heating"]['Capacity (W)'][heating_speed] * 
#                       properties['HVAC Heating']["EIR (-)"][heating_speed]) / 1000
#     else:
#         hp_size_kw = (properties["HVAC Heating"]['Capacity (W)'][heating_speed] / 
#                       properties['HVAC Heating']["EIR (-)"][heating_speed]) / 1000
    
#     hp_size_heat = properties["HVAC Heating"]['Capacity (W)'][heating_speed] / 1000
                             
#     if properties["HVAC Cooling"]['Fuel'] == 'Electric':
#         ac_size_kw = (properties["HVAC Cooling"]['cooling capacity (W)'][cooling_speed] *
#                       properties["HVAC Cooling"]['EIR (-)'][cooling_speed]) / 1000
#         ac_size_heat = properties["HVAC Cooling"]["cooling capacity (W)"][cooling_speed] / 1000
#     else:
#         print('ERROR: non-electric cooling!')
#         ac_size_kw = 0
#         ac_size_heat = 0
    
#     erwh_size_kw = 0.0
#     hpwh_size_kw = 0.0

#     # Determine the size of the WH
#     if properties['Water Heating']["Fuel"] == 'Electric':
#         erwh_size_kw = properties["Water Heating"]['Capacity (W)']/1000
#     #TODO Test this line
#     if properties['Water Heating']["Equipment Name"] == 'heatpump':
#         hpwh_size_kw = 0.4
    
#     return ac_size_kw, hp_size_kw, ac_size_heat, hp_size_heat, erwh_size_kw, hpwh_size_kw    


