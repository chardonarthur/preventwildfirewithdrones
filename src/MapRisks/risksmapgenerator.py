import folium
import pandas as pd
import numpy as np
import requests
import lxml.html as lh
from datetime import datetime, timedelta
import sys
import getopt
import locale
import math
from folium.plugins import HeatMap

mapObj = folium.Map(location=[43.73297657196887, 4.953574013028534], zoom_start=8) 

incendiesLayer = folium.FeatureGroup("Historical Fires") 
incendiesLayer.add_to(mapObj)

import sqlite3
bd = sqlite3.connect('tipe.db')
curseur = bd.cursor()
curseur.execute("""SELECT * FROM liste_incendies_du_26_01_2022_carte JOIN DFCI_2x2_v2 ON SUBSTR(code_DFCI,1,6)=numb;""")
data = curseur.fetchall()
bd.close()

"""
path = 'liste_incendies_ du_26_01_2022_carte.csv'  # file name
data = pd.read_csv(path)
"""

mapData = []
for a in data: 
    latVal = a[-2]
    lngVal = a[-1]
    FFMC = a[-9]
    ISI = a[-8]
    SB = a[-7]
    IR = math.exp(FFMC / 10) * 0.35 * 10 ** (-3) + 0.89 * ISI / 6 + 0.63 * math.log1p(SB) / 4.5
    surVal = a[6]  # surface burned
    Code_DFCI = a[3]
    Rayon = (SB / np.pi) ** (1 / 2)

    if IR < 1:
        clr = "cyan"
    if 1 <= IR < 2:
        clr = "black"
    elif 2 <= IR < 4:
        clr = "blue"
        if Rayon < 200:
            Rayon = 200
    elif 4 <= IR < 6:
        clr = "yellow"
        if Rayon < 400:
            Rayon = 400
    elif 6 <= IR < 10:
        clr = "orange"
        if Rayon < 600:
            Rayon = 600
    else:
        if Rayon < 800:
            Rayon = 800
        clr = "red"

    radius = Rayon
    iframe = folium.IFrame('Coordinates: ' + str(lngVal) + ' , ' + str(latVal) + '<br>' + 'SB: ' + str(
        SB) + ' m^2' + '<br>' + 'VPI: ' + str(ISI) + '<br>' + 'CS: ' + str(FFMC) + '<br>' + 'IR (Resulting Index): ' + str(IR))
    folium.Circle(
        location=[lngVal, latVal],
        radius=radius,
        color=clr,
        weight=2,
        fill=True,
        fill_color=clr,
        fill_opacity=0.1,
        popup=folium.Popup(iframe, min_width=300, max_width=300)
    ).add_to(incendiesLayer)

legendHtml = '''
     <div style="position: fixed; 
     bottom: 80px; left: 50px; width: 110px; height: 150px; 
     border:2px solid grey; z-index:9999;background-color:white;
     opacity: .85; font-size:16px;
     ">&nbsp; Indices <br>
     &nbsp; <i class="fa fa-circle"
                  style="color:black"></i> &nbsp; 1-2<br>
     &nbsp; <i class="fa fa-circle"
                  style="color:blue"></i> &nbsp; 2-4<br>
     &nbsp; <i class="fa fa-circle"
                  style="color:yellow"></i> &nbsp; 4-6<br>
     &nbsp; <i class="fa fa-circle"
                  style="color:orange"></i> &nbsp; 6-10<br>
     &nbsp; <i class="fa fa-circle"
                  style="color:red"></i> &nbsp; 10 and +<br>
      </div>
     '''

mapObj.get_root().html.add_child(folium.Element(legendHtml))

folium.LayerControl().add_to(mapObj)
mapObj.save('RisksMap.html')
