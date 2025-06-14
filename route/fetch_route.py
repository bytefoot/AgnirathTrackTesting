import requests
import csv
import polyline
from geopy.distance import geodesic

# --- Google Maps Directions API (Route) ---
GOOGLE_API_KEY = "AIzaSyB1fFyFTdCrb0XKH53XpApt8jSBE3VR-O4"  # Replace with your key

def get_google_route():
    origin = "13.2346538,80.2781245"
    waypoints = [
        "13.2323194,80.2797041",
        "13.234185,80.2818078"
    ]
    
    url = f"https://maps.googleapis.com/maps/api/directions/json?origin={origin}&destination={origin}&waypoints={'|'.join(waypoints)}&key={GOOGLE_API_KEY}"
    response = requests.get(url).json()
    
    if response['status'] != 'OK':
        raise Exception(f"Google API Error: {response['status']}")
    
    return polyline.decode(response['routes'][0]['overview_polyline']['points'])

# --- Open-Elevation API (Free) ---
def get_elevation_osm(points):
    url = "https://api.open-elevation.com/api/v1/lookup"
    locations = [{"latitude": lat, "longitude": lon} for lat, lon in points]
    
    response = requests.post(url, json={"locations": locations}).json()
    return [result['elevation'] for result in response['results']]

# --- Interpolate Points (10m spacing) ---
def interpolate_points(points, interval=10):
    interpolated = []
    for i in range(len(points)-1):
        start, end = points[i], points[i+1]
        distance = geodesic(start, end).meters
        steps = int(distance // interval)
        
        for step in range(steps + 1):
            ratio = step / steps if steps > 0 else 0
            lat = start[0] + (end[0] - start[0]) * ratio
            lon = start[1] + (end[1] - start[1]) * ratio
            interpolated.append((lat, lon))
    return interpolated

# --- Save Data ---
def save_to_csv(points, elevations):
    with open('route_data.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Latitude', 'Longitude', 'Elevation (m)'])
        for (lat, lon), elev in zip(points, elevations):
            writer.writerow([lat, lon, round(elev, 1) if elev else ''])

if __name__ == "__main__":
    route_points = get_google_route()
    dense_points = interpolate_points(route_points, interval=10)
    elevations = get_elevation_osm(dense_points)
    save_to_csv(dense_points, elevations)
    print(f"Generated {len(dense_points)} points in hybrid_route_data.csv")