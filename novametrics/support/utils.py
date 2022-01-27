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


def get_filename(path, end_condition):
    filename = [f for f in os.listdir(path) if f.endswith(end_condition)]
    if len(filename) != 1:
        print('More than one file type matches condition')
    else:
        filename = filename[0]
    return filename


def load_post(path, filename):
    # Load a json into a python dictionary
    with open(os.path.join(path, filename), 'r') as fp:
        post = json.load(fp)
    return post


def save_post(post, path, filename):
    with open(os.path.join(path, filename), 'w') as fp:
        json.dump(post, fp, indent = 2)

    
def get_fan_adjustment(fan_power_series, main_power_series):
    ratio=fan_power_series/main_power_series
    ratio=ratio.replace([np.inf, -np.inf], np.nan)
    ratio=ratio.dropna()
    if round(max(ratio),4) != round(min(ratio),4):
        print('Different fan power ratios:', max(ratio), min(ratio))
    return max(ratio)
 
def get_cop(parsed_prop, hourly_inputs, hp_cop_col, ac_cop_col, hp_delivered_col, hp_fan_power_col, n_timesteps=8760):     
    
    if parsed_prop['heating fuel'] == 'Electric':
        heating_speed = parsed_prop['heating number of speeds']-1
        hp_fan_power_ratio = (parsed_prop['heating fan power (W/cfm)'] * parsed_prop['heating airflow rate (cfm)'][heating_speed]) / \
                             (parsed_prop['heating capacity (W)'][heating_speed] * parsed_prop['heating EIR'][heating_speed])
        cop_factor_heating = (((1/parsed_prop['heating EIR'][heating_speed]) + hp_fan_power_ratio) / (1 + hp_fan_power_ratio)) / \
                             (1/parsed_prop['heating EIR'][heating_speed])
        if cop_factor_heating > (1/parsed_prop['heating EIR'][heating_speed]):
            print('Check HVAC heating!')
        hp_cop = list(hourly_inputs.loc[:, hp_cop_col]*cop_factor_heating)
    else:
        constant_heating_cop = get_fan_adjustment(hourly_inputs.loc[:, hp_delivered_col], hourly_inputs.loc[:, hp_fan_power_col])
        hp_cop = [constant_heating_cop]*n_timesteps
        
    if parsed_prop['cooling fuel'] == 'Electric':
        cooling_speed = parsed_prop['cooling number of speeds']-1
        ac_fan_power_ratio = (parsed_prop['cooling fan power (W/cfm)'] * parsed_prop['cooling airflow rate (cfm)'][cooling_speed]) / \
                             (parsed_prop['cooling capacity (W)'][cooling_speed] * parsed_prop['cooling EIR'][cooling_speed])
        cop_factor_cooling = (((1/parsed_prop['cooling EIR'][cooling_speed]) - ac_fan_power_ratio) / (1 + ac_fan_power_ratio)) / \
                             (1/parsed_prop['cooling EIR'][cooling_speed])
        ac_cop = list(hourly_inputs.loc[:, ac_cop_col]*cop_factor_cooling)
    else:
        print('ERROR: non-electric cooling!')
    
    return ac_cop, hp_cop

def get_hvac_inputs(parsed_prop, hourly_inputs, hp_cop_col, ac_cop_col, hp_delivered_col, hp_fan_power_col, hp_er_col, n_timesteps=8760, er_on_by_days=False):     
    
    if parsed_prop['heating fuel'] == 'Electric':
        hp_cop = list(hourly_inputs.loc[:, hp_cop_col])
        heating_speed = parsed_prop['heating number of speeds']-1
        hp_fan_power_ratio = (parsed_prop['heating fan power (W/cfm)'] * parsed_prop['heating airflow rate (cfm)'][heating_speed]) / \
                             (parsed_prop['heating capacity (W)'][heating_speed] * parsed_prop['heating EIR'][heating_speed])
        hp_dse = parsed_prop['heating duct dse']
        
        try:
            if er_on_by_days:
                er_on = hourly_inputs[[hp_er_col]].copy()
                er_on.index = pd.to_datetime(hourly_inputs['Time'])
                
                days = er_on.resample('1D').sum()
                cold_days = days[days[hp_er_col]>0].index
                
                for cold_day in cold_days:
                    er_on[er_on.index.date == cold_day] = 10
                    
                er_on.index = range(n_timesteps)
                er_on = er_on[hp_er_col]
            else:
                er_on = hourly_inputs.loc[:, hp_er_col]
        except:
            print('No ER element.')
            er_on = pd.Series([-1]*n_timesteps)
    else:
        hp_dse = parsed_prop['heating duct dse']
        constant_heating_cop = get_fan_adjustment(hourly_inputs.loc[:, hp_delivered_col], hourly_inputs.loc[:, hp_fan_power_col])
        hp_cop = [constant_heating_cop/hp_dse]*n_timesteps
        hp_fan_power_ratio = 0
        er_on = pd.Series([-1]*n_timesteps) 
        
    if parsed_prop['cooling fuel'] == 'Electric':
        ac_cop = list(hourly_inputs.loc[:, ac_cop_col])
        cooling_speed = parsed_prop['cooling number of speeds']-1
        ac_fan_power_ratio = (parsed_prop['cooling fan power (W/cfm)'] * parsed_prop['cooling airflow rate (cfm)'][cooling_speed]) / \
                             (parsed_prop['cooling capacity (W)'][cooling_speed] * parsed_prop['cooling EIR'][cooling_speed])
        ac_dse = parsed_prop['cooling duct dse']
    else:
        print('ERROR: non-electric cooling!')
    
    return ac_cop, hp_cop, ac_fan_power_ratio, hp_fan_power_ratio, ac_dse, hp_dse, er_on
        

def get_system_sizes(parsed_prop):
    
    heating_speed = parsed_prop['heating number of speeds']-1
    cooling_speed = parsed_prop['cooling number of speeds']-1
    
    if parsed_prop['heating fuel'] == 'Electric':
        hp_size_kw = (parsed_prop['heating capacity (W)'][heating_speed] * 
                      parsed_prop['heating EIR'][heating_speed]) / 1000
    else:
        hp_size_kw = (parsed_prop['heating capacity (W)'][heating_speed] / 
                      parsed_prop['heating EIR'][heating_speed]) / 1000
    
    hp_size_heat = parsed_prop['heating capacity (W)'][heating_speed] / 1000
                             
    if parsed_prop['cooling fuel'] == 'Electric':
        ac_size_kw = (parsed_prop['cooling capacity (W)'][cooling_speed] *
                      parsed_prop['cooling EIR'][cooling_speed]) / 1000
        ac_size_heat = parsed_prop['cooling capacity (W)'][cooling_speed] / 1000
    else:
        print('ERROR: non-electric cooling!')
        ac_size_kw = 0
        ac_size_heat = 0
        
    erwh_size_kw = 0.0
    hpwh_size_kw = 0.0

    # Determine the size of the WH
    if parsed_prop['water heater fuel'] == 'Electric':
        erwh_size_kw = parsed_prop['rated input power (W)']/1000
    if parsed_prop['water heater type'] == 'Heatpump':
        hpwh_size_kw = 0.4

    return ac_size_kw, hp_size_kw, ac_size_heat, hp_size_heat, erwh_size_kw, hpwh_size_kw
 
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