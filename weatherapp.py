import requests
import ujson
from iso3166 import countries
import country_converter as coco
import datetime

APIKEY = "20a5b7e9f72e96c2e49942191ce3d94d"

def get_coordinates():
    """
    Compute the co-ordinates of the city. (NEEDED FOR CURRENT WEATHER)
    """
    countrycode = getcc()
    c_lat, c_lon = getcitycord(countrycode)
    print("Getting coordinates")
    return c_lat, c_lon 

def getcitycord(countrycode):
    """To get the city co-ordinates

    Args:
        countrycode (int): _The country specified's ISO3166 country code_
print("Getting coordinates")
    Returns:
        _(2)integers_: _geographic co-ordinates of the city in "lat" and "long" (needed for API request)_ 
    """
    # statecode = None #For American cities only - maybe do? works fine without.
    limit = 1
    cityname = input("Enter city name: ")
    try:
        print("Fetching co-ordinates data...")
        apireq = requests.get(f"http://api.openweathermap.org/geo/1.0/direct?q={cityname},{countrycode}&limit={limit}&appid={APIKEY}")
    except ConnectionError:
        print("City not found. Timed out")
    print("Parsing co-ordinates json")
    apiinfo = ujson.loads(apireq.text)
    try:
        city_data = apiinfo[0]
        lat = city_data.get("lat")
        lon = city_data.get("lon")
        return lat, lon
    except requests.exceptions.RequestException as e:
        print(f"Error fetching coordinates data: {e}")
    except (IndexError, KeyError):
        print("Country not found. Please try again...")
    except ValueError:
        print("Error parsing JSON data. Please try again...")
    return None, None

def getcc():
    """
    Finds the country code using iso1366 module
    
    returns: numeric countrycode
    """    
    while True: 
        country = input("Enter country: ")
        country_name = country.strip()
        try:
            standard_name = coco.convert(names=country_name, to='ISO3')
            countrycode = countries.get(standard_name)
            return countrycode.numeric
        except KeyError:
            print("Error. Country not found. Please try again")

def get_currentAPI(lat, lon):
    """_Inputs the co-ordinates and retreives the json of CURRENT weather data_

    Args:
        lat (float): _latitude of location_
        lon (float): _longitude of location_
    Returns:
    Parsed JSON FILE as python list. Contains all *current* weather information
    """
    try:
        print("Fetching current weather")
        currentAPI = requests.get(f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={APIKEY}&units=metric")
        print("Parsing current weather json") #
        current_data = ujson.loads(currentAPI.text)
        return current_data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching current weather data: {e}")
    except ValueError:
        print("Error parsing JSON data for current weather. Please try again...")
        return None

def get_current_weather(current_data):
    """
    Retrieves keys from the original current weather API dictionaries.

    Args:
        current_data (dictionary): Contains all the current weather data from the API

    Returns:
        _string_: (City) name, (Sky) conditions, current (temp) in celcius
    """
    if current_data:
        city = current_data.get('name')
        sky = current_data.get('weather')[0].get('main') #just following the flow of the data and json
        if sky == "Clouds":
            sky = "cloudy"
        temperature = current_data.get('main').get('temp')
        humidity = current_data.get('main').get('humidity')
        celcius = round(float("{:.1f}".format(temperature)))
        return city, sky, celcius, humidity
    return None, None, None
def get_city_id(city):
    """_Takes a city and searches for the OpenWeather city ID. (ID is reuired for API requests)

    Args:
        city (_string_): User input of the city to get the id for 

    Returns:
        _int_: City ID that matches the search term
    """
    print("finding city id")
    with open(f"city_index.json", encoding="utf-8", mode='r') as file:
        city_index = ujson.load(file)
        city_lower = city.lower()
        results = {}
        for place in city_index:
            if city_lower in place.lower():
                results[place] = city_index.get(f"{place}")
        if len(results) == 1:
            for i in results:
                city = results.get(i)
                cityID = city['id']
                return cityID
        else:
            if len(results) == 0:
                print("No matches found.")
            elif 0 <= len(results) <= 10:
                print("Which city do you mean?")
                for number, place in enumerate(results, start=1):
                    print(f"{number}. {place}, {results.get(place)['country']}")
                try:
                    choice = int(input("Choose the city number: "))
                    if 1 <= choice <= len(results):
                        selected_city = list(results.keys())[choice - 1]
                        cityID = results[selected_city]['id']
                        return cityID
                    else:
                        print("Invalid choice.")
                        return None
                except ValueError:
                    print("Invalid input. Please enter a number.")
                    return None
            else:
                print("Too many matches. Please refine your search")
        return None



def get_forecastAPI(city_id):
    """Request the api forecast data for the city ID

    Args:
        city_id (_int_): City id from get_city_id

    Returns:
        _json file_: cotnains forecast dat.  probably requires preprocessing. will get to sometime
    """
    print("Fetching forecast data...")
    try:
        forecast_data = requests.get(f"https://api.openweathermap.org/data/2.5/forecast?id={city_id}&appid={APIKEY}&units=metric")
        return ujson.loads(forecast_data.text)['list']
    except Exception as e:
        print(f"Error fetching forecast data: {e}")
        return None
    

def get_forecast(forecast_data):
    """Prints the forecast data 

    Args:
        forecast_data (list of dict): contains various descriptions of the weather in nested dictionaries
    """
    forecast = []
    for i in forecast_data:
        time = i['dt']
        temp = round(i['main']['temp'])
        humidity = i['main']['humidity']
        info = {'celcius' : temp, 'humidity' : humidity}
        entry = {'time': time, 'info': info}
        forecast.append(entry) 
    for i in range(0, len(forecast), 2):
        data = forecast[i]['info']
        unixtime = forecast[i].get('time')
        time = datetime.datetime.fromtimestamp(unixtime, datetime.UTC).strftime('%Y-%m-%d %H:%M')
        print(f"{time}: Temp:{data['celcius']}°C Humidity: {data['humidity']}%")

def main_current():
    """Runs the functions need to retrive current weather
    """
    lat, lon = get_coordinates()
    if lat and lon:
        current_data = get_currentAPI(lat, lon)
        if current_data:
            city, sky, celcius, humidity = get_current_weather(current_data)
            if city and sky and celcius and humidity is not None:
                print(f"The current weather in {city} is {celcius}°C and {sky} with a humidity of {humidity}%.")
    else:
        print("Error. Debug")


def main_forecast():
    """
    Runs the functions needed to retrieve 5 day weather forecast
    """
    city_input = input("City: ")
    city_id = get_city_id(city_input)
    if city_id:
        forecast_data = get_forecastAPI(city_id)
        if forecast_data:
            get_forecast(forecast_data)
            print("You worked out the data format and unix timestamp")
        else:
            print("Failed to retrieve forecast data.") 
    else:
        print("Please try again")   
       
def menu():
    """
    Displays the menu and handles user input.
    """
    
    while True:
        print("--- Welcome to the Weather App ---")
        print("1. Get Current Weather")
        print("2. Get 5-Day Weather Forecast")
        print("3. Exit")
        choice = input("Choose an option: ")
        if choice == '1':
            main_current()
        elif choice == '2':
            main_forecast()
        elif choice == '3':
            print("Exiting the Weather App. Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")
if __name__ == "__main__":
    menu()



