from flask import Blueprint, render_template, request, redirect, url_for
import requests
import ujson
from iso3166 import countries
import country_converter as coco
import datetime
from flask import Flask

app = Flask(__name__)

@app.template_filter('datetimeformat')
def datetimeformat(value, format='%Y-%m-%d %H:%M'):
    return datetime.datetime.fromtimestamp(value, datetime.UTC).strftime(format)

APIKEY = "20a5b7e9f72e96c2e49942191ce3d94d"

main = Blueprint('main', __name__)

@main.route('/')
def home():
    return render_template('home.html')

@main.route('/current_weather', methods=['GET', 'POST'])
def current_weather():
    if request.method == 'POST':
        country = request.form['country']
        city = request.form['city']
        lat, lon = get_coordinates(city, country)
        if lat and lon:
            current_data = get_currentAPI(lat, lon)
            if current_data:
                city, sky, celcius, humidity = get_current_weather(current_data)
                return render_template('current_weather.html', city=city, sky=sky, celcius=celcius, humidity=humidity)
    return render_template('current_weather.html')

@main.route('/forecast', methods=['GET', 'POST'])
def forecast():
    if request.method == 'POST':
        city = request.form['city']
        city_id = get_city_id(city)
        if city_id:
            forecast_data = get_forecastAPI(city_id)
            if forecast_data:
                forecast = process_forecast(forecast_data)
                return render_template('forecast.html', forecast=forecast)
    return render_template('forecast.html')

def get_coordinates(cityname, countryname):
    countrycode = getcc(countryname)
    c_lat, c_lon = getcitycord(cityname, countrycode)
    return c_lat, c_lon

def getcitycord(cityname, countrycode):
    limit = 1
    try:
        apireq = requests.get(f"http://api.openweathermap.org/geo/1.0/direct?q={cityname},{countrycode}&limit={limit}&appid={APIKEY}")
    except ConnectionError:
        print("City not found. Timed out")
    apiinfo = ujson.loads(apireq.text)
    try:
        city_data = apiinfo[0]
        lat = city_data.get("lat")
        lon = city_data.get("lon")
        return lat, lon
    except Exception as e:
        print(f"Error fetching coordinates data: {e}")
    return None, None

def getcc(country_name):
    try:
        standard_name = coco.convert(names=country_name, to='ISO3')
        countrycode = countries.get(standard_name)
        return countrycode.alpha2
    except KeyError:
        print("Error. Country not found.")
        return None

def get_currentAPI(lat, lon):
    try:
        currentAPI = requests.get(f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={APIKEY}&units=metric")
        current_data = ujson.loads(currentAPI.text)
        return current_data
    except Exception as e:
        print(f"Error fetching current weather data: {e}")
        return None

def get_current_weather(current_data):
    if current_data:
        city = current_data.get('name')
        sky = current_data.get('weather')[0].get('main')
        if sky == "Clouds":
            sky = "cloudy"
        temperature = current_data.get('main').get('temp')
        humidity = current_data.get('main').get('humidity')
        celcius = round(float("{:.1f}".format(temperature)))
        return city, sky, celcius, humidity
    return None, None, None, None

def get_city_id(city):
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
            return None

def get_forecastAPI(city_id):
    try:
        forecast_data = requests.get(f"https://api.openweathermap.org/data/2.5/forecast?id={city_id}&appid={APIKEY}&units=metric")
        return ujson.loads(forecast_data.text)['list']
    except Exception as e:
        print(f"Error fetching forecast data: {e}")
        return None

def process_forecast(forecast_data):
    forecast = []
    for i in forecast_data:
        time = i['dt']
        temp = round(i['main']['temp'])
        humidity = i['main']['humidity']
        info = {'celcius' : temp, 'humidity' : humidity}
        entry = {'time': time, 'info': info}
        forecast.append(entry)
    return forecast

from flask import Flask

app = Flask(__name__)

@app.template_filter('datetimeformat')
def datetimeformat(value, format='%Y-%m-%d %H:%M'):
    return datetime.datetime.fromtimestamp(value, datetime.UTC).strftime(format)
