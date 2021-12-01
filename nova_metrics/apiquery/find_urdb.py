# import json 
import pandas as pd
import os
import requests
# os.chdir(os.path.dirname(__file__))
#%%
#Code finds urdb label for location. Will pull all active residential rates urdb of given utility and can find default rate for utility. 
#If google maps api key added can pull utility from long lat. Can get utility from zip code as well. 

def get_utility_data():
    IOU = pd.read_csv("../Data/iou_zipcodes_2019.csv")[["zip", "utility_name", "ownership"]]
    NonIOU = pd.read_csv("../Data/non_iou_zipcodes_2019.csv")[["zip", "utility_name", "ownership"]]
    data = pd.concat([IOU, NonIOU]).drop_duplicates()
    return data


UTILITY_DATA = get_utility_data()
UTILITY_SIZES = pd.read_csv("../Data/EIA_utility_sizes.csv")[["Entity","Customers (Count)"]].set_index("Entity").to_dict()["Customers (Count)"]
# google_api_key = "AIzaSyClR0k7J3W1i4yECOiVEcCW2dF0I_D7CdE"
# urdb_api_key = "2qt5uihpKXdywTj3uMIhBewxY9K4eNjpRje1JUPL"
#%%
#uses urdb api to extract utility rates. If single_label == TRUE then extracts only first rate. If return_default_rate == TRUE then returns default active rate.
def get_urdb_label(utility, api_key, sector = "Residential", return_default_rate = True, remove_phrases = ["Experimental"], single_label = True):
    utility_name = utility.replace("&", "%26").replace(" ", "+").replace(".", "")
    url = f"https://api.openei.org/utility_rates?version=latest&api_key={api_key}&ratesforutility={utility_name}&sector={sector}&approved=true"
    #Download rates which have not ended
    urdb = [x for x in requests.get(url).json()["items"] if not "enddate" in x]
    if return_default_rate:
        urdb = [x for x in urdb if "is_default" in x and x["is_default"]]
    for phrase in remove_phrases:
        urdb = [x for x in urdb if not phrase in x["name"]]
    
    if single_label:
        if len(urdb) > 0:
            return urdb[0]["label"]
        else:
            return input(f"Could not find default utility rate utility rate for {utility}. Please enter urdb label here:")
    else:
        return urdb
#%%
#uses google api to get latitude longitude and from location addres
def get_lat_lon_from_address(address, google_api_key):
    #Need to obtain a google api key. A credit card is required but api pulls are free for all but large downloads. 
    geo = requests.get(f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={google_api_key}").json()
    if geo["status"] == "OK":
        lat_long = geo["results"][0]["geometry"]["location"]
        return (lat_long["lat"], lat_long["lng"])
    else:
        print("api request failed:", geo["status"], "returning dummy long lats")
        return (39.7555, -105.2211)
#%%
#Uses google api to get address from latitude and longitude
def get_address_from_latlon(lat, lon, google_api_key):
    geo = requests.get(f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lon}&key={google_api_key}").json()
    if geo["status"] == "OK":
        address = geo["results"][0]["address_components"]
        address_components = {}
        for component in address:
            if component["types"] == ['locality', 'political']:
                address_components["locality"] = component["long_name"]
            elif component["types"] == ['postal_code']:
                address_components["zipcode"] = int(component["long_name"])
            elif component["types"] == ['administrative_area_level_2', 'political']:
                address_components["County"] = component["long_name"]
            elif component["types"] == ['administrative_area_level_1', 'political']:
                address_components["State"] = component["long_name"]
            elif component["types"] == ['postal_code_suffix']:
                address_components["zipcode_suffix"] = int(component["long_name"])
    if not "zipcode" in address_components:
        address_components["zipcode"] = input(f"Could not find zipcode for {address_components}. Please input here:")
        
    return address_components
    

#%%
#Extracts list of utilities at zip code
def get_utilities_at_zip(zipcode, return_all = False):
    utilities_at_zip = UTILITY_DATA.loc[UTILITY_DATA["zip"] == zipcode]["utility_name"].values.tolist()
    if return_all:
        return utilities_at_zip
    N = len(utilities_at_zip)
    if N == 0:
        return input(f"Could not find utility at zip code {zipcode}. Please input utility name here (or input ''): ")
    elif N == 1:
        return utilities_at_zip[0]
    else:
        num_customers = [0 for i in range(N)]
        for i in range(N):
            if utilities_at_zip[i] in UTILITY_SIZES:
                num_customers[i] = UTILITY_SIZES[utilities_at_zip[i]]
        return utilities_at_zip[num_customers.index(max(num_customers))]

#%%
# get_urdb_label('Public Service Co of Colorado', api_key, sector = "Residential", return_default_rate = True, remove_phrases = ["Experimental"], single_label = True)
def get_default_urdb_label(urdb_api_key, zipcode = None, utility_name = None, lat = None, lon = None, google_api_key = None):
    if utility_name == None:
        if zipcode == None:
            #If zipcode is unavailable then reverse geocode lon lat to get zipcode
            if lon == None or lat == None:
                print("Need to specify a utility_name, zipcode, or latitude and longitude")
                return ""
            else:
                zipcode = get_address_from_latlon(lat, lon, google_api_key)["zipcode"]
        utility_name = get_utilities_at_zip(zipcode, return_all = False)
        
    return get_urdb_label(utility_name, urdb_api_key, sector = "Residential", return_default_rate = True, remove_phrases = [], single_label = True)

# google_api_key = "AIzaSyClR0k7J3W1i4yECOiVEcCW2dF0I_D7CdE"
# urdb_api_key = "2qt5uihpKXdywTj3uMIhBewxY9K4eNjpRje1JUPL"
# # add_urdb_label(urdb_api_key, zipcode = 22201, utility_name = None, lon = None, lat = None, google_api_key = google_api_key)
# # get_utilities_at_zip(80302, UTILITY_DATA, UTILITY_SIZES, return_all = False)
# google_api_key = "AIzaSyClR0k7J3W1i4yECOiVEcCW2dF0I_D7CdE"
# lat = 29.7604267
# lon =   -95.3698028
# address = get_address_from_latlon(lat, lon, google_api_key = "AIzaSyClR0k7J3W1i4yECOiVEcCW2dF0I_D7CdE")
# # utility = get_utilities_at_zip(address["zipcode"], return_all = False)
# # urdb_label = get_urdb_label(utility, urdb_api_key, sector = "Residential", return_default_rate = True, remove_phrases = ["Experimental"], single_label = True)
# get_address_from_latlon(45.5230622,	-122.6764816, google_api_key)
