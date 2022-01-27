"""
Collection of functions to subset REopt results to facilitate metrics calculations 
"""
import os 
import json
import numpy as np
from novametrics.analyze_results.simulate_outages import simulate_outages
HOURS = 8760
#%%
#Code subsets REopt results for final metrics generation. 
def return_zero_values():
    """Return dictionary of default results in case where REopt does not include system"""
    d = {"kw_capacity":0, "kwh_capacity": 0, "annual_exports": 0, "hourly_exports": [0]*HOURS, "annual_generation": 0, "hourly_generation": [0]*HOURS, "annual_load": 0, "hourly_load": [0]*HOURS, "upfront_capital_cost": 0} 
    return d
#%%
def pv_values(reopt_results):
    """
    Return dictionary of select PV outputs
    
    `hourly_exports` and `hourly_generation` are timeseries values
    All other outputs are single values
    """
    inputs = reopt_results["inputs"]["Scenario"]["Site"]["PV"]
    outputs = reopt_results["outputs"]["Scenario"]["Site"]["PV"]
    
    if outputs["size_kw"] != None and outputs["size_kw"] > 0.01:
        d = {}
        d["kw_capacity"] = outputs["size_kw"]
        d["kwh_capacity"] = 0
        d["annual_exports"] = sum(outputs["year_one_to_grid_series_kw"])
        d["hourly_exports"] = outputs["year_one_to_grid_series_kw"]
        d["annual_generation"] = sum(outputs["year_one_power_production_series_kw"])
        d["hourly_generation"] = outputs["year_one_power_production_series_kw"]
        d["upfront_capital_cost"] = outputs["size_kw"] * inputs["installed_cost_us_dollars_per_kw"]
        d["pv_average_capacity_factor"] = sum(inputs["prod_factor_series_kw"])/len(inputs["prod_factor_series_kw"])
    else:
        d = return_zero_values()
        d["pv_average_capacity_factor"] = 0
    return d
#%%
def storage_values(reopt_results):
    """
    Return dictionary of select PV outputs
    
    `hourly_exports`, `hourly_generation`, `hourly-load`, and `state_of_charge` are timeseries values
    All other outputs are single values
    """
    inputs = reopt_results["inputs"]["Scenario"]["Site"]
    outputs = reopt_results["outputs"]["Scenario"]["Site"]
    
    if outputs["Storage"]["size_kw"] != None and outputs["Storage"]["size_kw"] > 0.01:
        d = {}
        d["kw_capacity"] = outputs["Storage"]["size_kw"]
        d["kwh_capacity"] = outputs["Storage"]["size_kwh"]
        d["annual_exports"] = sum(outputs["Storage"]["year_one_to_grid_series_kw"])
        d["hourly_exports"] = outputs["Storage"]["year_one_to_grid_series_kw"]
        
        dispatch = [outputs["Storage"]["year_one_to_load_series_kw"][i] + outputs["Storage"]["year_one_to_grid_series_kw"][i] for i in range(HOURS)]
        d["annual_generation"] = sum(dispatch)
        d["hourly_generation"] = dispatch
        d["state_of_charge"] = outputs["Storage"]["year_one_soc_series_pct"]
        
        load = [outputs["ElectricTariff"]["year_one_to_battery_series_kw"][i] + outputs["PV"]["year_one_to_battery_series_kw"][i] for i in range(HOURS)]
        d["annual_load"] = sum(load)
        d["hourly_load"] = load
        
        d["upfront_capital_cost"] = outputs["Storage"]["size_kw"] * inputs["Storage"]["installed_cost_us_dollars_per_kw"] + outputs["Storage"]["size_kwh"] * inputs["Storage"]["installed_cost_us_dollars_per_kwh"]
    else:
        d = return_zero_values()
        d["state_of_charge"] = [0]*HOURS
    return d
#%%
def financial_values(reopt_results):
    """Return dictionary of financial values including LCC, net capital costs, and initial capital costs"""
    outputs = reopt_results["outputs"]["Scenario"]["Site"]["Financial"]
    
    d = {
        "LCC": outputs["lcc_us_dollars"],
        "net_capital_costs": outputs["net_capital_costs"],
        "initial_capital_costs": outputs["initial_capital_costs"],
        "total_om_cost": outputs["total_om_costs_us_dollars"] #,
        # "total_production_incentive_benefit": outputs["total_production_incentive_after_tax"]        
        }
    return d
#%%
def load_values(reopt_results):
    """Return dictionary of load values including `home_load`, `net_load`, and `grid_purchases`."""
    outputs = reopt_results["outputs"]["Scenario"]["Site"]
    d = {"grid_purchases_kw" : [outputs["ElectricTariff"]["year_one_to_battery_series_kw"][ts] + outputs["ElectricTariff"]["year_one_to_load_series_kw"][ts] for ts in range(HOURS)]}
    
    pv_to_grid = outputs["PV"]["year_one_to_grid_series_kw"]
    pv_to_load = outputs["PV"]["year_one_to_load_series_kw"]
    if len(pv_to_load) == 0:
        pv_to_grid = [0]*HOURS
        pv_to_load = [0]*HOURS
    
    d["net_load"] = [d["grid_purchases_kw"][h] - pv_to_grid[h] - outputs["Storage"]["year_one_to_grid_series_kw"][h] for h in range(HOURS)]
    d["home_load"] = [outputs["ElectricTariff"]["year_one_to_load_series_kw"][h] + pv_to_load[h] + outputs["Storage"]["year_one_to_load_series_kw"][h] for h in range(HOURS)]
    d["annual_grid_purchases"] = sum(d["grid_purchases_kw"])
    return d
#%%

def ra_values(reopt_results):
    outputs = reopt_results["outputs"]["Scenario"]["Site"]["ElectricTariff"]
    d = {}
    if "monthly_ra_value" in outputs and len(outputs["monthly_ra_value"]) > 0:
        if len(outputs["monthly_ra_reduction"]) > 0:
            d["avg_monthly_ra_reduction"] = np.mean(outputs["monthly_ra_reduction"]) 
        else:
            d["avg_monthly_ra_reduction"] = np.mean(outputs["hourly_reductions"]) 

        d["total_ra_value"] = sum(outputs["monthly_ra_value"]) 
        d["avg_hourly_ra_reduction"] = np.mean(outputs["hourly_reductions"])

    else:
        d["avg_hourly_ra_reduction"] = 0
        d["total_ra_value"] = 0
    return d
# query_reopt_outputs(["year_one_energy_cost_us_dollars", "year_one_energy_supplied_kwh", "year_one_bill_us_dollars", "year_one_export_benefit_us_dollars", "year_one_coincident_peak_cost_us_dollars"], reopt_results, save_dict, "ElectricTariff")

#%%
def resilience_values(reopt_results, critical_loads):
    d = {}
    outputs = reopt_results["outputs"]["Scenario"]["Site"]
    battery = outputs["Storage"]
    pv = outputs["PV"]
     #Calculate Resilience Metrics
    resilience_no_notice = simulate_outages(batt_kwh= battery["size_kw"], 
                                          batt_kw= battery["size_kwh"], 
                                          pv_kw_ac_hourly= pv["year_one_power_production_series_kw"], 
                                          init_soc= battery["year_one_soc_series_pct"], 
                                          critical_loads_kw= critical_loads, 
                                          batt_roundtrip_efficiency=0.829)
    
    d["avg_resilience_no_notice"] = resilience_no_notice["resilience_hours_avg"]
    d["hourly_survival_no_notice"]   = resilience_no_notice["resilience_by_timestep"]
    return d

#%%
def utility_bill(reopt_results):
    outputs = reopt_results["outputs"]["Scenario"]["Site"]["ElectricTariff"]
    
    d = {"annual_bill": outputs["year_one_bill_us_dollars"], 
         "total_utility_energy_cost": outputs["year_one_energy_cost_us_dollars"], 
         # "total_fuel_cost": reopt_results["outputs"]["Scenario"]["Site"]["FuelTariff"]["total_fuel_cost_us_dollars"],
         
         "total_utility_demand_cost": outputs["year_one_demand_cost_us_dollars"],
         "total_energy": outputs["total_energy_cost_us_dollars"],
         "energy_costs_per_kwh" : outputs["year_one_energy_cost_series_us_dollars_per_kwh"],
         "demand_charge_per_kw": outputs["year_one_demand_cost_series_us_dollars_per_kw"],
         "total_utility_fixed_cost": outputs["total_fixed_cost_us_dollars"],
         "total_utility_min_cost_adder_cost": outputs["total_min_charge_adder_us_dollars"],
         "total_utility_coincident_peak_cost": outputs["total_coincident_peak_cost_us_dollars"],
         "total_utility_coincident_peak_cost_bau": outputs["total_coincident_peak_cost_bau_us_dollars"],
         "total_export_benefit": outputs["total_export_benefit_us_dollars"]
         # ,
         # "total_resource_adequacy_benefit": outputs["total_resource_adequacy_benefit"]
         }
    return d
    
#%%
#FlexTechAC, FlexTechHP, FlexTechERWH, FlexTechHPWH
def flex_tech_values(reopt_results, tech_name):
    d = {}
    if tech_name not in reopt_results["inputs"]["Scenario"]["Site"]:
        return return_zero_values()
    else: 
        inputs = reopt_results["inputs"]["Scenario"]["Site"][tech_name]
        outputs = reopt_results["outputs"]["Scenario"]["Site"][tech_name]
        
        if "size_kw" in outputs and outputs["size_kw"] != None and outputs["size_kw"] > 0.01:
            d["kw_capacity"] = outputs["size_kw"]
            d["kwh_capacity"] = 0
            d["annual_exports"] = 0
            d["hourly_exports"] = [0]*HOURS
            d["hourly_generation"] = outputs["year_one_power_production_series_kw"]
            d["annual_generation"] = sum(outputs["year_one_power_production_series_kw"])
            d["upfront_capital_cost"] = outputs["size_kw"] * inputs["installed_cost_us_dollars_per_kw"]
            d["hourly_load"]: outputs["year_one_power_consumption_series_kw"]
            d["annual_load"]: sum(outputs["year_one_power_consumption_series_kw"])
        elif outputs["year_one_power_consumption_series_kw"] != None and len(outputs["year_one_power_consumption_series_kw"]) > 0:
            d["kw_capacity"] = inputs["size_kw"]
            d["kwh_capacity"] = 0
            d["annual_exports"] = 0
            d["hourly_exports"] = [0]*HOURS
            d["hourly_generation"] = outputs["year_one_power_production_series_kw"]
            d["annual_generation"] = sum(outputs["year_one_power_production_series_kw"])
            d["upfront_capital_cost"] = outputs["size_kw"] * inputs["installed_cost_us_dollars_per_kw"]
            d["hourly_load"]: outputs["year_one_power_consumption_series_kw"]
            d["annual_load"]: sum(outputs["year_one_power_consumption_series_kw"])
            
        else:
            d = return_zero_values()
        return d
#%%
def temperature_values(reopt_results):
    if "RC" in reopt_results["outputs"]["Scenario"]["Site"]:
        outputs = reopt_results["outputs"]["Scenario"]["Site"]["RC"]
        return {'temperatures_degree_C': outputs['temperatures_degree_C'], 
                'comfort_penalty': outputs['comfort_penalty_degC'], 
                "outdoor_air_temp_degF": reopt_results["outputs"]["Scenario"]["Site"]["outdoor_air_temp_degF"]}
    else:
        return {'temperatures_degree_C': [None]*HOURS, 'comfort_penalty': [0]*HOURS, "outdoor_air_temp_degF": [None]*HOURS}
#%%
def emissions_values(reopt_results):
    outputs = reopt_results["outputs"]["Scenario"]["Site"]
    d = {
        "annual_emissions_tons_CO2": outputs["year_one_emissions_tCO2"],
        "total_emissions_tons_CO2" : outputs["lifecycle_emissions_tCO2"]
        "hourly_emissions_factors_lb_CO2_per_kwh": reopt_results["inputs"]["Scenario"]["Site"]["ElectricTariff"]["emissions_factor_series_lb_CO2_per_kwh"]
        }
    if reopt_results["inputs"]["Scenario"]["Site"].get("include_climate_in_objective"):
        d["total_climate_cost"] = outputs["lifecycle_emissions_cost_CO2"]
    else:
        d["total_climate_cost"] = 0
    if reopt_results["inputs"]["Scenario"]["Site"].get("include_health_in_objective"):
        d["total_health_cost"] = outputs["lifecycle_emissions_cost_Health"]
    else:
        d["total_health_cost"] = 0
        
    return d 

#%%
def comfort_values(reopt_results):
    d = {
    "total_wh_comfort_cost": 0,
    "total_hvac_comfort_cost": 0
        }
    if "RC" in reopt_results["outputs"]["Scenario"]["Site"]:
        outputs = reopt_results["outputs"]["Scenario"]["Site"]["RC"]
        if "wh_comfort_cost_total" in outputs:
            d["total_wh_comfort_cost"] = outputs["wh_comfort_cost_total"]
        if "hvac_comfort_cost_total" in outputs:
            d["total_hvac_comfort_cost"] = outputs["hvac_comfort_cost_total"]
    return d
#%%
def metadata_values(reopt_results, filename):
    d = {}
    outputs = reopt_results["outputs"]["Scenario"]
    d["status"] = outputs["status"]
    d["run_uuid"] = outputs["run_uuid"]
    d["filename"] = filename
    d["latitude"] = reopt_results["inputs"]["Scenario"]["Site"]["latitude"]
    d["longitude"] = reopt_results["inputs"]["Scenario"]["Site"]["longitude"]

    if outputs["status"] != "optimal":
        d["run_failed"] = True
    else:
        d["run_failed"] = False
    return d



def extract_results(filepath, filename):
    with open(os.path.join(filepath, filename), 'r') as fp:
        reopt_results = json.load(fp)
    
    d = {}
    d["metadata"] = metadata_values(reopt_results, filename)
    if d["metadata"]["run_failed"]:
        print(f"Run {d['metadata']['filename']} Failed")

    d["PV"] = pv_values(reopt_results)
    d["Storage"] = storage_values(reopt_results)
    for tech_name in ["FlexTechAC", "FlexTechHP", "FlexTechERWH", "FlexTechHPWH"]:
        d[tech_name] = flex_tech_values(reopt_results, tech_name)
        
    d["temperature"] = temperature_values(reopt_results)
    d["financial"] = financial_values(reopt_results)
    d["load"] = load_values(reopt_results)
    
    d["ra"] = ra_values(reopt_results)
    d["utility_bill"] = utility_bill(reopt_results)
    d["emissions"] = emissions_values(reopt_results)
    
    d["resilience"] = resilience_values(reopt_results, d["load"]["home_load"])
    d["comfort"] = comfort_values(reopt_results)
    return d 