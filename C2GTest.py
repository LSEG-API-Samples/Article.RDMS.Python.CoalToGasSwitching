import json
import pandas as pd
import refinitiv.dataplatform.eikon as ek
import rdms_gas as rdms
import itertools
import statsmodels.api as sm

with open('AccessKeys.txt') as access_keys_file:
    keys_dict = json.load(access_keys_file)
eikon_app_key = keys_dict['EIKON_APP_KEY']
ek.set_app_key(eikon_app_key)

def RegionalC2GTest(BA_names,FixRICs,spotRICs,n,spotNames=0,shiftday=0,isodata = 0,pricedata = 0,exclusion_dates = 0):
    if spotNames == 0:
        spotNames = spotRICs
    if type(isodata) == int:
        eia930_ids = pd.read_csv('EIA930_curves.csv',index_col= 0);
        ba_ids = eia930_ids.loc[BA_names].dropna().astype(int)
        df = rdms.getTimeSeriesMatrix(ba_ids,ba_ids.index)
        df = df.resample('D').mean()
        df['Ratio'] = df['Natural gas']/df['Coal']
        isodata = df
    else:
        df = isodata
    if type(pricedata) == int:
        startdate = df.index[0].strftime("%Y-%m-%d")
        enddate = df.index[-1].strftime("%Y-%m-%d")
        RICs = FixRICs + spotRICs
        price_df = getRICData(RICs,startdate,enddate)
        price_df.columns = FixRICs + spotNames
        price_df[spotNames] = price_df[spotNames].shift(shiftday)
        price_df = price_df.fillna(method = 'ffill')
        price_df = price_df.tz_localize('UTC', copy=False)
    else:
        price_df = pricedata
    df = df.merge(price_df, left_index=True, right_index=True)
    if type(exclusion_dates) != int:
        df = df.loc[~df.index.isin(exclusion_dates)]
    df= df.dropna().astype(float);
    X = df.drop(['Coal','Natural gas','Other','Hydro','Solar','Ratio'],axis = 1)
    if 'Petroleum' in list(df.columns):
        X = X.drop(['Petroleum'],axis = 1)
    y = df['Ratio']
    select = list(itertools.combinations(list(range(1,len(spotRICs)+1)),n))
    pricepairs = dict()
    for i in select:
        X = sm.add_constant(X)
        sel = [-j for j in list(i)]
        est = sm.OLS(y,X.iloc[:,list(range(len(X.columns)-len(spotRICs)))+ sel])
        est2 = est.fit()
        pricepairs[tuple([X.columns[k] for k in sel])] = est2.rsquared_adj
    sorted_pricepairs = sorted(pricepairs.items(), key=lambda kv: -kv[1])
    df_result = pd.DataFrame.from_dict(sorted_pricepairs)
    df_result.columns = ['Selected Price','Rsq']
    return df_result.set_index('Selected Price'),isodata,price_df  
                          
def getRICData(RICs,startdate,enddate):
    curve_data = list(map(lambda x: ek.get_timeseries(x,'Close',startdate,enddate,'daily'),RICs))
    for idx, sub_df in enumerate(curve_data):
        sub_df.columns = [RICs[idx]]
    return pd.concat(curve_data, axis=1)