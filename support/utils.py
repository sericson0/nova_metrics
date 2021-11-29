import os
import json
import pickle
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd 

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
    vol = out['building length (m)'] * out['building width (m)'] * out['ceiling height (m)'] * out['num stories']
    out['building volume (m^3)'] = vol
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
 
def get_REopt_post(a_matrix, b_matrix, hourly_inputs, a_matrix_wh, b_matrix_wh, hvac_temperature_lower_bound, hvac_temperature_upper_bound, 
                   wh_temperature_lower_bound, wh_temperature_upper_bound, wh_comfort_temp_limit, hvac_comfort_temp_lower_bound, 
                   hvac_comfort_temp_upper_bound, parsed_prop, post_path, post_filename, elec_load_col, hvac_injection_node_col, 
                   space_node_col, wh_injection_node_col, water_node_col, ac_delivered_col, ac_consumption_col, ac_capacity_col, 
                   ac_cop_col, ac_shr_col, hp_delivered_col, hp_consumption_col, hp_capacity_col, hp_cop_col, wh_delivered_col, 
                   wh_consumption_col, hpwh_capacity_col, hpwh_cop_col, ac_fan_power_col, ac_main_power_col, hp_fan_power_col, 
                   hp_main_power_col, urdb_label, techs_dict, prod_factor_file, ra_post, hp_er_col, custom_post=None, optional_load=None, 
                   data_4CP = None, comfort_cost = None, wh_only = False):
    
    if wh_only is True:
        erwh_size_kw, hpwh_size_kw = get_system_sizes(parsed_prop)[-2:]
        
        if (erwh_size_kw + hpwh_size_kw) > 0.01:
            load = list(hourly_inputs.loc[:, elec_load_col] - hourly_inputs.loc[:, wh_consumption_col])
            
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
        else:
            print('No WH for WH-ONLY scenario')    
            
    else:
        if techs_dict['HVAC'] is True:               
            ac_size_kw, hp_size_kw, ac_size_heat, hp_size_heat, erwh_size_kw, hpwh_size_kw = get_system_sizes(parsed_prop)
            
            # Electric load net of the consumption of REopt controlled technologies
            if (erwh_size_kw + hpwh_size_kw) > 0.01:
                load = list(hourly_inputs.loc[:, elec_load_col] - hourly_inputs.loc[:, hp_consumption_col] -
                            hourly_inputs.loc[:, ac_consumption_col] - hourly_inputs.loc[:, wh_consumption_col])
            else:
                load = list(hourly_inputs.loc[:, elec_load_col] - hourly_inputs.loc[:, hp_consumption_col] -
                            hourly_inputs.loc[:, ac_consumption_col])
        
            # Get initial HVAC temperatures
            init_temperatures_hvac = hourly_inputs.loc[:, a_matrix.keys()]
            init_temperatures_hvac = list(init_temperatures_hvac.iloc[0])
        
        #    # Adjust COP to consider fan power
        #    ac_fan_adj = get_fan_adjustment(hourly_inputs.loc[:, ac_fan_power_col], hourly_inputs.loc[:, ac_main_power_col])+1
        #    hp_fan_adj = get_fan_adjustment(hourly_inputs.loc[:, hp_fan_power_col], hourly_inputs.loc[:, hp_main_power_col])+1
        #    
        #    # HVAC COP
        #    ac_cop = list(hourly_inputs.loc[:, ac_cop_col]/ac_fan_adj)
        #    hp_cop = list(hourly_inputs.loc[:, hp_cop_col]/hp_fan_adj)
        #    ac_cop, hp_cop = get_cop(parsed_prop, hourly_inputs, hp_cop_col, ac_cop_col, hp_delivered_col, hp_fan_power_col, n_timesteps=8760)
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
    
            if sum(er_on)>0:
                print('ER ON')
                
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
        
            # Process water heater inputs
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
        else:
            if optional_load is not None:
                load = optional_load
            else:
                load = list(hourly_inputs.loc[:, elec_load_col])
        
    post = load_post(post_path, post_filename)
    
    post['Scenario']['Site']['LoadProfile']['loads_kw'] = load
    post['Scenario']['Site']['ElectricTariff']['net_metering_limit_kw'] = techs_dict['net_metering_limit_kw']
    if urdb_label == 'custom':
        post['Scenario']['Site']['ElectricTariff']['urdb_response'] = custom_post['urdb_response']
    else:    
        post['Scenario']['Site']['ElectricTariff']['urdb_label'] = urdb_label
    
    
    if ra_post is not None:
        for key in ra_post:
            post['Scenario']['Site']['ElectricTariff'][key] = ra_post[key]
    
    if data_4CP is not None:   
        for key in data_4CP:
            post['Scenario']['Site']['ElectricTariff'][key] = data_4CP[key]

    if comfort_cost is not None:   
        post['Scenario']['Site']['RC']['comfort_HVAC_value_usd_per_degC'] = comfort_cost
            
    for tech in techs_dict.keys():
        if tech not in ['HVAC','net_metering_limit_kw']:
            for val in techs_dict[tech]:
                post['Scenario']['Site'][tech][val] = techs_dict[tech][val]
    
    if post['Scenario']['Site']['PV']['max_kw'] > 0:
        df = pd.read_csv(os.path.join(post_path, prod_factor_file), header=None)
        post['Scenario']['Site']['PV']['prod_factor_series_kw'] = list(df[0])
      
    if wh_only is True:
        post['Scenario']['Site']['RC']['use_flexloads_model'] = False
        
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
        
    else:   
        if techs_dict['HVAC'] is True: 
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
        else:
            erwh_size_kw = 0
            hpwh_size_kw = 0
            post['Scenario']['Site']['RC']['use_flexloads_model'] = False
            post['Scenario']['Site']['FlexTechERWH']['size_kw'] = 0
            post['Scenario']['Site']['FlexTechHPWH']['size_kw'] = 0
        
    # Save some OCHRE outputs in REopt results
    ochre_outputs = {}
    ochre_outputs['indoor_temp_degC'] = list(hourly_inputs.loc[:, space_node_col])
    ochre_outputs['outdoor_temp_degC'] = list((hourly_inputs.loc[:, 'Temperature - Outdoor (C)'] * 9/5) + 32)
    ochre_outputs['hvac_cooling_delivered_kw'] = list(hourly_inputs.loc[:, ac_delivered_col])
    ochre_outputs['hvac_heating_delivered_kw'] = list(hourly_inputs.loc[:, hp_delivered_col])
    ochre_outputs['hvac_cooling_elec_power_kw'] = list(hourly_inputs.loc[:, ac_consumption_col])
    ochre_outputs['hvac_heating_elec_power_kw'] = list(hourly_inputs.loc[:, hp_consumption_col])
    
    if (erwh_size_kw + hpwh_size_kw) > 0.01:
        ochre_outputs['wh_outlet_temp_degC'] = list(hourly_inputs.loc[:, 'Hot Water Outlet Temperature (C)'])
        ochre_outputs['wh_heating_delivered_kw'] = list(hourly_inputs.loc[:, wh_delivered_col])
        ochre_outputs['wh_elec_power_kw'] = list(hourly_inputs.loc[:, wh_consumption_col])
    
    return post, ochre_outputs


def save_api_results(api_response, path, filename):
    with open(os.path.join(path, filename + '.pickle'), 'wb') as handle:
        pickle.dump(api_response, handle, protocol=pickle.HIGHEST_PROTOCOL)
      
    
def load_api_results(path, filename):
    with open(os.path.join(path, filename + '.pickle'), 'rb') as handle:
        api_response = pickle.load(handle)
    return api_response


def plot_temperatures(temperatures1, temperatures2, title1='OCHRE hot water outlet temperature', 
                      title2='REopt hot water tank temperature', ylabel='Temperature [Celsius]',
                      xlabel='Timestep', n_timestep=8760):

    x_axis = np.linspace(1,n_timestep,n_timestep)
    fig, ax = plt.subplots()
    plt.subplot(2,1,1)
    plt.plot(x_axis, temperatures1)
    plt.title(title1)
    plt.ylabel(ylabel)
    plt.grid(True)
    
    plt.subplot(2,1,2)
    plt.plot(x_axis, temperatures2)
    plt.plot([1, 8760], [23.3, 23.3], c='b')
    plt.plot([1, 8760], [25, 25], c='r')
    plt.title(title2)
    plt.ylabel(ylabel)
    plt.xlabel(xlabel)
    plt.grid(True)

    plt.tight_layout()
    plt.show()        
    
    
def plot_energy_comparison(plt1_series, plt2_series, plt1_series_labels=['OCHRE', 'REopt'], plt2_series_labels=['OCHRE', 'REopt'],
                           title1='Delivered', title2='Consumption', ylabel='Monthly Energy Use [kWh]', xlabel='Month', n_timesteps=12):

    x_axis = np.linspace(1,n_timesteps,n_timesteps)
    fig, ax = plt.subplots()
    plt.subplot(2,1,1)
    for idx, series in enumerate(plt1_series):
        plt.plot(x_axis, series, label=plt1_series_labels[idx])
    plt.title(title1)
    plt.legend()
    plt.ylabel(ylabel)

    plt.subplot(2,1,2)
    for idx, series in enumerate(plt2_series):
        plt.plot(x_axis, series, label=plt2_series_labels[idx])
        
    plt.title(title2)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.legend()
    plt.tight_layout()
    plt.show()
    
    
def plot_timeseries(x_axis, plt_series, titles=None, plt_series_labels=None, ylabel='Monthly Energy Use [kWh]', 
                    xlabel='Month', x=8, y=8, drawlines=False, xlim=None, savefig_path=None):

    n_subplots = len(plt_series)
    fig, ax = plt.subplots(figsize=(x, y))
#    x_axis = pd.date_range("1/1/2019 00:00", periods=8760, freq="1H") #np.linspace(1, n_timesteps, n_timesteps)
    for i, series in enumerate(plt_series):
        plt.subplot(n_subplots,1,i+1)
        for j, vals in enumerate(series):
            if plt_series_labels is not None:
                plt.plot(x_axis, vals, label=plt_series_labels[i][j])
            else:
                plt.plot(x_axis, vals)
                if i == 2 and drawlines == True:
                    plt.plot(x_axis, [23.3]*len(x_axis), c='b')
                    plt.plot(x_axis, [25]*len(x_axis), c='r')
        if xlim is not None:
            plt.xlim(xlim)
        if titles is not None:
            plt.title(titles[i])
        if plt_series_labels is not None:
            plt.legend()
        plt.ylabel(ylabel)
        plt.grid(True)
        
#    if xticklabels is not None:
#        ax.set_xticklabels(xticklabels)

    plt.xlabel(xlabel)
    plt.tight_layout()
    plt.show()
    
    if savefig_path is not None:
        plt.savefig(savefig_path)