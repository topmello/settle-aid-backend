import requests

from .config import settings
# Your Mapbox Access Token
MAPBOX_ACCESS_TOKEN = settings.MAPBOX_ACCESS_TOKEN

def get_route(coordinates, profile='walking'):
    """
    Get the route between multiple locations using Mapbox API.

    Parameters:
        locations (list): A list of tuples containing the longitude and latitude of the locations.
        access_token (str): Your Mapbox access token.

    Returns:
        route (dict): A dictionary containing the route data as GeoJSON.
    """

    url = f"https://api.mapbox.com/directions/v5/mapbox/{profile}/{coordinates}"
    params = {
        'geometries': 'geojson',
        'access_token': MAPBOX_ACCESS_TOKEN,
        'steps': 'true'
    }
    response = requests.get(url, params=params)
    data = response.json()
    
    return data
