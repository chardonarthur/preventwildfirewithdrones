import pandas as pd
import numpy as np
import sqlite3
import math

bd=sqlite3.connect('tipe.db')
curseur=bd.cursor()
curseur.execute("""SELECT DISTINCT Departemente, Code_INSEE, code_DFCI, Jour, Heure, Surface_parcourue_m2, pTempMax_Deg,
pTempMin_Deg,pWind_kmh, pWet_percent,pVisibility_km, pCloudCoverage_percent, pDayduration_hour, pregion, pTempMax_Deg_1,pTempMin_Deg_1,pWind_kmh_1, pWet_percent_1,pVisibility_km_1, pCloudCoverage_percent_1, pDayduration_hour_1
FROM liste_incendies_du_18_12_2021_blank2 JOIN (Donnees_meteo JOIN departement ON pregion=nom_region) ON pday=Jour;""")
data=curseur.fetchall()
bd.close()


"""
Ed=0.942H**0.679+11*math.exp((H-100)/10)+0.18*(21.1-T)*(1-math.exp(-0.115H))
Ew=0.618H**0.753+10*math.exp((H-100)/10)+0.18*(21.1-T)*(1-math.exp(-0.115H))
mo=147.2*(101-Fo)/(59.5+Fo)
m=Ed+(mo-Ed)*10**(-kd)
m=Ew-(Ew-mo)*10**(-kw)
mr=mo+42.5*rt*(math.exp(-100*(251-mo)))*(1-math.exp(-6.93/rt))
Fj_1=60
"""

def FFMCandISI(F,T,W,H):
    Fo=F
    mo=147.2*(101-Fo)/(59.5+Fo)
    m=0
    "calcul mo pour ro>0.5"
    if ro>0.5:
        rt=ro-0.5
        if mo<=150:
            mr=mo+42.5*rt*(math.exp(-100*(251-mo)))*(1-math.exp(-6.93/rt))
        else:
            mr=mo+42.5*rt*(math.exp(-100*(251-mo)))*(1-math.exp(-6.93/rt))+0.0015*((mo-150)**2)*rt**0.5
            mo=mr

    "calcul de m"
    Ed=0.942*H**0.679+11*math.exp((H-100)/10)+0.18*(21.1-T)*(1-math.exp(-0.115*H))
    if mo>Ed:
        ko=0.424*(1-((100-H)/100)**1.7)+0.0694*(W**0.5)*(1-(H/100)**8)
        kd=ko*0.581*math.exp(0.0365*T)
        m=Ed+(mo-Ed)*10**(-kd)
    elif mo<Ed:
        Ew=0.618*H**0.753+10*math.exp((H-100)/10)+0.18*(21.1-T)*(1-math.exp(-0.115*H))
        if mo<Ew:
            kl=0.424*(1-((100-H)/100)**1.7)+0.0694*(W**0.5)*(1-((H/100)/100)**8)
            kw=kl*0.581*math.exp(0.0365*T)
            m=Ew-(Ew-mo)*10**(-kw)
    else:
            m=mo
            
    "calcul indices"
    F=(59.5*(250-m))/(147.2+m) #FFMC
    
    fw=math.exp(0.05039*W)
    fF=91.9*math.exp(-0.1386*m*(1+m**5.31/(4.93*10**7)))
    R=0.208*fw*fF   #ISI
    
    return(F,R)

ro=0.5

Fo=80
To=10
Wo=15
Ho=60

def indices():
    L=[]
    for i in data:
        Fpp,Rpp=FFMCandISI(Fo,To,Wo,Ho) #cycle 1
        Tp=(i[14]+i[15])/2
        Hp=i[17]
        Wp=i[16]
        Fp,Rp=FFMCandISI(Fpp,Tp,Wp,Hp) #cycle 2
        T=(i[6]+i[7])/2
        H=i[9]
        W=i[8]
        F,R=FFMCandISI(Fp,T,W,H)
        S=i[5]                      #cycle 3
        L.append([F,R,S])
    return(L)

"""F/90+0.89*R/300+0.63*S**(1/2)/10**4"""

def file_end():
    L=indices()
    C1=[]
    C2=[]
    C3=[]
    C4=[]
    C5=[]
    C6=[]
    C7=[]
    C8=[]
    C9=[]
    C10=[]
    C11=[]
    C12=[]
    C13=[]
    C14=[]
    C15=[]
    C16=[]
    C17=[]
    for i in range(len(data)):
        x=0
        for el in [C1,C2,C3,C4,C5,C6,C7,C8,C9,C10,C11,C12,C13,C14]:
            el.append(data[i][x])
            x+=1
        C15.append(L[i][0])
        C16.append(L[i][1])
        C17.append(L[i][2])            
    df = pd.DataFrame({'Departement':C1,
                   'Code_INSEE':C2,
                    'pregion':C14,
                   'code_DFCI':C3,
                   'Jour':C4,
                   'Heure':C5,
                   'Surface_parcourue_m2':C6,
                   'pTempMax_Deg':C7,
                   'pTempMin_Deg':C8,
                   'pWind_kmh':C9,
                   'pWet_percent':C10,
                   'pVisibility_km':C11,
                   'pCloudCoverage_percent':C12,
                    'pDayduration_hour':C13,
                    'FFMC':C15,
                    'ISI':C16,
                    'SB':C17})

    df.to_csv('liste_incendies_ du_26_01_2022_carte', index=False)


def séparation_colomnes():
    
    GPS_path = 'liste_incendies_ du_26_01_2022_v2.csv' #nom fichier
    gps = pd.read_csv(GPS_path)
    Co=gps.Alerte

    C1 = gps.Annee
    C2 = gps.Numero,
    C3=gps.Type_de_feu
    C4=gps.Departement
    C5=gps.Code_INSEE
    C6=gps.Commune
    C7=gps.Lieu_dit
    C8=gps.code_DFCI
    C9=[]
    C9p=[]
    for el in Co:  
        C9.append(el[:10])
        C9p.append(el[11:])
    C10=gps.Origine_de_l_alerte
    C11=gps.Surface_parcourue_m2

    #print (len(C1),len(C3),len(C4),len(C5),len(C6),len(C7),len(C8),len(C9),len(C9p),len(C10))

    df = pd.DataFrame({'Annee':C1,
                   #'Numéro':C2,
                   'Type_de_feu':C3,
                   'Departemente':C4,
                   'Code_INSEE':C5,
                   'Commune':C6,
                   'Lieu_dit':C7,
                   'code_DFCI':C8,
                   'Jour':C9,
                   'Heure':C9p,
                   'Origine_de_l_alerte':C10,
                   'Surface_parcourue_m2':C11})

    df.to_csv('liste_incendies_ du_26_01_2022_evolved', index=False)

