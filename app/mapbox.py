import requests
# Your Mapbox Access Token
MAPBOX_ACCESS_TOKEN = 'pk.eyJ1IjoiamlyYXRoaXAiLCJhIjoiY2xsdTBoNzQ3MHdndzNzc3luaW03YmNseSJ9.CvqEW28-Dab5qUQ1MCQOgg'

def get_route(coordinates, access_token=MAPBOX_ACCESS_TOKEN):
    """
    Get the route between multiple locations using Mapbox API.

    Parameters:
        locations (list): A list of tuples containing the longitude and latitude of the locations.
        access_token (str): Your Mapbox access token.

    Returns:
        route (dict): A dictionary containing the route data as GeoJSON.
    """

    url = f"https://api.mapbox.com/directions/v5/mapbox/driving/{coordinates}"
    params = {
        'geometries': 'geojson',
        'access_token': access_token
    }
    response = requests.get(url, params=params)
    data = response.json()
    
    return data
