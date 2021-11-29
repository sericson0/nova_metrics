# import sys, os
import pandas as pd
# os.chdir(os.path.dirname(__file__))
#%%
# # Declare all variables as strings. Spaces must be replaced with '+', i.e., change 'John Smith' to 'John+Smith'.
# # Define the lat, long of the location and the year
# lat, lon, year = 33.2164, -97.1292, 2019
# api_key = 'gAfosXcQ9Ldfw3qXqvKVb7PxMEkYigozmC9R3mXQ'
# # Set the attributes to extract (e.g., dhi, ghi, etc.), separated by commas.
# # attributes = 'ghi,dhi,dni,wind_speed,air_temperature,solar_zenith_angle'
# attributes = 'dni,ghi,dhi,air_temperature,wind_speed'
# #DHI	DNI	GHI	Clearsky DHI	Clearsky DNI	Clearsky GHI	Cloud Type	Dew Point	Solar Zenith Angle	Fill Flag	Surface Albedo	Wind Speed	Precipitable Water	Wind Direction	Relative Humidity	Temperature	Pressure
# #%%
# # Choose year of data
# year = '2019'
# # Set leap year to true or false. True will return leap day data if present, false will not.
# leap_year = 'false'
# # Set time interval in minutes, i.e., '30' is half hour intervals. Valid intervals are 30 & 60.
# interval = '30'
# # Specify Coordinated Universal Time (UTC), 'true' will use UTC, 'false' will use the local time zone of the data.
# # NOTE: In order to use the NSRDB data in SAM, you must specify UTC as 'false'. SAM requires the data to be in the
# # local time zone.
# utc = 'false'
# # Your full name, use '+' instead of spaces.
# # your_name = 'Sean+Ericson'
# your_name = 'Kights+Who+Say+Ni'
# # Your reason for using the NSRDB.
# reason_for_use = 'Seek+The+Holy+Grail'
# # Your affiliation
# your_affiliation = 'Nunya+Buisness'
# # Your email address
# your_email = 'made.up@nrel.gov'
# #%%
# # Please join our mailing list so we can keep you up-to-date on new developments.
# mailing_list = 'false'

# # Declare url string
# url = 'https://developer.nrel.gov/api/nsrdb/v2/solar/psm3-download.csv?wkt=POINT({lon}%20{lat})&names={year}&leap_day={leap}&interval={interval}&utc={utc}&full_name={name}&email={email}&affiliation={affiliation}&mailing_list={mailing_list}&reason={reason}&api_key={api}&attributes={attr}'.format(year=year, lat=lat, lon=lon, leap=leap_year, interval=interval, utc=utc, name=your_name, email=your_email, mailing_list=mailing_list, affiliation=your_affiliation, reason=reason_for_use, api=api_key, attr=attributes)
# # Return just the first 2 lines to get metadata:
# # info = pd.read_csv(url, nrows=1)
# nsrdb = pd.read_csv(url)
# nsrdb.to_csv("NSRDB_test.csv", index = False)
# See metadata for specified properties, e.g., timezone and elevation
# timezone, elevation = info['Local Time Zone'], info['Elevation']
#All potential outputs
# 'air_temperature',
#  'clearsky_dhi',
#  'clearsky_dni',
#  'clearsky_ghi',
#  'cloud_type',
#  'coordinates',
#  'dew_point',
#  'dhi',
#  'dni',
#  'fill_flag',
#  'ghi',
#  'meta',
#  'relative_humidity',
#  'solar_zenith_angle',
#  'surface_albedo',
#  'surface_pressure',
#  'time_index',
#  'total_precipitable_water',
#  'wind_direction',
 # 'wind_speed'
 
#download_nsrdb downloads weather file required for OCHRE runs.
#NSRDB requires a variety of inputs, but seems to run fine with dummy inputs added.
def download_nsrdb(filename, lat, lon, api_key, year = 2019, leap_year = "false", 
                   your_name = 'Kights+Who+Say+Ni', reason_for_use = 'Seek+The+Holy+Grail', 
                   your_affiliation = 'Nunya+Buisness', your_email = 'made.up@nrel.gov'):
    interval = '30'
    utc = 'false'
    mailing_list = 'false'
    attributes = 'dni,ghi,dhi,air_temperature,wind_speed,surface_pressure,relative_humidity'
    url = 'https://developer.nrel.gov/api/nsrdb/v2/solar/psm3-download.csv?wkt=POINT({lon}%20{lat})&names={year}&leap_day={leap}&interval={interval}&utc={utc}&full_name={name}&email={email}&affiliation={affiliation}&mailing_list={mailing_list}&reason={reason}&api_key={api}&attributes={attr}'.format(year=year, lat=lat, lon=lon, leap=leap_year, interval=interval, utc=utc, name=your_name, email=your_email, mailing_list=mailing_list, affiliation=your_affiliation, reason=reason_for_use, api=api_key, attr=attributes)
    pd.read_csv(url).to_csv(filename, index = False)
    
    