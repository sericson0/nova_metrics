import os
import numpy as np
import pandas as pd
import yaml
import xmltodict
from novametrics.support.utils import load_post, not_none, get_dictionary_value, get_filename
#%%

def get_properties_file(file_path):
    """
    Parse .properties OCHRE inputs file and return relevant parameters for REopt integration.
    
    Assumes initial file structure, e.g. "city          = CA_RIVERSIDE-MUNI

    Parameters
    ----------
    file_path : str
        Path to .properties file.

    Returns
    -------
    out : dic
        Dictionary of OCHRE property values for HVAC and water heater dispatch.
    """
    properties = {}
    out = {}
    #TODO update to keep potential variations such as no HVAC cooling
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
                    properties[key] = eval(val)
                except (NameError, SyntaxError):
                    properties[key] = val
            elif len(line_split) > 2:
                # convert to dict (all should be floats)
                line_list = '='.join(line_split[1:]).split('   ')
                line_list = [tuple(s.split('=')) for s in line_list]
                properties[key] = {k.strip(): float(v.strip()) for (k, v) in line_list}



    if "heating fuel" in properties:
        out['heating fuel'] = properties["heating_fuel"]
        if out["heating fuel"] == "Electric":
            out["heating fuel"] = "Electricity"

        out['heating number of speeds'] = properties["heating number of speeds"]
        out['heating fan power (W/cfm)'] = properties["heating fan power (W/cfm)"]
        out['heating airflow rate (cfm)'] = properties["heating airflow rate (cfm)"]
        out['heating capacity (W)'] = properties["heating capacity (W)"]
        out['heating EIR'] = properties["heating EIR"]
        if "heating duct dse" in properties:
            out['heating duct dse'] = properties["heating duct dse"]
        else:
            out["heating duct dse"] = 1
            
    else:
        print(f"Building {file_path} has no HVAC Heating.")
        out['heating fuel'] = "None"
        out['heating number of speeds'] = 1
        out['heating fan power (W/cfm)'] = 0
        out['heating airflow rate (cfm)'] = 0
        out['heating capacity (W)'] = 0
        out['heating EIR'] = 1
        out['heating duct dse'] = 1


    if "cooling fuel" in properties:
        out['cooling fuel'] = properties["cooling fuel"]
        if out["cooling fuel"] == "Electric":
            out["cooling fuel"] = "Electricity"
        out['cooling number of speeds'] = properties["cooling number of speeds"]
        out['cooling fan power (W/cfm)'] = properties["cooling fan power (W/cfm)"]
        out['cooling airflow rate (cfm)'] = properties["cooling airflow rate (cfm)"]
        out['cooling capacity (W)'] = properties["cooling capacity (W)"]
        out['cooling EIR'] = properties["cooling EIR"]
        if "cooling duct dse" in properties:
            out['cooling duct dse'] = properties["cooling duct dse"]
        else:
            out['cooling duct dse'] = 1
    else:
        out['cooling fuel'] = "None"
        out['cooling number of speeds'] = 1
        out['cooling fan power (W/cfm)'] = 0
        out['cooling airflow rate (cfm)'] = 0
        out['cooling capacity (W)'] = 0
        out['cooling EIR'] = 1
        out['cooling duct dse'] = 1
        
        
    if "water heater fuel" in properties:    
        out['water heater fuel'] = properties["water heater fuel"]
        if out["water heater fuel"] == "Electric":
            out["water heater fuel"] = "Electricity"
        out['rated input power (W)'] = properties["rated input power (W)"]
        out['water heater type'] = properties["water heater type"]
    else:
        print("No Water Heating")
        out['water heater fuel'] = "None"
        out['rated input power (W)'] = 0
        out['water heater type'] = "None"
        
    return out


def get_yaml_file(file_path):
    """
    Parse .yaml OCHRE property file and return relevant values for REopt integration

    Parameters
    ----------
    file_path : str
        Path to .properties file.

    Returns
    -------
    out : dict
        Dictionary of OCHRE property values for HVAC and water heater dispatch.
    """
    with open(file_path) as f:
        properties = yaml.safe_load(f)["Equipment"]

    out = {}
    if "HVAC Heating" in properties:
        out['heating fuel'] = properties["HVAC Heating"]["Fuel"]
        if out["heating fuel"] == "Electric":
            out["heating fuel"] = "Electricity"
        out['heating number of speeds'] = properties["HVAC Heating"]["Number of Speeds (-)"]
        out['heating fan power (W/cfm)'] = properties["HVAC Heating"]["Fan Power (W/cfm)"]
        out['heating airflow rate (cfm)'] = properties["HVAC Heating"]["Airflow Rate (cfm)"]
        out['heating capacity (W)'] = properties["HVAC Heating"]["Capacity (W)"]
        out['heating EIR'] = properties["HVAC Heating"]["EIR (-)"]
        if "Duct DSE (-)" in properties["HVAC Heating"]:
            out['heating duct dse'] = properties["HVAC Heating"]["Duct DSE (-)"]
        else:
            out["heating duct dse"] = 1
            
    else:
        print(f"Building {file_path} has no HVAC Heating.")
        out['heating fuel'] = "None"
        out['heating number of speeds'] = 1
        out['heating fan power (W/cfm)'] = 0
        out['heating airflow rate (cfm)'] = 0
        out['heating capacity (W)'] = 0
        out['heating EIR'] = 1
        out['heating duct dse'] = 1
        
    if "HVAC Cooling" in properties:
        out['cooling fuel'] = properties["HVAC Cooling"]["Fuel"]
        if out["cooling fuel"] == "Electric":
            out["cooling fuel"] = "Electricity"
        out['cooling number of speeds'] = properties["HVAC Cooling"]["Number of Speeds (-)"]
        out['cooling fan power (W/cfm)'] = properties["HVAC Cooling"]["Fan Power (W/cfm)"]
        out['cooling airflow rate (cfm)'] = properties["HVAC Cooling"]["Airflow Rate (cfm)"]
        out['cooling capacity (W)'] = properties["HVAC Cooling"]["Capacity (W)"]
        out['cooling EIR'] = properties["HVAC Cooling"]["EIR (-)"]
        if "Duct DSE (-)" in properties["HVAC Cooling"]:
            out['cooling duct dse'] = properties["HVAC Cooling"]["Duct DSE (-)"]
        else:
            out['cooling duct dse'] = 1
    else:
        out['cooling fuel'] = "None"
        out['cooling number of speeds'] = 1
        out['cooling fan power (W/cfm)'] = 0
        out['cooling airflow rate (cfm)'] = 0
        out['cooling capacity (W)'] = 0
        out['cooling EIR'] = 1
        out['cooling duct dse'] = 1
        
        
    if "Water Heating" in properties:    
        out['water heater fuel'] = properties["Water Heating"]["Fuel"]
        if out["water heater fuel"] == "Electric":
            out["water heater fuel"] = "Electricity"
        out['rated input power (W)'] = properties["Water Heating"]["Capacity (W)"]
        out['water heater type'] = properties["HVAC Heating"]["Equipment Name"]
    else:
        print("No Water Heating")
        out['water heater fuel'] = "None"
        out['rated input power (W)'] = 0
        out['water heater type'] = "None"
        
    return out



# def get_building_metadata(xml_filepath, yaml_filepath):
#     string = ""
#     with open(xml_filepath) as f:
#        xml_data = xmltodict.parse(f.read())
#     string += "state|" + xml_data["HPXML"]["Building"]["Site"]["Address"]["StateCode"] + ", "
#     string += "zipcode|" + xml_data["HPXML"]["Building"]["Site"]["Address"]["ZipCode"] + ", "
#     string += "site_type|" + xml_data["HPXML"]["Building"]["BuildingDetails"]["BuildingSummary"]["Site"]["SiteType"]["#text"] + ", "
#     string += "year_built|" + xml_data["HPXML"]["Building"]["BuildingDetails"]["BuildingSummary"]["BuildingConstruction"]["YearBuilt"] + ", "
#     string += "building_type|" + xml_data["HPXML"]["Building"]["BuildingDetails"]["BuildingSummary"]["BuildingConstruction"]["ResidentialFacilityType"] + ", "
#     string += "number_of_bedrooms|" + xml_data["HPXML"]["Building"]["BuildingDetails"]["BuildingSummary"]["BuildingConstruction"]["NumberofBedrooms"] + ", "
#     # string += "number_of_bathrooms|" + xml_data["HPXML"]["Building"]["BuildingDetails"]["BuildingSummary"]["BuildingConstruction"]["NumberofBathrooms"] + ", "
#     string += "floor_area|" + xml_data["HPXML"]["Building"]["BuildingDetails"]["BuildingSummary"]["BuildingConstruction"]["ConditionedFloorArea"] + ", "
#     string += "climate_zone|" + xml_data["HPXML"]["Building"]["BuildingDetails"]["ClimateandRiskZones"]["ClimateZoneIECC"]["ClimateZone"] + ","

#     with open(yaml_filepath) as f:
#         yaml_data = yaml.safe_load(f)
#     string += "occupants|" + str(yaml_data["Occupancy"]["Number of Occupants (-)"]) + ","
#     string += "wall_r_val|" + str(yaml_data["Boundaries"]["Exterior Wall"]["Boundary R Value"]) + ", "
#     string += "heating_type|" + yaml_data["Equipment"]["HVAC Heating"]["Equipment Name"] + ", "
#     string += "heating_fuel|" + yaml_data["Equipment"]["HVAC Heating"]["Fuel"] + ", "
#     string += "water_heater_type|" + yaml_data["Equipment"]["Water Heating"]["Equipment Name"] + ", "
#     string += "water_heater_fuel|" + yaml_data["Equipment"]["Water Heating"]["Fuel"] + ", "
#     if "HVAC Cooling" in yaml_data["Equipment"]:
#         string += "cooling_type|" + yaml_data["Equipment"]["HVAC Cooling"]["Equipment Name"] 
#     else:
#         string += "cooling_type|" + "None"
#     return string


# xml_filepath = "D:/test_resstock/ResStock/bldg0000002/in.xml"
# yaml_filepath = "D:/test_resstock/ResStock/bldg0000002/in.yaml"
 






def parse_properties(file_path):
    """
    Calculate property values needed for OCHRE-REopt dispatchable load integration

    Parameters
    ----------
    file_path : str
        Path to either a .properties or a .yaml OCHRE properties file.

    Returns
    -------
    out : dict
        Dictionary of parsed HVAC and water heater values.

    """
    if file_path.endswith(".properties"):
        prop_values = get_properties_file(file_path)
    elif file_path.endswith(".yaml"):
        prop_values = get_yaml_file(file_path)
    else:
        #TODO work on better error message
        print("The properties file must be a .properties or .yaml extension")
        return {"erwh_size_kw": 0.0, "hpwh_size_kw" : 0.0, "hp_size_heat": 0.0,
                "hp_fan_power_ratio": 0, "ac_size_kw" : 0, "ac_size_heat" : 0,
                "ac_fan_power_ratio" : 0, "heating fuel": "", "cooling fuel": ""}
    out = {}
    
    #Heating
    out["heating fuel"] = prop_values["heating fuel"]
    out["hp_dse"] = prop_values['heating duct dse']
    heating_speed = prop_values["heating number of speeds"] -1 
    out["hp_size_heat"] = prop_values['heating capacity (W)'][heating_speed] / 1000
    if prop_values['heating fuel'] == "Electricity":
        out["hp_size_kw"] = (prop_values['heating capacity (W)'][heating_speed] * 
                      prop_values['heating EIR'][heating_speed]) / 1000
        
        out["hp_fan_power_ratio"] = (prop_values['heating fan power (W/cfm)'] * prop_values['heating airflow rate (cfm)'][heating_speed]) / \
                             (prop_values['heating capacity (W)'][heating_speed] * prop_values['heating EIR'][heating_speed])
    else:
        out["hp_size_kw"] = (prop_values['heating capacity (W)'][heating_speed] / 
                      prop_values['heating EIR'][heating_speed]) / 1000
        out["hp_fan_power_ratio"] = 0
    
    
    #Cooling    
    out["cooling fuel"] = prop_values["cooling fuel"]
    cooling_speed = prop_values["cooling number of speeds"] -1 
    out["ac_dse"] = prop_values['cooling duct dse']
    
    
    if prop_values['cooling fuel'] == "Electricity":
        out["ac_size_kw"] = (prop_values['cooling capacity (W)'][cooling_speed] *
                      prop_values['cooling EIR'][cooling_speed]) / 1000
        out["ac_size_heat"] = prop_values['cooling capacity (W)'][cooling_speed] / 1000
        
        out["ac_fan_power_ratio"] = (prop_values['cooling fan power (W/cfm)'] * prop_values['cooling airflow rate (cfm)'][cooling_speed]) / \
                             (prop_values['cooling capacity (W)'][cooling_speed] * prop_values['cooling EIR'][cooling_speed])
    else:
        # print('ERROR: non-electric cooling!')
        out["ac_size_kw"] = 0
        out["ac_size_heat"] = 0
        out["ac_fan_power_ratio"] = 0
    
    # Water Heater
    out["erwh_size_kw"] = 0.0
    out["hpwh_size_kw"] = 0.0

    out["water heater fuel"] = prop_values['water heater fuel']

    if prop_values['water heater fuel'] == "Electricity":
        #TODO See why zero is needed in code below
        if type(prop_values['rated input power (W)']) == list:
            out["erwh_size_kw"] = prop_values['rated input power (W)'][0]/1000 
        else:
            out["erwh_size_kw"] = prop_values['rated input power (W)']/1000 
        
    if prop_values['water heater type'] == 'Heatpump':
        out["hpwh_size_kw"] = 0.4
        

    return out

def load_ochre_outputs(ochre_controls):
    """
    Return list of OCHRE building model output results.
         
    Parameters
    ----------
    ochre_controls : dict
     Dictionary containing specifications for strings to match filenames.
     OCHRE output folder filenames default to:
         ochre_outputs_main_folder - OCHRE
         ochre_outputs_subfolder - No default
         properties_file - .properties
         envelope_matrixA - _Envelope_matrixA.csv
         envelope_matrixB - _Envelope_matrixB.csv
         hourly_inputs - OCHRE_Run.csv
         water_tank_matrixA - _Water Tank_matrixA.csv
         water_tank_matrixB - _Water Tank_matrixB.csv
    
    Returns
    -------
    list
    [parsed_prop, a_matrix, b_matrix, hourly_inputs, a_matrix_wh, b_matrix_wh]
    """
    input_main_folder = get_dictionary_value(ochre_controls, "ochre_inputs_main_folder", "ResStock")
    xml_properties_ext = get_dictionary_value(ochre_controls, "properties_file", "in.xml")
    
    
    ochre_input_file_path = os.path.join(input_main_folder, ochre_controls["ochre_outputs_subfolder"])    
    ochre_output_file_path = os.path.join(ochre_controls["ochre_outputs_main_folder"], ochre_controls["ochre_outputs_subfolder"])    
    properties_file_key = get_dictionary_value(ochre_controls, "properties_file", "in.yaml").rsplit(".", 1)[0] + ".yaml"
    envelope_matrixA_key = get_dictionary_value(ochre_controls, "envelope_matrixA", "_Envelope_matrixA.csv")
    envelope_matrixB_key = get_dictionary_value(ochre_controls, "envelope_matrixB", "_Envelope_matrixB.csv")
    hourly_inputs_key = get_dictionary_value(ochre_controls, "hourly_inputs", "OCHRE_Run.csv")
    water_tank_matrixA_key = get_dictionary_value(ochre_controls, "water_tank_matrixA", "_Water Tank_matrixA.csv")
    water_tank_matrixB_key = get_dictionary_value(ochre_controls, "water_tank_matrixB", "_Water Tank_matrixB.csv")

    xml_file = get_filename(ochre_input_file_path, xml_properties_ext)
    properties_file = get_filename(ochre_input_file_path, properties_file_key)           
    b_matrix_file = get_filename(ochre_output_file_path, envelope_matrixB_key)
    a_matrix_file = get_filename(ochre_output_file_path, envelope_matrixA_key)
    hourly_inputs_file = get_filename(ochre_output_file_path, hourly_inputs_key)
    a_matrix_wh_file = get_filename(ochre_output_file_path, water_tank_matrixA_key)
    b_matrix_wh_file = get_filename(ochre_output_file_path, water_tank_matrixB_key)
    
    parsed_prop = parse_properties(os.path.join(ochre_input_file_path, properties_file))
    a_matrix = pd.read_csv(os.path.join(ochre_output_file_path, a_matrix_file), index_col=0)
    b_matrix = pd.read_csv(os.path.join(ochre_output_file_path, b_matrix_file), index_col=0)
    hourly_inputs = pd.read_csv(os.path.join(ochre_output_file_path, hourly_inputs_file))
    a_matrix_wh = pd.read_csv(os.path.join(ochre_output_file_path, a_matrix_wh_file), index_col=0)
    b_matrix_wh = pd.read_csv(os.path.join(ochre_output_file_path, b_matrix_wh_file), index_col=0)

    # building_metadata = get_building_metadata(os.path.join(ochre_input_file_path, xml_file), os.path.join(ochre_input_file_path, properties_file))
    return [parsed_prop, a_matrix, b_matrix, hourly_inputs, a_matrix_wh, b_matrix_wh]
    


    


def wh_post(post, ochre_outputs, ochre_controls):
    parsed_prop, a_matrix, b_matrix, hourly_inputs, a_matrix_wh, b_matrix_wh = ochre_outputs
    erwh_size_kw = parsed_prop["erwh_size_kw"]
    hpwh_size_kw = parsed_prop["hpwh_size_kw"]
    
    
    if (parsed_prop["water heater fuel"] == "None") or ((erwh_size_kw + hpwh_size_kw) <= 0.01):
        if 'FlexTechERWH' not in post['Scenario']['Site']:
            post['Scenario']['Site']['FlexTechERWH'] = {}
        post['Scenario']['Site']['FlexTechERWH']['size_kw'] = erwh_size_kw
            
        if 'FlexTechHPWH' not in post['Scenario']['Site']:
            post['Scenario']['Site']['FlexTechHPWH'] = {'size_kw': 0.0, "prod_factor_series_kw": [], "cop": []}
    
    else:
        wh_temperature_lower_bound = get_dictionary_value(ochre_controls, "wh_temperature_lower_bound", 30)
        wh_temperature_upper_bound = get_dictionary_value(ochre_controls, "wh_temperature_upper_bound", 60)
        wh_comfort_temp_limit = get_dictionary_value(ochre_controls, "wh_comfort_temp_limit", 43)
        wh_load = list(hourly_inputs.loc[:, 'Water Heating Electric Power (kW)'])
        post['Scenario']['Site']['LoadProfile']['loads_kw'] = [post['Scenario']['Site']['LoadProfile']['loads_kw'][i] - wh_load[i] for i in range(len(wh_load))]

        init_temperatures_wh = hourly_inputs.loc[:, a_matrix_wh.keys()]
        init_temperatures_wh = list(init_temperatures_wh.iloc[0])
        
        if hpwh_size_kw > 0.01:
            hpwh_cop = list(hourly_inputs.loc[:, 'Water Heating Heat Pump COP (-)'])
            hpwh_prodfactor = list(hourly_inputs.loc[:, 'Water Heating Heat Pump Max Capacity (kW)'] / hpwh_size_kw)
        else:
            hpwh_cop = []
            hpwh_prodfactor = []
            
        n_temp_nodes_wh = a_matrix_wh.shape[1]
        n_input_nodes_wh = b_matrix_wh.shape[1]
        
        wh_injection_node_num = b_matrix_wh.columns.get_loc('H_WH1') + 1
        water_node_num = a_matrix_wh.columns.get_loc('T_WH1') + 1
    
        u_inputs_wh = hourly_inputs.loc[:, b_matrix_wh.keys()]
        u_inputs_wh.loc[:, 'H_WH1'] = u_inputs_wh.loc[:, 'H_WH1'] - hourly_inputs.loc[:, 'Water Heating Delivered (kW)'] * 1000
                                                    
        a_matrix_wh = list(a_matrix_wh.T.stack().reset_index(name='new')['new'])
        b_matrix_wh = list(b_matrix_wh.T.stack().reset_index(name='new')['new'])
        u_inputs_wh = list(u_inputs_wh.T.stack().reset_index(name='new')['new'])
        
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
        post['Scenario']['Site']['FlexTechERWH']['size_kw'] = erwh_size_kw
            
        if 'FlexTechHPWH' not in post['Scenario']['Site']:
            post['Scenario']['Site']['FlexTechHPWH'] = {}
        post['Scenario']['Site']['FlexTechHPWH']['size_kw'] = hpwh_size_kw
        post['Scenario']['Site']['FlexTechHPWH']['prod_factor_series_kw'] = hpwh_prodfactor
        post['Scenario']['Site']['FlexTechHPWH']['cop'] = hpwh_cop
        

    


def hvac_post(post, ochre_outputs, ochre_controls):
    n_timesteps = 8760

    parsed_prop, a_matrix, b_matrix, hourly_inputs, a_matrix_wh, b_matrix_wh = ochre_outputs
    
    hvac_temperature_lower_bound = get_dictionary_value(ochre_controls, "hvac_temperature_lower_bound", 0)
    hvac_temperature_upper_bound = get_dictionary_value(ochre_controls, "hvac_temperature_upper_bound", 40)
    hvac_comfort_temp_lower_bound = get_dictionary_value(ochre_controls, "hvac_comfort_temp_lower_bound", 19.56)
    hvac_comfort_temp_upper_bound = get_dictionary_value(ochre_controls, "hvac_comfort_temp_upper_bound", 25.6)
    
    
    
    init_temperatures_hvac = hourly_inputs.loc[:, a_matrix.keys()]
    init_temperatures_hvac = list(init_temperatures_hvac.iloc[0])
    
    

    
    if parsed_prop['heating fuel'] == "Electricity":
        hp_cop = list(hourly_inputs.loc[:, 'HVAC Heating COP (-)'])
        try:
            er_on = hourly_inputs.loc[:, 'HVAC Heating ER Power (kW)']
        except:
            er_on = pd.Series([-1]*n_timesteps)
    else:
        constant_heating_cop = get_fan_adjustment(hourly_inputs.loc[:, 'HVAC Heating Delivered (kW)'], hourly_inputs.loc[:, 'HVAC Heating Fan Power (kW)'])
        hp_cop = [constant_heating_cop/parsed_prop["ac_dse"]]*n_timesteps
        er_on = pd.Series([-1]*n_timesteps) 
        
    if parsed_prop['cooling fuel'] == "Electricity":
        ac_shr = list(hourly_inputs.loc[:, 'HVAC Cooling SHR (-)'])
        if "FlexTechAC" not in post['Scenario']['Site']:
            post['Scenario']['Site']["FlexTechAC"] = {}
        ac_cop = list(hourly_inputs.loc[:, 'HVAC Cooling COP (-)'])
        ac_prodfactor = hourly_inputs.loc[:, 'HVAC Cooling Max Capacity (kW)'] / parsed_prop["ac_size_heat"]
        ac_prodfactor = list(ac_prodfactor)
        post['Scenario']['Site']['FlexTechAC']['min_kw'] = parsed_prop["ac_size_kw"]
        post['Scenario']['Site']['FlexTechAC']['max_kw'] = parsed_prop["ac_size_kw"]
        post['Scenario']['Site']['FlexTechAC']['shr'] = ac_shr
        post['Scenario']['Site']['FlexTechAC']['prod_factor_series_kw'] = ac_prodfactor
        post['Scenario']['Site']['FlexTechAC']['cop'] = ac_cop
        post['Scenario']['Site']['FlexTechAC']['dse'] = parsed_prop["ac_dse"]
        post['Scenario']['Site']['FlexTechAC']['fan_power_ratio'] = parsed_prop["ac_fan_power_ratio"]
        cooling_hourly_loads = hourly_inputs.loc[:, 'HVAC Cooling Electric Power (kW)']
        cooling_delivered = hourly_inputs.loc[:, 'HVAC Cooling Delivered (kW)'] * 1000
    else:
        cooling_hourly_loads = pd.Series([0]*n_timesteps) 
        cooling_delivered = pd.Series([0]*n_timesteps)
        
    hvac_load = hourly_inputs.loc[:, 'HVAC Heating Electric Power (kW)'] + cooling_hourly_loads
    # HVAC RC characteristics    
    n_temp_nodes_hvac = a_matrix.shape[1]
    n_input_nodes_hvac = b_matrix.shape[1]
    hvac_injection_node_num = b_matrix.columns.get_loc('H_LIV') + 1
    space_node_num = a_matrix.columns.get_loc('T_LIV') + 1
    
    u_inputs = hourly_inputs.loc[:, b_matrix.keys()]
    u_inputs.loc[:, 'H_LIV'] = u_inputs.loc[:, 'H_LIV'] + cooling_delivered - hourly_inputs.loc[:, 'HVAC Heating Delivered (kW)'] * 1000
    # Convert matrices to lists for API input
    a_matrix = list(a_matrix.T.stack().reset_index(name='new')['new'])
    b_matrix = list(b_matrix.T.stack().reset_index(name='new')['new'])
    u_inputs = list(u_inputs.T.stack().reset_index(name='new')['new'])                                                

    #    
    
    hp_prodfactor = hourly_inputs.loc[:, 'HVAC Heating Max Capacity (kW)'] / parsed_prop["hp_size_heat"]

    # Zero out prodfactors where necessary to ensure heating and cooling cannot occur simultaneously
#        space_cond = u_inputs.loc[:, hvac_injection_node_col]
#        ac_prodfactor[space_cond < -500] = 0.01
#        hp_prodfactor[space_cond > 500] = 0.01
    hp_prodfactor[er_on > 0] = 5.0

    hp_prodfactor = list(hp_prodfactor)
    

    if "RC" not in post['Scenario']['Site']:
        post['Scenario']['Site']["RC"] = {}
        

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
    if round(max(ratio, default = 1),4) != round(min(ratio, default = 1),4):
        print('Different fan power ratios:', max(ratio, default = 1), min(ratio, default = 1))
    return max(ratio, default = 1)


# ochre_controls = {"ochre_inputs_main_folder":"ResStock", "ochre_outputs_main_folder": "OCHRE", "properties_file" : "in.xml", 
#                   "hourly_inputs": "OCHRE_Run.csv", "weather_file_path": "C:/Users/sean/BuildStock_TMY3_FIPS", "schedule_inputs": "schedules.csv"}
# file_path_name = 'C:/Users/sean/Desktop/test ResStock/Test2/OCHRE/bldg0000004'
# parsed_prop, a_matrix, b_matrix, hourly_inputs, a_matrix_wh, b_matrix_wh = load_ochre_outputs(file_path_name, ochre_controls)
# post = {"Scenario" : {"Site" : {"LoadProfile": {"loads_kw": [5]*8760}}}}

