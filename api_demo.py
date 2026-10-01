from dataclasses import dataclass

import requests #client HTTP installato con uv

URL = "https://api.open-meteo.com/v1/forecast"


@dataclass
class Weather:
    temperature: float
    wind: float


def fetch_weather(lat: float, lon: float) -> dict:
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,wind_speed_10m",
    }
    response = requests.get(URL, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def parse_weather(data: dict) -> Weather:
    current = data["current"]
    return Weather(
        temperature=current["temperature_2m"],
        wind=current["wind_speed_10m"],
    )


def summarize(weather: Weather) -> str:
    return f"Temperatura: {weather.temperature} C, vento: {weather.wind} km/h"


def main() -> None:
    try:
        data = fetch_weather(45.07, 7.69)  # Torino
        print(summarize(parse_weather(data)))
    except requests.exceptions.RequestException as e:
        print(f"Errore di rete: {e}")
    except KeyError as e:
        print(f"Campo mancante nella risposta: {e}")


if __name__ == "__main__":
    main()