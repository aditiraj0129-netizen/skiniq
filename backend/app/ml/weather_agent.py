"""
Weather/UV Agent: fetches real current UV index and weather conditions from
Open-Meteo (free, no API key required) -- used to add sun-exposure context
to symptom analysis.
"""
import requests

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def get_weather_context(lat: float, lng: float) -> dict:
    """
    Returns current UV index and temperature for the given coordinates.
    Fails gracefully (returns None fields) if the API is unreachable --
    weather context is a nice-to-have, not a hard dependency.
    """
    try:
        response = requests.get(
            OPEN_METEO_URL,
            params={
                "latitude": lat,
                "longitude": lng,
                "current": "temperature_2m,uv_index",
                "timezone": "auto",
            },
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()
        current = data.get("current", {})
        return {
            "uv_index": current.get("uv_index"),
            "temperature_c": current.get("temperature_2m"),
            "available": True,
        }
    except Exception:
        return {"uv_index": None, "temperature_c": None, "available": False}


def interpret_uv(uv_index: float | None) -> str | None:
    if uv_index is None:
        return None
    if uv_index >= 8:
        return "Very high UV today -- sun exposure is a plausible contributing factor for exposed-skin symptoms."
    if uv_index >= 6:
        return "High UV today -- sun exposure may be worth considering as a contributing factor."
    if uv_index >= 3:
        return "Moderate UV today."
    return "Low UV today -- sun exposure is less likely to be a primary factor right now."