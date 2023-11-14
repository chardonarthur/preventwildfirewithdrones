import folium
from folium import IFrame
import os
import base64


m = folium.Map(location=[48.690602, 2.088856], zoom_start=17)
walkData = os.path.join('flight.json')

folium.GeoJson(walkData, name='flight').add_to(m)
m.save("essaivol.html");





