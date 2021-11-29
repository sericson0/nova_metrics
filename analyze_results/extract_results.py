# import numpy as np
import os 
import json
from nova_metrics.analyze_results.simulate_outages import *

HOURS = 8760
#%%
#Code subsets REopt results for final metrics generation. 
#Default results if there REopt does not include system
def return_zero_values():
    d = {"kw_capacity":0, "kwh_capacity": 0, "annual_exports": 0, "hourly_exports": [0]*HOURS, "annual_generation": 0, "hourly_generation": [0]*HOURS, "annual_load": 0, "hourly_load": [0]*HOURS, "upfront_capital_cost": 0} 
    return d
#%%
def pv_values(reopt_results):
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
        d["annual_load"]: 0
        d["hourly_load"]: [0]*HOURS
        d["pv_average_capacity_factor"] = sum(inputs["prod_factor_series_kw"])/len(inputs["prod_factor_series_kw"])
    else:
        d = return_zero_values()
        d["pv_average_capacity_factor"] = 0
    return d
#%%
def storage_values(reopt_results):
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
    outputs = reopt_results["outputs"]["Scenario"]["Site"]["Financial"]
    # additional_costs = float(reopt_results["inputs"]["Scenario"]["description"])
    # else:
    #     additional_costs = 0 
    return {"LCC": outputs["lcc_us_dollars"], "net_capital_costs": outputs["net_capital_costs"], "initial_capital_costs": outputs["initial_capital_costs"]}
#%%
def load_values(reopt_results):
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
         "energy": outputs["year_one_energy_cost_us_dollars"], 
         "demand_charges": outputs["year_one_demand_cost_us_dollars"],
         "export_benefits": outputs["year_one_export_benefit_us_dollars"],
         "total_energy": outputs["total_energy_cost_us_dollars"],
         "energy_costs_per_kwh" : outputs["year_one_energy_cost_series_us_dollars_per_kwh"],
         "demand_charge_per_kw": outputs["year_one_demand_cost_series_us_dollars_per_kw"]}
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
    return {"annual_emissions_lb_CO2": reopt_results["outputs"]["Scenario"]["Site"]["year_one_emissions_lb_C02"],
            "hourly_emissions_factors_lb_CO2_per_kwh": reopt_results["inputs"]["Scenario"]["Site"]["ElectricTariff"]["emissions_factor_series_lb_CO2_per_kwh"]}

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
        return d
    else:
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
        return d 

# with open(os.path.join("../../Nova_Analysis/REopt_results/California Case Study/ra", "CA_5cbf599a5457a3d119671081_basecase_CA_All_Electric.json"), 'r') as fp:
#     reopt_results = json.load(fp)   

# os.chdir(os.path.dirname(__file__))
# # # for key in d: print(key)
# for i in d["outputs"]["Scenario"]["Site"]["ElectricTariff"]: print(i)
# # for i in d["outputs"]["Scenario"]["Site"]["Storage"]: print(i)
# # for i in d["outputs"]["Scenario"]["Site"]["FlexTechHPWH"]: print(i)
# df = extract_results("../../Nova_Analysis/REopt_results/Arizona Case Study/ra_phoenix", "AZ_5cacc7715457a393487780e2_fixed_PV_batt_large_NEM_Phoenix_Mandalay.json")

# outputs = reopt_results["outputs"]["Scenario"]["Site"]
# d = {"grid_purchases_kw" : [outputs["ElectricTariff"]["year_one_to_battery_series_kw"][ts] + outputs["ElectricTariff"]["year_one_to_load_series_kw"][ts] for ts in range(HOURS)]}


# d["net_load"] = [d["grid_purchases_kw"][h] - outputs["PV"]["year_one_to_grid_series_kw"][h] - outputs["Storage"]["year_one_to_grid_series_kw"][h] for h in range(HOURS)]
# d["home_load"] = [outputs["ElectricTariff"]["year_one_to_load_series_kw"][h] + outputs["PV"]["year_one_to_load_series_kw"][h] for h in range(HOURS)]
# d["annual_grid_purchases"] = sum(d["grid_purchases_kw"])
