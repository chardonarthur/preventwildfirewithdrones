import pandas as pd
import numpy as np
import requests
import lxml.html as lh
from datetime import datetime, timedelta
import sys
import getopt
import locale

urlbase= "https://www.historique-meteo.net/france"

# Labels to grab
labels = ['TempÃ©rature maximale',
          'TempÃ©rature minimale',
          'Vitesse du vent',
          'HumiditÃ©',
          'VisibilitÃ©',
          'Couverture nuageuse',
          'DurÃ©e du jour']

# Old regions (but the web site refers to these regions
regions = ['alsace',
            'aquitaine',
            'ardeche',
            'auvergne',
            'bourgogne',
            'bretagne',
            'centre',
            'champagne-ardenne',
            'corse',
            'franche-comte',
            'ile-de-re',
            'ile-de-france',
            'languedoc-roussillon',
            'limousin',
            'lorraine',
            'midi-pyrenees',
            'nord-pas-de-calais',
            'normandie',
            'pays-de-la-loire',
            'picardie',
            'poitou-charentes',
            'rh-ne-alpes',
            'provence-alpes-c-te-d-azur']

# New French regions breakdown
reg_target = ['Île-de-France', 'Nouvelle-Aquitaine', 'Auvergne-Rhône-Alpes',
       'Bourgogne-Franche-Comté', 'Hauts-de-France', 'Grand Est',
       'Guadeloupe', 'Martinique', 'Guyane', 'La Réunion', 'Mayotte',
       'Centre-Val de Loire', 'Normandie', 'Pays de la Loire', 'Bretagne',
       'Occitanie', "Provence-Alpes-Côte d'Azur", 'Corse']

def getValue(_val):
  try:
    myval = _val.replace('Â', '').replace('°', '').replace('%', '').replace('km/h', '').replace('mm', '').replace('km', '')
    return myval
  except:
    return np.nan

def getSunTimeInSec(_val):
  try:
    vals = _val.split(':')
    return int(vals[2]) + int(vals[1]) * 60 +  int(vals[0]) * 60 * 60
  except:
    return np.nan

# Return the text value from an XPath
def getValueFromXPath(doc, _xpath):
  try:
    value = doc.xpath(_xpath)
    myval = value[0].text_content().strip()
    return myval
  except:
    return np.nan

# Get the XPath infor for the XPath reference
def getXPath(_rowidx = 1, _colidx = 4):
  return '//*[@id="content"]/div/div/div[1]/table/tbody/tr['+  str(_rowidx) + ']/td['+  str(_colidx) + ']'

# Get one feature into the web page by XPath search
def getOneMeteoFeature(_doc, _table, _feature):
  featureValue = ""
  row = 1
  endOfTable = False
  while (not endOfTable):
    label = getValueFromXPath(_doc, getXPath(row, 1))
    if (label == _feature):
      featureValue = getValueFromXPath(_doc, getXPath(row, 4) + '/b')
      break
    row = row + 1
    if ((row > len(labels)+2) or (label == 'Error')): endOfTable = True
  return featureValue

# Return the meteo data for 1 day / 1 region
def get1RegionMeteoByDay(_region, _day):
    url = urlbase + '/' + _region + '/' + _day
    #print ("Get data from: ", url)
    page = requests.get(url)
    doc = lh.fromstring(page.content)
    table = 2
    index = _region + "_" + _day
    dataset = pd.DataFrame(columns=labels, index=[index])
    # Loop with all the required labels to grab their data
    for label in labels:
        val = getOneMeteoFeature(doc, table, label)
        dataset[label][index] = getValue(val)
    dataset['region'] = _region
    issue=dataset.to_numpy().tolist()
    
    return issue

# Return the meteo data for 1 day for all region
# _day : day to retrieve meteo (format YYYY/MM/DD)
def getAllRegionByDay(_day):
  all_day_dataset = pd.DataFrame()
  print (f"Grab Meteo Data for {_day}")
  
  # Loop through all regions and get their meteo data per day
  for region in regions:
    #print (".", end='')
    try:
        dataframe_region = get1RegionMeteoByDay(region, _day)
        all_day_dataset = pd.concat([all_day_dataset, dataframe_region])
    except:
        print(f'Error while retreiving data for {region}, day {_day} | ', sys.exc_info()[0])    
    
  # reformat dataset columns names
  all_day_dataset.columns = ['TempMax_Deg',
                            'TempMin_Deg',
                            'Wind_kmh',
                            'Wet_percent',
                            'Visibility_km',
                            'CloudCoverage_percent',
                            'Dayduration_hour',
                            'region']
  all_day_dataset['day'] = _day
  return all_day_dataset

def GetMeteoData(_start, _End, _Folder):
    ds = pd.DataFrame()
    end_of_loop = False
    
    # Convert in datetime
    start = datetime.strptime(_start, "%Y/%m/%d")
    end = datetime.strptime(_End, "%Y/%m/%d")
    filename = "MeteoFR_" + _start.replace('/', '-') + "_" + _End.replace('/', '-') + ".csv"
    
    # Loop from start date to end
    while (start <= end):
        ds_one_day = getAllRegionByDay(start.strftime("%Y/%m/%d"))
        ds = pd.concat([ds, ds_one_day])
        start = start + timedelta(days=1)
    
    return filename, ds

# return the number of minutes in a time
def convTimeInMinute(_time):
  time = datetime.strptime(str(_time), "%H:%M:%S")
  return float(time.hour * 60 + time.minute)

# convert float and replace no numerical data by nan
# take care to convert by using locale (point or comma)
def defaultFloat(val):
    if str(val).isnumeric():
        return float(val.replace(".", locale.localconv()['decimal_point']))
    else:
        print ("> Error while converting " + str(val))
        return np.nan

# Convert Data to new regions
def convertRegionData(dataset):
    print ("Convert French Region with new ones")
    print ("convertRegionData> Columns to convert:", dataset.columns)
    
    # Effectively do the region mapping
    dataset['region'] = dataset['region'].map({'ile-de-france' : 'Île-de-France',
                                                     'limousin' : 'Nouvelle-Aquitaine',
                                                     'aquitaine' : 'Nouvelle-Aquitaine',
                                                     'poitou-charentes' : 'Nouvelle-Aquitaine',
                                                     '' : 'Auvergne-Rhône-Alpes',
                                                     'bourgogne' : 'Bourgogne-Franche-Comté',
                                                     'franche-comte' : 'Bourgogne-Franche-Comté',
                                                     'nord-pas-de-calais' : 'Hauts-de-France',
                                                     'picardie' : 'Hauts-de-France',
                                                     'alsace' : 'Grand Est',
                                                     'lorraine' : 'Grand Est',
                                                     '--' : 'Guadeloupe',
                                                     '--' : 'Martinique',
                                                     '--' : 'Guyane',
                                                     '--' : 'La Réunion',
                                                     '--' : 'Mayotte',
                                                     'centre' : 'Centre-Val de Loire',
                                                     'normandie' : 'Normandie',
                                                     'pays-de-la-loire' : 'Pays de la Loire',
                                                     'bretagne' : 'Bretagne',
                                                     'midi-pyrenees' : 'Occitanie',
                                                     'languedoc-roussillon' : 'Occitanie',
                                                     'provence-alpes-c-te-d-azur' : "Provence-Alpes-Côte d'Azur",
                                                     'corse' : 'Corse'
                                                    })
    
    print ("convertRegionData> Convert float data")
    # Convert in float to be able to group by
    ColumlToFloatConvert = ['TempMax_Deg',
                            'TempMin_Deg',
                            'Wind_kmh',
                            'Wet_percent',
                            'Visibility_km',
                            'CloudCoverage_percent']
    #for label in ColumlToFloatConvert:
    #    dataset[label] = [ defaultFloat(val) for val in dataset[label] ]
        #dataset[label] = dataset[label].astype(float, errors='ignore')
    
    print ("convertRegionData> Data converted in float")
    dataset['Dayduration_Min'] = dataset['Dayduration_hour'].apply(convTimeInMinute)
    
    print ("convertRegionData> Dayduration_Min converted in minutes, new columns set: ", dataset.columns)
    # Now need to group the identical days (coming from the same region) to ensure no duplicates
    dataset = dataset.groupby(['region', 'day'], dropna=True).mean()
    
    print ("convertRegionData> Columns converted after grouping:", dataset.columns)
    
    return dataset

# Launch data gathering
def collectMeteoData(_starDate, _endDate, _targetFolder):
    print (f"Starting Date: <{_starDate}>")
    print (f"End Date Date: <{_endDate}>")
    print (f"Target Folder: <{_targetFolder}>")
    
    # Launch Meteo gathering
    try:
        filename, ds = GetMeteoData(_starDate, _endDate, _targetFolder)
        print (f"Store results in {_targetFolder + filename}")
        ds.to_csv(_targetFolder + "oldReg_" + filename)
    except:
        print("> Error while gathering meteo data. Error raised: ", sys.exc_info()[0])
        
# convert in new FR region
def convertMeteoDataInNewFRRegions(_sourcefile, _targetfile):
    print (f"Source file: <{_sourcefile}>")
    print (f"Target File: <{_targetfile}>")
    
    #try:
    dataset = pd.read_csv(_sourcefile)
    dataset_result = convertRegionData(dataset)
    dataset_result.to_csv(_targetfile)
    #except:
    #    print("> Impossible to convert Meteo data into new French Region. Error raised: ", sys.exc_info()[0])

def usage():
    print ('Meteo Gathering Usage is GetFRMeteoData.py -a collect -s <Start Date> -e <End Date> -f <Target Folder>')
    print ('Meteo Fr New Region conversion Usage is GetFRMeteoData.py -a convert -i <input file> -o <output file>')
    
# Main function
def main():
    # Manage arguments
    starDate, endDate, targetFolder, inFile, outFile = '', '', '', '', ''
    action = "collect" # by default collect data
    
    try:
        argv = sys.argv[1:]
        opts, args = getopt.getopt(argv , "a:s:e:f:i:o:h")
    except getopt.GetoptError:
        usage()
        sys.exit(2)
        
    for opt, arg in opts:
        if opt == '-h':
            usage()
            return
        elif opt in ["-a"]:
            action = arg.strip()
        elif opt in ["-s"]:
            starDate = arg.strip()
        elif opt in ["-e"]:
            endDate = arg.strip()
        elif opt in ["-f"]:
            targetFolder = arg.strip()
        elif opt in ["-i"]:
            inFile = arg.strip()
        elif opt in ["-o"]:
            outFile = arg.strip()
            
    print (f"Action to launch: <{action}>")
    if (action.capitalize() == "collect".capitalize()):
        collectMeteoData(starDate, endDate, targetFolder)
        
    elif (action.capitalize() == "convert".capitalize()):
        convertMeteoDataInNewFRRegions(inFile, outFile)
    

if __name__ == "__main__":
    main()

def encodage():
    import sqlite3
    bd=sqlite3.connect('tipe.db')
    curseur=bd.cursor()
    curseur.execute("""SELECT * FROM DFCI_2x2_v2 JOIN
    (liste_incendies_du_18_12_2021_blank2 JOIN departement ON SUBSTR(Departement,1,3)=code_departement) ON SUBSTR(code_DFCI,1,6)=numb
    WHERE liste_incendies_du_18_12_2021_blank2.Surface_parcourue_m2>70650 AND liste_incendies_du_18_12_2021_blank2.Annee>2009;""")
    data=curseur.fetchall()
    bd.close()

    record = {'pday':[],
                            'pTempMax_Deg':[],
                            'pTempMin_Deg':[],
                            'pWind_kmh':[],
                            'pWet_percent':[],
                            'pVisibility_km':[],
                            'pCloudCoverage_percent':[],
                            'pDayduration_hour':[],
                            'pregion':[],
                           'pTempMax_Deg_1':[],
                            'pTempMin_Deg_1':[],
                            'pWind_kmh_1':[],
                            'pWet_percent_1':[],
                            'pVisibility_km_1':[],
                            'pCloudCoverage_percent_1':[],
                            'pDayduration_hour_1':[],
                       }

    for a in data:
        Date = a[-7][0:10]
        region_fct = a[-1]
        date_fct = Date.replace('-','/')
        rd = get1RegionMeteoByDay(region_fct, date_fct)
        record['pday'].append(Date)
        record['pTempMax_Deg'].append(rd[0][0])
        record['pTempMin_Deg'].append(rd[0][1])
        record['pWind_kmh'].append(rd[0][2])
        record['pWet_percent'].append(rd[0][3])
        record['pVisibility_km'].append(rd[0][4])
        record['pCloudCoverage_percent'].append(rd[0][5])
        record['pDayduration_hour'].append(rd[0][6])
        record['pregion'].append(rd[0][7])

        date_fct_1 = date_fct[:9]+ str(int(date_fct[9:11])-1)
        rd1 = get1RegionMeteoByDay(region_fct, date_fct_1)
        record['pTempMax_Deg_1'].append(rd[0][0])
        record['pTempMin_Deg_1'].append(rd[0][1])
        record['pWind_kmh_1'].append(rd[0][2])
        record['pWet_percent_1'].append(rd[0][3])
        record['pVisibility_km_1'].append(rd[0][4])
        record['pCloudCoverage_percent_1'].append(rd[0][5])
        record['pDayduration_hour_1'].append(rd[0][6])


    df = pd.DataFrame.from_dict(record, orient='columns')
    df.to_csv('weather_conditions')
        
