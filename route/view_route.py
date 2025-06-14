import folium
import csv
from geopy.distance import geodesic

def create_map():
    m = folium.Map(location=[13.2346538, 80.2781245], zoom_start=17)
    points = []
    
    with open('route_data.csv') as f:
        reader = csv.reader(f)
        next(reader)
        points = [(float(row[0]), float(row[1])) for row in reader]
    
    # Add route line
    folium.PolyLine(
        locations=points,
        color='#FF4500',
        weight=6,
        opacity=0.8
    ).add_to(m)
    
    # Add 50m distance markers
    for i, point in enumerate(points):
        # if i % 5 == 0:  # 10m * 5 = 50m markers
        if i % 1 == 0:  # 10m * 5 = 50m markers
            folium.Marker(
                location=point,
                icon=folium.DivIcon(html=f'<div style="font-weight:bold">{i*10}m</div>')
            ).add_to(m)
    
    m.save('10m_route_map.html')
    print("Map with 50m markers saved to 10m_route_map.html")

if __name__ == "__main__":
    create_map()