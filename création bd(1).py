#Tout est mis en commentaire pour ne pas exécuter à nouveau ce fichier.



import sqlite3
bd=sqlite3.connect('tipe.db')
curseur=bd.cursor()

curseur.executescript('''
CREATE TABLE DFCI_2x2_v2(XCoord,YCoord,FID,numb,lat,lng);
''')

curseur.executescript('''
CREATE TABLE Donnees_meteo(Num,pday,pTempMax_Deg,pTempMin_Deg,pWind_kmh,pWet_percent,pVisibility_km,pCloudCoverage_percent,pDayduration_hour,pregion,
pTempMax_Deg_1,pTempMin_Deg_1,pWind_kmh_1,pWet_percent_1,pVisibility_km_1,pCloudCoverage_percent_1,pDayduration_hour_1);
''')

curseur.executescript('''
CREATE TABLE departement(code_departement,nom_departement,code_region,nom_region);
''')

curseur.executescript('''
CREATE TABLE liste_incendies_du_18_12_2021_blank2(Annee,Type_de_feu,Departemente,Code_INSEE,Commune,Lieu_dit,code_DFCI,Jour,Heure,Origine_de_l_alerte,Surface_parcourue_m2);
''')

curseur.executescript('''
CREATE TABLE liste_incendies_du_26_01_2022_carte(Departement,Code_INSEE,pregion,code_DFCI,Jour,Heure,Surface_parcourue_m2,pTempMax_Deg,pTempMin_Deg,pWind_kmh,pWet_percent,
        pVisibility_km,pCloudCoverage_percent,pDayduration_hour,FFMC,ISI,SB);
''')


import pandas

fichier=pandas.read_csv('C:/Users/User/Documents/Prépa CPGE/TIPE/exp1/annexe/DFCI_2x2_v2.csv',delimiter=',')
fichier.to_sql('DFCI_2x2_v2',bd,if_exists='append',index = False)

fichier=pandas.read_csv('C:/Users/User/Documents/Prépa CPGE/TIPE/exp1/annexe/departements-francev3.csv',delimiter=',')
fichier.to_sql('departement',bd,if_exists='append',index = False)

fichier=pandas.read_csv('C:/Users/User/Documents/Prépa CPGE/TIPE/exp1/annexe/liste_incendies_ du_26_01_2022_evolved.csv',delimiter=',')
fichier.to_sql('liste_incendies_du_18_12_2021_blank2',bd,if_exists='append',index = False)

fichier=pandas.read_csv('C:/Users/User/Documents/Prépa CPGE/TIPE/exp1/annexe/donnees_meteo.csv',delimiter=',')
fichier.to_sql('Donnees_meteo',bd,if_exists='append',index = False)

fichier=pandas.read_csv('C:/Users/User/Documents/Prépa CPGE/TIPE/exp1/annexe/liste_incendies_ du_26_01_2022_carte.csv',delimiter=',')
fichier.to_sql('liste_incendies_du_26_01_2022_carte',bd,if_exists='append',index = False)

bd.close()



