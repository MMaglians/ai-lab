from api_demo import Weather, parse_weather, summarize

def test_parse_weather():
    data = {"current": {"temperature_2m": 12.5, "wind_speed_10m": 7.0}}
    assert parse_weather(data) == Weather(temperature=12.5, wind=7.0)
    
def test_summarize():
    assert summarize(Weather(12.5, 7.0)) == "Temperatura: 12.5 C, vento: 7.0 km/h"