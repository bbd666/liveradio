import requests
import openmeteo_requests
import json
import pandas as pd
import requests_cache
from retry_requests import retry


def get_weather_description(code: int) -> str:
    """Convert Open-Meteo weather code to a textual description."""
    if code == 0:
        return "Ciel clair"
    elif code in (1, 2, 3):
        return "Ciel principalement clair/ partiellement nuageux/couvert"
    elif code in (45, 48):
        return "Brouillard"
    elif code in (51, 53, 55):
        return "Brume"
    elif code in (56, 57):
        return "Brouillard verglacant"
    elif code in (61, 63, 65):
        return "Pluie"
    elif code in (66, 67):
        return "pluie verglacante"
    elif code in (71, 73, 75):
        return "Chute de neige"
    elif code == 77:
        return "Flocons"
    elif code in (80, 81, 82):
        return "Averses"
    elif code in (85, 86):
        return "Giboulées de neige"
    elif code == 95:
        return "Orages"
    elif code in (96, 99):
        return "Orages avec grêle"
    else:
        return "Unknown weather"
    
# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

city='liverdun' # replace any city of country
result_city = requests.get(url='https://geocoding-api.open-meteo.com/v1/search?name=' + city)
location = result_city.json()

longitude=str(location['results'][0]['longitude'])
latitude=str(location['results'][0]['latitude'])

# Make sure all required weather variables are listed here
# The order of variables in hourly or daily is important to assign them correctly below
url = "https://api.open-meteo.com/v1/forecast"
params = {
	"latitude": latitude,
	"longitude": longitude,
	"hourly": ["temperature_2m", "precipitation_probability", "rain", "wind_speed_10m", "weather_code"],
}
responses = openmeteo.weather_api(url, params=params)

# Process first location. Add a for-loop for multiple locations or weather models
response = responses[0]
print(f"Coordinates: {response.Latitude()}°N {response.Longitude()}°E")
print(f"Elevation: {response.Elevation()} m asl")
print(f"Timezone difference to GMT+0: {response.UtcOffsetSeconds()}s")

# Process hourly data. The order of variables needs to be the same as requested.
hourly = response.Hourly()
hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
hourly_precipitation_probability = hourly.Variables(1).ValuesAsNumpy()
hourly_rain = hourly.Variables(2).ValuesAsNumpy()
hourly_wind_speed_10m = hourly.Variables(3).ValuesAsNumpy()
hourly_weather_code = hourly.Variables(4).ValuesAsNumpy()

hourly_data = {"date": pd.date_range(
	start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
	end = pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
	freq = pd.Timedelta(seconds = hourly.Interval()),
	inclusive = "left"
)}

hourly_data["temperature_2m"] = hourly_temperature_2m
hourly_data["precipitation_probability"] = hourly_precipitation_probability
hourly_data["rain"] = hourly_rain
hourly_data["wind_speed_10m"] = hourly_wind_speed_10m
hourly_data["weather_code"] = hourly_weather_code

hourly_dataframe = pd.DataFrame(data = hourly_data)
print("\nHourly data\n", hourly_dataframe)
#print(hourly_temperature_2m[1])
print(get_weather_description(hourly_weather_code[2]))
print(get_weather_description(hourly_weather_code[3]))
print(hourly_weather_code[28])
print(get_weather_description(hourly_weather_code[28]))

