import requests
import json
import pandas as pd

with open('AccessKeys.txt') as access_keys_file:
    keys_dict = json.load(access_keys_file)
rdms_demo_app_key = keys_dict['RDMS_DEMO_APP_KEY']
headers = {'Authorization' : f'apikey-v1 {rdms_demo_app_key}'}

def getForecast(curveid,ForecastDate):
    res = requests.get('https://demo.rdms.refinitiv.com/api/v1/CurveValues/Forecast/'+ curveid+'/0/'+ ForecastDate,
                      headers=headers, verify=True)
    curve_data = pd.DataFrame.from_dict(res.json())
    curve_data.index = pd.DatetimeIndex(curve_data.valueDate)
    curve_data.drop(columns = ['valueDate'],inplace = True)
    return curve_data
    
def getForecastMatrix(curveids,ForecastDate,curvenames):
    curveids = [str(i) for i in curveids]
    curve_data = list(map(lambda x: getForecast(x,ForecastDate), curveids))
    for idx, sub_df in enumerate(curve_data):
        sub_df.columns = [curvenames[idx]]
    return pd.concat(curve_data, axis=1)
    
def getLatestForecast(curveid):
    res = requests.get('https://demo.rdms.refinitiv.com/api/v1/CurveValues/LatestForecast/'+ curveid+'/0/',
                      headers=headers, verify=True)
    curve_data = pd.DataFrame.from_dict(res.json())
    curve_data.index = pd.DatetimeIndex(curve_data.valueDate)
    curve_data.drop(columns = ['valueDate'],inplace = True)
    return curve_data
    
def getLatestForecastMatrix(curveids,curvenames):
    curveids = [str(i) for i in curveids]
    curve_data = list(map(getLatestForecast, curveids))
    for idx, sub_df in enumerate(curve_data):
        sub_df.columns = [curvenames[idx]]
    return pd.concat(curve_data, axis=1)
    
def getTimeSeries(curveid):
    res = requests.get('https://demo.rdms.refinitiv.com/api/v1/CurveValues/'+ curveid,
                      headers=headers, verify=True)
    curve_data = pd.DataFrame.from_dict(res.json())
    curve_data.index = pd.DatetimeIndex(curve_data.valueDate)
    curve_data.rename(columns={'value':curveid}, inplace=True)
    curve_data.drop(columns = ['scenarioID','forecastDate','valueDate'],inplace = True)
    return curve_data
    
def getTimeSeriesMatrix(curveids,curvenames):
    curveids = [str(i) for i in curveids]
    curve_data = list(map(getTimeSeries, curveids))
    for idx, sub_df in enumerate(curve_data):
        sub_df.columns = [curvenames[idx]]
    curve_data = pd.concat(curve_data,axis = 1)
    return curve_data