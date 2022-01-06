#!/usr/bin/env python
# coding: utf-8
import os 
import pandas as pd
from nova_metrics.support.utils import get_filename, parse_properties, get_system_sizes, get_hvac_inputs, not_none 
from nova_metrics.apiquery.download_pv_watts import download_pv_watts
# import collections.abc

#%%
# Column names in OCHRE output files
elec_load_col = 'Total Electric Power (kW)'
hvac_injection_node_col = 'H_LIV'
space_node_col = 'T_LIV'
wh_injection_node_col = 'H_WH1'
water_node_col = 'T_WH1'
ac_delivered_col = 'HVAC Cooling Delivered (kW)'
ac_consumption_col = 'HVAC Cooling Electric Power (kW)'
ac_capacity_col = 'HVAC Cooling Max Capacity (kW)'
ac_cop_col = 'HVAC Cooling COP (-)'
ac_shr_col = 'HVAC Cooling SHR (-)'
hp_delivered_col = 'HVAC Heating Delivered (kW)'
hp_consumption_col = 'HVAC Heating Electric Power (kW)'
hp_capacity_col = 'HVAC Heating Max Capacity (kW)'
hp_cop_col = 'HVAC Heating COP (-)'
wh_delivered_col = 'Water Heating Delivered (kW)'
wh_consumption_col = 'Water Heating Electric Power (kW)'
hpwh_capacity_col = 'Water Heating Heat Pump Max Power (kW)'
hpwh_cop_col = 'Water Heating Heat Pump COP (-)'
ac_fan_power_col = 'HVAC Cooling Fan Power (kW)'
ac_main_power_col = 'HVAC Cooling Main Power (kW)'
hp_fan_power_col = 'HVAC Heating Fan Power (kW)'
hp_main_power_col = 'HVAC Heating Main Power (kW)'
hp_er_col = 'HVAC Heating ER Power (kW)'
#%%
def load_ochre_outputs(file_path):
    """
    Return list of OCHRE building model output results.
    
    `file_path` is path to OCHRE output folder. 
    OCHRE output folder must have files with the following in their names:
        - .properties
        - _Envelope_matrixA.csv
        - _Water Tank_matrixA.csv
        - _Water Tank_matrixB.csv

    Returns a list of [parsed_prop, a_matrix, b_matrix, hourly_inputs, a_matrix_wh, b_matrix_wh]
    """
    properties_file = get_filename(file_path, '.properties')            
    parsed_prop = parse_properties(os.path.join(file_path, properties_file))
    
    # Read in RC matrices and timeseries inputs files 
    a_matrix_file = get_filename(file_path, '_Envelope_matrixA.csv')
    b_matrix_file = get_filename(file_path, '_Envelope_matrixB.csv')
    hourly_inputs_file = get_filename(file_path, '_hourly.csv')
    a_matrix_wh_file = get_filename(file_path, '_Water Tank_matrixA.csv')
    b_matrix_wh_file = get_filename(file_path, '_Water Tank_matrixB.csv')

    
    a_matrix = pd.read_csv(os.path.join(file_path, a_matrix_file), index_col=0)
    b_matrix = pd.read_csv(os.path.join(file_path, b_matrix_file), index_col=0)
    hourly_inputs = pd.read_csv(os.path.join(file_path, hourly_inputs_file))
    a_matrix_wh = pd.read_csv(os.path.join(file_path, a_matrix_wh_file), index_col=0)
    b_matrix_wh = pd.read_csv(os.path.join(file_path, b_matrix_wh_file), index_col=0)
    
    return [parsed_prop, a_matrix, b_matrix, hourly_inputs, a_matrix_wh, b_matrix_wh]

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
            
        
def wh_post(post, ochre_outputs, wh_temperature_lower_bound, wh_temperature_upper_bound, wh_comfort_temp_limit):
    #Adds relevant post information for water heater dispatch
    parsed_prop, a_matrix, b_matrix, hourly_inputs, a_matrix_wh, b_matrix_wh = ochre_outputs
    erwh_size_kw, hpwh_size_kw = get_system_sizes(parsed_prop)[-2:]
    
    
    if (erwh_size_kw + hpwh_size_kw) > 0.01:
        # ochre_outputs_to_reopt['wh_outlet_temp_degC'] = list(hourly_inputs.loc[:, 'Hot Water Outlet Temperature (C)'])
        # ochre_outputs_to_reopt['wh_heating_delivered_kw'] = list(hourly_inputs.loc[:, wh_delivered_col])
        # ochre_outputs_to_reopt['wh_elec_power_kw'] = list(hourly_inputs.loc[:, wh_consumption_col])
        
        wh_load = list(hourly_inputs.loc[:, wh_consumption_col])
        post['Scenario']['Site']['LoadProfile']['loads_kw'] = [post['Scenario']['Site']['LoadProfile']['loads_kw'][i] - wh_load[i] for i in range(len(wh_load))]
        
        init_temperatures_wh = hourly_inputs.loc[:, a_matrix_wh.keys()]
        init_temperatures_wh = list(init_temperatures_wh.iloc[0])
        
        if hpwh_size_kw > 0.01:
            hpwh_cop = list(hourly_inputs.loc[:, hpwh_cop_col])
            hpwh_prodfactor = list(hourly_inputs.loc[:, hpwh_capacity_col] / hpwh_size_kw)
        else:
            hpwh_cop = []
            hpwh_prodfactor = []
            
        n_temp_nodes_wh = a_matrix_wh.shape[1]
        n_input_nodes_wh = b_matrix_wh.shape[1]
        wh_injection_node_num = b_matrix_wh.columns.get_loc(wh_injection_node_col) + 1
        water_node_num = a_matrix_wh.columns.get_loc(water_node_col) + 1
    
        u_inputs_wh = hourly_inputs.loc[:, b_matrix_wh.keys()]
        u_inputs_wh.loc[:, wh_injection_node_col] = u_inputs_wh.loc[:, wh_injection_node_col] - \
                                                    hourly_inputs.loc[:, wh_delivered_col] * 1000
    
        a_matrix_wh = list(a_matrix_wh.T.stack().reset_index(name='new')['new'])
        b_matrix_wh = list(b_matrix_wh.T.stack().reset_index(name='new')['new'])
        u_inputs_wh = list(u_inputs_wh.T.stack().reset_index(name='new')['new'])

    # post['Scenario']['Site']['RC']['use_flexloads_model'] = False
    
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
        
    post['Scenario']['Site']['FlexTechERWH']['size_kw'] = erwh_size_kw
    post['Scenario']['Site']['FlexTechHPWH']['size_kw'] = hpwh_size_kw
    post['Scenario']['Site']['FlexTechHPWH']['prod_factor_series_kw'] = hpwh_prodfactor
    post['Scenario']['Site']['FlexTechHPWH']['cop'] = hpwh_cop
    
    return None


def hvac_post(post, ochre_outputs, hvac_temperature_lower_bound, hvac_temperature_upper_bound, hvac_comfort_temp_lower_bound, hvac_comfort_temp_upper_bound):
    #Add relevant post information for HVAC dispatch
    parsed_prop, a_matrix, b_matrix, hourly_inputs, a_matrix_wh, b_matrix_wh = ochre_outputs
    ac_size_kw, hp_size_kw, ac_size_heat, hp_size_heat, erwh_size_kw, hpwh_size_kw = get_system_sizes(parsed_prop)
    
    # Electric load net of the consumption of REopt controlled technologies
    hvac_load = hourly_inputs.loc[:, hp_consumption_col] + hourly_inputs.loc[:, ac_consumption_col]
    post['Scenario']['Site']['LoadProfile']['loads_kw'] = [post['Scenario']['Site']['LoadProfile']['loads_kw'][i] - hvac_load[i] for i in range(len(hvac_load))]
    # Get initial HVAC temperatures
    init_temperatures_hvac = hourly_inputs.loc[:, a_matrix.keys()]
    init_temperatures_hvac = list(init_temperatures_hvac.iloc[0])

    ac_cop, hp_cop, ac_fan_power_ratio, hp_fan_power_ratio, ac_dse, hp_dse, er_on = \
            get_hvac_inputs(parsed_prop, hourly_inputs, hp_cop_col, ac_cop_col, hp_delivered_col, hp_fan_power_col, hp_er_col)
        
    # AC SHR
    ac_shr = list(hourly_inputs.loc[:, ac_shr_col])

    # HVAC RC characteristics    
    n_temp_nodes_hvac = a_matrix.shape[1]
    n_input_nodes_hvac = b_matrix.shape[1]
    hvac_injection_node_num = b_matrix.columns.get_loc(hvac_injection_node_col) + 1
    space_node_num = a_matrix.columns.get_loc(space_node_col) + 1

    # HVAC injection node output contains all equipment gains (HVAC, water heater, lighting, appliances, etc.)
    # Subtract out REopt controlled equipment 
    u_inputs = hourly_inputs.loc[:, b_matrix.keys()]
    u_inputs.loc[:, hvac_injection_node_col] = u_inputs.loc[:, hvac_injection_node_col] + \
                                               hourly_inputs.loc[:, ac_delivered_col] * 1000 - \
                                               hourly_inputs.loc[:, hp_delivered_col] * 1000
    
    # HVAC production factors - normalize by nominal capacity
    ac_prodfactor = hourly_inputs.loc[:, ac_capacity_col] / ac_size_heat
    hp_prodfactor = hourly_inputs.loc[:, hp_capacity_col] / hp_size_heat

    # Zero out prodfactors where necessary to ensure heating and cooling cannot occur simultaneously
#        space_cond = u_inputs.loc[:, hvac_injection_node_col]
#        ac_prodfactor[space_cond < -500] = 0.01
#        hp_prodfactor[space_cond > 500] = 0.01
    hp_prodfactor[er_on > 0] = 5.0

    ac_prodfactor = list(ac_prodfactor)
    hp_prodfactor = list(hp_prodfactor)
#        print(max(ac_prodfactor), min(ac_prodfactor), max(hp_prodfactor), min(hp_prodfactor))
    
    # Convert matrices to lists for API input
    a_matrix = list(a_matrix.T.stack().reset_index(name='new')['new'])
    b_matrix = list(b_matrix.T.stack().reset_index(name='new')['new'])
    u_inputs = list(u_inputs.T.stack().reset_index(name='new')['new'])

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
    
    post['Scenario']['Site']['FlexTechAC']['min_kw'] = ac_size_kw
    post['Scenario']['Site']['FlexTechAC']['max_kw'] = ac_size_kw
    post['Scenario']['Site']['FlexTechAC']['shr'] = ac_shr
    post['Scenario']['Site']['FlexTechAC']['prod_factor_series_kw'] = ac_prodfactor
    post['Scenario']['Site']['FlexTechAC']['cop'] = ac_cop
    post['Scenario']['Site']['FlexTechAC']['dse'] = ac_dse
    post['Scenario']['Site']['FlexTechAC']['fan_power_ratio'] = ac_fan_power_ratio

    post['Scenario']['Site']['FlexTechHP']['min_kw'] = hp_size_kw
    post['Scenario']['Site']['FlexTechHP']['max_kw'] = hp_size_kw
    post['Scenario']['Site']['FlexTechHP']['prod_factor_series_kw'] = hp_prodfactor
    post['Scenario']['Site']['FlexTechHP']['cop'] = hp_cop
    post['Scenario']['Site']['FlexTechHP']['dse'] = hp_dse
    post['Scenario']['Site']['FlexTechHP']['fan_power_ratio'] = hp_fan_power_ratio
    
    return None
    


