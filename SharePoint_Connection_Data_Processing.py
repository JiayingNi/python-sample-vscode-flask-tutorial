#!/usr/bin/env python
# coding: utf-8

# In[49]:


# tool bag import

# import sys, win32com.client
# import win32api,win32gui,win32con,win32ui,time,os,subprocess
# import win32com.client, subprocess
# import time
import datetime
import pandas as pd
import numpy as np
# import pyperclip
# import pymssql
# from tabulate import tabulate
import requests
import json
import os
# import ssl
import pandas as pd
# import urllib

# create blank month_file folder
now_time = datetime.datetime.now()
# now_time = datetime.datetime(2022, 12, 15, 10, 25, 20, 454992)

# for the time gap on server
# time_gap = datetime.timedelta(hours=8)
# now_time = now_time + time_gap

# for test
'''
file_time = '20221215'
month_file = '202212'
'''
file_time = now_time.strftime('%Y%m%d')
month_file = now_time.strftime('%Y%m')

hour = now_time.hour
minute = now_time.minute
sec = now_time.second
region = 'LAA'

# SharePoint Connection, getFile and uploadFile
client_id = 'bce0d6c6-6d51-48b2-afe4-1592cfd783db'
client_secret = 'm5oyqgNx9T05I/IgdTM1AKp6E4adXO0fGxolsqeuTsI='
tenant =  'workspaces' 
tenant_id = 'c3e32f53-cb7f-4809-968d-1cc4ccc785fe'  
client_id = client_id + '@' + tenant_id

data = {
    'grant_type':'client_credentials',
    'resource': "00000003-0000-0ff1-ce00-000000000000/" + tenant + ".bsnconnect.com@" + tenant_id, 
    'client_id': client_id,
    'client_secret': client_secret
}

headers = {
    'Content-Type':'application/x-www-form-urlencoded'
}

url = "https://accounts.accesscontrol.windows.net/c3e32f53-cb7f-4809-968d-1cc4ccc785fe/tokens/OAuth/2"
r = requests.post(url, data=data, headers=headers)
json_data = json.loads(r.text)

headers = {
    'Authorization': "Bearer " + json_data['access_token'],
    'Accept':'application/json;odata=verbose',
    'Content-Type': 'application/json;odata=verbose'
}

site_url= "workspaces.bsnconnect.com/teams/DCS_Global_BOP_Process_Management_Teams"

# definitions for get folder, get the latest folder, get file.xlsx, get file.txt, upload_file
def getFolder(get_folder):
    uploadUrl = f"https://{site_url}/_api/web/GetFolderByServerRelativeUrl('/teams/DCS_Global_BOP_Process_Management_Teams/Shared Documents/General/{get_folder}')/Files"
    headers = {"Authorization":"Bearer " + json_data['access_token'],"Accept": "application/json;odata=verbose"
    }
    r = requests.get(uploadUrl,headers=headers, verify = False)
    l = json.loads(r.text)["d"]["results"]
    get_folder_list =[]
    for file in l:
        get_folder_list.append(file["Name"])
    return get_folder_list

def getLatestFolderName(get_folder,today):
    uploadUrl = f"https://{site_url}/_api/web/GetFolderByServerRelativeUrl('/teams/DCS_Global_BOP_Process_Management_Teams/Shared Documents/General/{get_folder}')/Folders"
    headers = {"Authorization":"Bearer " + json_data['access_token'],"Accept": "application/json;odata=verbose"
    }
    r = requests.get(uploadUrl,headers=headers, verify = False)
    l = json.loads(r.text)["d"]["results"]
    get_folder_list =[]
    for folder in l:
        get_folder_list.append(folder["Name"])
    for folder in get_folder_list:
        if folder.find(today)>-1:
            return folder
    raise Exception("can't find today's folder")

def getFile(get_folder,get_filename):
    result = {"status":1,"content":None}
    try:
        getFolderUrl = f"https://{site_url}/_api/web/GetFileByServerRelativeUrl('/teams/DCS_Global_BOP_Process_Management_Teams/Shared Documents/General/{get_folder}/{get_filename}')/$value"
        r = requests.get(getFolderUrl, headers=headers, verify = False)
        result["content"] = r.content
    except Exception:
        result["status"] = -1
        result["content"] = "no file"
    return result

def getTxt(get_folder,get_txt):
    result = {"status":1,"content":None}
    try:
        getFolderUrl = f"https://{site_url}/_api/web/GetFileByServerRelativeUrl('/teams/DCS_Global_BOP_Process_Management_Teams/Shared Documents/General/{get_folder}/{get_txt}')/$value"
        r = requests.get(getFolderUrl, headers=headers, verify = False)
        result["content"] = r.text
    except Exception:
        result["status"] = -1
        result["content"] = "no file"
    if result["status"] == 1:
        with open("./temp.txt","w+") as f:
            f.write(result["content"])
        file_get = pd.read_csv("./temp.txt",header=None,sep = '\t')
    return file_get
    
def uploadFile(up_folder,up_filename,up_filepath):
    uploadUrl = f"https://{site_url}/_api/web/GetFolderByServerRelativeUrl('/teams/DCS_Global_BOP_Process_Management_Teams/Shared Documents/General/{up_folder}')/Files/add(url='{up_filename}',overwrite=true)"
    with open(up_filepath,'rb') as f:
        content = f.read()
    headers = {"Authorization":"Bearer " + json_data['access_token'],
        "Content-Length":str(len(content))
    }
    r = requests.post(uploadUrl, data=content, headers=headers, verify = False)

# use dictionary to combine filter type and filter variant
# combine filter variant by region as one
full_variant_list = pd.DataFrame()
f=getFile(f'BOP Management Documents/{region} BOP Variant List',f'{region} BOP Variant List.xlsx')
if f["status"] == 1:
    data = pd.read_excel(f["content"], sheet_name = 'Variant List')
    full_variant_list = full_variant_list.append(data)
full_variant_list.index=range(len(full_variant_list))

CombinedDict = dict(zip(full_variant_list['Filter Variant'],full_variant_list['Filter Type']))# "filter variant" as keys, "filter type" as value
EXEmodeDict = dict(zip(full_variant_list['Filter Variant'],full_variant_list['Execution Mode'])) # "filter variant" as keys, "Execution Mode" as value
PlannerDict = dict(zip(full_variant_list['Filter Variant'],full_variant_list['Email Receipt Name']))
CreatebyDict = dict(zip(full_variant_list['Filter Variant'],full_variant_list['CreatedBy']))
RegionDict = dict(zip(full_variant_list['Filter Variant'],full_variant_list['Region']))
TeamDict = dict(zip(full_variant_list['Filter Variant'],full_variant_list['Team']))
filter_variant = PlannerDict.keys()

# ==============================BOP coding adjust from here=========================
def downloaded_BOP_process(data,region,value_check):
    Raw_Result = data.drop(columns=[0])
    # adjust "*Total" line(s)
    a = len(pd.value_counts(Raw_Result.index))
    if pd.isnull(Raw_Result.loc[a-1,6]) == True:
        Raw_Result = Raw_Result.drop(len(pd.value_counts(Raw_Result.index))-1)
    else:
        Raw_Result = Raw_Result.drop(len(pd.value_counts(Raw_Result.index))-1)
        Raw_Result = Raw_Result.drop(len(pd.value_counts(Raw_Result.index))-1)
    # copy those lines in 1 column and switch column name
    for i in Raw_Result.columns:
        if (Raw_Result.loc[:1,i].notna()).sum()>1:
            Raw_Result.insert(i+1,'copy'+str(i),Raw_Result[i])
            Raw_Result.loc[1,'copy'+str(i)] = Raw_Result.loc[0,i]
            Raw_Result.loc[0,'copy'+str(i)] = Raw_Result.loc[1,i]
        else:
            if pd.isnull(Raw_Result.loc[0,i])==True:
                Raw_Result.loc[0,i] = Raw_Result.loc[1,i] 
            else:
                Raw_Result.loc[1,i] = Raw_Result.loc[0,i]
    for i in Raw_Result.columns:
        if pd.isnull(Raw_Result.loc[0,i]) == True:
            Raw_Result.loc[0,i] = Raw_Result.loc[1,i]
    Raw_Result = Raw_Result.drop(1)
    Raw_Result.columns = Raw_Result.loc[0,:]
    Raw_Result.drop([0], inplace = True)
    # adjust data in "sort item"&"MAD"
    Raw_Result.index = range(len(Raw_Result))
    for i in Raw_Result.index:
        if pd.isnull(Raw_Result.loc[i,'Order']) == True:
            Raw_Result.loc[i,'Sort Item'] = np.nan
    for i in Raw_Result.index:
        if pd.isnull(Raw_Result.loc[i,'  Rqmt Quantity']) == True:
            Raw_Result.loc[i,'MAD'] = np.nan
    # ffill the cell value in header level at 1 step
    need_fill_c = ['Order','Sort Item','Item','Cat','Stat. Aft.','Update','Product','Location','Log.System','Product Short Description','Location Description','       CSR','CSR Email Address','Sales Family']
    Raw_Result[need_fill_c] = Raw_Result[need_fill_c].fillna(method = 'ffill',limit = 1)
    # delete the lines with only header indicator
    for i in Raw_Result.index:
        if pd.isnull(Raw_Result.loc[i,'Order']) == False and pd.isnull(Raw_Result.loc[i,'MAD']) == True:
            Raw_Result.drop([i], inplace = True)

    Raw_Result.index = range(len(pd.value_counts(Raw_Result.index)))
    need_fill_c1 = {'Order','Sort Item','MAD','  Rqmt Quantity','MBUHR','MBTZN'}
    need_fill_c2 = {'MAD New','  Confirmed new','MBUHR New','MBTZN New'}
    need_fill_c3 = {'MBDAT Old','  Confirmed old','MBUHR Old','MBTZN Old'}
    # fill MBDAT in the line with MAD
    for i in list(range(1,len(Raw_Result.index))):
        if pd.isnull(Raw_Result.loc[i-1,'MAD']) == False:
            if pd.isnull(Raw_Result.loc[i,'MAD']) == True:
                if pd.isnull(Raw_Result.loc[i-1,'MBDAT Old']) == True and pd.isnull(Raw_Result.loc[i,'MBDAT Old']) == False:
                    Raw_Result.loc[i-1,need_fill_c3] = Raw_Result.loc[i,need_fill_c3]
                if Raw_Result.loc[i-1,'MAD'] == Raw_Result.loc[i-1,'MBDAT Old']:# scenarioI: MBDAT Old = MAD
                    if pd.isnull(Raw_Result.loc[i,'MAD New']) == True:
                        if pd.isnull(Raw_Result.loc[i-1,'MAD New']) == True:
                            Raw_Result.loc[i-1,need_fill_c2] = 'No Data'
                    else:
                        if pd.isnull(Raw_Result.loc[i-1,'MAD New']) == True:
                            Raw_Result.loc[i-1,need_fill_c2] = Raw_Result.loc[i,need_fill_c2]
            else:
                if pd.isnull(Raw_Result.loc[i-1,'MAD New']) == True:
                    Raw_Result.loc[i-1,need_fill_c2] = 'No Data'
    # scenarioII: MBDAT Old != MAD
    # II-1 MBDAT Old no data
    for i in list(range(1,len(Raw_Result.index))):
        if pd.isnull(Raw_Result.loc[i-1,'MAD']) == False:
            if pd.isnull(Raw_Result.loc[i-1,'MBDAT Old']) == True and pd.isnull(Raw_Result.loc[i,'MBDAT Old']) == True:
                if pd.isnull(Raw_Result.loc[i,'MAD New']) == True:
                    if pd.isnull(Raw_Result.loc[i-1,'MAD New']) == True:
                        Raw_Result.loc[i-1,need_fill_c2] = 'No Data'
                else:
                    if pd.isnull(Raw_Result.loc[i-1,'MAD New']) == True:
                        Raw_Result.loc[i-1,need_fill_c2] = Raw_Result.loc[i,need_fill_c2]
    # nan the MBDAT Old != MAD
    for i in list(range(1,len(Raw_Result.index))):
        if Raw_Result.loc[i-1,'MBDAT Old'] == Raw_Result.loc[i,'MBDAT Old'] and pd.isnull(Raw_Result.loc[i,'MAD']) == True:
            Raw_Result.loc[i,need_fill_c3] = np.nan
    for i in Raw_Result.index:
        if pd.isnull(Raw_Result.loc[i,'MAD']) == True and pd.isnull(Raw_Result.loc[i,'MBDAT Old']) == True and pd.isnull(Raw_Result.loc[i,'MAD New']) == True:
            Raw_Result.drop([i], inplace = True)

    Raw_Result.index = range(len(pd.value_counts(Raw_Result.index)))
    for i in list(range(1,len(Raw_Result.index))):
        if pd.isnull(Raw_Result.loc[i,'MBDAT Old']) == False and pd.isnull(Raw_Result.loc[i,'MAD']) == True:
            Raw_Result.loc[i,need_fill_c1] = Raw_Result.loc[i-1,need_fill_c1]

    for i in list(range(1,len(Raw_Result.index))):
        if pd.isnull(Raw_Result.loc[i-1,'MBDAT Old']) == False and pd.isnull(Raw_Result.loc[i-1,'MAD']) == False:
            if pd.isnull(Raw_Result.loc[i,'Sort Item']) == False:
                if pd.isnull(Raw_Result.loc[i-1,'MAD New']) == True:
                    Raw_Result.loc[i-1,need_fill_c2] = 'No Data'
            else:
                if pd.isnull(Raw_Result.loc[i-1,'MAD New']) == True and pd.isnull(Raw_Result.loc[i,'MAD New']) == False:
                    Raw_Result.loc[i-1,need_fill_c2] = Raw_Result.loc[i,need_fill_c2]

    for i in Raw_Result.index:
        if pd.isnull(Raw_Result.loc[i,'MAD']) == True:
            Raw_Result.drop([i], inplace = True)

    Raw_Result[need_fill_c] = Raw_Result[need_fill_c].fillna(method = 'ffill')
    Raw_Result.loc[:,need_fill_c2] = Raw_Result.loc[:,need_fill_c2].replace('No Data',np.nan)
    # delete unnecessary columns
    Deleted_Columns = ['Sch.','Main Item','Cat','Stat. Aft.','Reqmnt','Perc. Disp','Subloc.','Ver',' DT',' DT',' Qt',' Qt',' PA',' AL',' FC','Log.System','Anchor','Status','Quantity','Date/Time','Quantity','Date/Time','Location Description','Display','Change']
    Raw_Result.drop(Deleted_Columns,axis = 1, inplace = True)

    # design customized columns
    Raw_Result.insert(0,'MAD New-MAD',np.nan)
    Raw_Result.insert(1,'QTY New-QTY',np.nan)
    Raw_Result.index = range(len(pd.value_counts(Raw_Result.index)))
    # calculate gap between MAD NEW and MAD
    Raw_Result.insert(0,'MAD Status',np.nan)
    for j in Raw_Result.index:
        if pd.isnull(Raw_Result.loc[j,'MAD New']) == True:
            Raw_Result.loc[j,'MAD Status'] = 'Not confirmed'
        else:
            Raw_Result.loc[j,'MAD New-MAD'] = (pd.Period(Raw_Result.loc[j,'MAD New'], freq = 'D')-pd.Period(Raw_Result.loc[j,'MAD'], freq = 'D')).n
            if Raw_Result.loc[j,'MAD New-MAD'] < 0:
                Raw_Result.loc[j,'MAD Status'] = 'Fulfil in advance'
            if Raw_Result.loc[j,'MAD New-MAD'] == 0:
                Raw_Result.loc[j,'MAD Status'] = 'Equal to MAD'
            if 0< Raw_Result.loc[j,'MAD New-MAD'] < 7:
                Raw_Result.loc[j,'MAD Status'] = 'Delay < 1 week'
            if Raw_Result.loc[j,'MAD New-MAD'] >= 7:
                Raw_Result.loc[j,'MAD Status'] = 'Delay >= 1 week'
    # calculate gap between MAD NEW and MAD OLD
    Raw_Result.insert(0,'MAD New-MBDAT Old',np.nan)
    for j in Raw_Result.index:
        if pd.isnull(Raw_Result.loc[j,'MAD New']) == True or pd.isnull(Raw_Result.loc[j,'MBDAT Old']) == True:
            Raw_Result.loc[j,'MAD New-MBDAT Old'] = 'No Data'
        else:
            Raw_Result.loc[j,'MAD New-MBDAT Old'] = (pd.Period(Raw_Result.loc[j,'MAD New'], freq = 'D')-pd.Period(Raw_Result.loc[j,'MBDAT Old'], freq = 'D')).n  
    # calculate Qty duration
    Raw_Result.insert(2,'Qty Status',np.nan)
    for j in Raw_Result.index:
        if pd.isnull(Raw_Result.loc[j,'  Confirmed new']) == True:
            Raw_Result.loc[j,'Qty Status'] = 'Not confirmed'
        else:
            Raw_Result.loc[j,'QTY New-QTY'] = int(float((Raw_Result.loc[j,'  Confirmed new'].replace(" ","").replace(',',''))))-int(float((Raw_Result.loc[j,'  Rqmt Quantity'].replace(" ","").replace(',',''))))
            if Raw_Result.loc[j,'QTY New-QTY'] < 0:
                Raw_Result.loc[j,'Qty Status'] = 'Confirmed Qty reduced'
            if Raw_Result.loc[j,'QTY New-QTY'] == 0:
                Raw_Result.loc[j,'Qty Status'] = 'Equal to Reqmt'
            if Raw_Result.loc[j,'QTY New-QTY'] > 0:
                Raw_Result.loc[j,'Qty Status'] = 'Confirmed Qty increased'
    # adjust column order finally
    colNameDict = {'       CSR':'CSR ZE Partner code'}         
    Raw_Result.rename(columns = colNameDict,inplace=True)
    Result = Raw_Result.reindex(columns = ['MAD Status','Order','Item','MAD New','MAD','MBDAT Old','MAD New-MAD','MAD New-MBDAT Old','Sort Item','Update','Product','Product Short Description','Location','Qty Status','  Rqmt Quantity','  Confirmed new','  Confirmed old','QTY New-QTY','BUn','CSR ZE Partner code','CSR Email Address','Sales Family','MBUHR','MBTZN','MBUHR Old','MBTZN Old','MBUHR New','MBTZN New'])
    lstfolder_path = getLatestFolderName(f'BOP Result/{region}/{month_file}',file_time)
    list_file = getFolder(f'BOP Result/{region}/{month_file}/{lstfolder_path}/{file_time}_Raw Data')
    variant = value_check
    variant_name = variant[variant.find('_',variant.find('_',variant.find('_')))+len('_'):variant.find('.txt')]
    now_time = datetime.datetime.now()
    process_time = now_time.strftime('%Y-%m-%d at %H-%M')
    Result.to_excel('./local.xlsx',index=False)
    up_folder = f'BOP Result/{region}/{month_file}/{lstfolder_path}/{file_time}_Raw Data'
    up_filename = f'{variant_name} {process_time} BOP Result.xlsx'
    up_filepath = './local.xlsx'
    uploadFile(up_folder,up_filename,up_filepath)

# multiple case
lstfolder_path = getLatestFolderName(f'BOP Result/{region}/{month_file}',file_time)
list_file = getFolder(f'BOP Result/{region}/{month_file}/{lstfolder_path}/{file_time}_Raw Data')
for i in range(0,len(list_file)):
    txt_check = []
    if list_file[i].endswith('.txt'):
        data = getTxt(f'BOP Result/{region}/{month_file}/{lstfolder_path}/{file_time}_Raw Data',list_file[i])
        if len(data) >= 4:
            try:
                downloaded_BOP_process(data,'LAA',list_file[i])
            except:
                pass
        else:
            pass
    else:
        pass

# integrate orders as a full list
FullList_df = pd.DataFrame()
lstfolder_path = getLatestFolderName(f'BOP Result/{region}/{month_file}',file_time)
list_file = getFolder(f'BOP Result/{region}/{month_file}/{lstfolder_path}/{file_time}_Raw Data')

for i in range(0,len(list_file)):
    if list_file[i].endswith('.xlsx'):
        variant = list_file[i]
        variant = variant[variant.find('_',variant.find('_',variant.find('_')+1))+len('_'):variant.find(' 2')]
        planner = PlannerDict[variant]
        f = getFile(f'BOP Result/{region}/{month_file}/{lstfolder_path}/{file_time}_Raw Data',list_file[i])
        if f["status"] == 1:
            add_data = pd.read_excel(f["content"])
        add_data.to_excel('./local.xlsx')

        # add variant
        add_data['Planner'] = np.nan
        add_data['Planner'] = add_data['Planner'].fillna(planner)
        add_data['Variant'] = np.nan
        add_data['Variant'] = add_data['Variant'].fillna(variant)
        FullList_df = FullList_df.append(add_data, ignore_index = True)
    else:
        pass

# add customer requested latest delivery date
try:
    file_to_process = file_time+" Delivery Date Full List"+".XLSX"
    lstfolder_dlv_path = getLatestFolderName(f'BOP Result/{region}/SO &DLV/{month_file}',file_time)
    f = getFile(f'BOP Result/{region}/SO &DLV/{month_file}/{lstfolder_dlv_path}',file_to_process)
    if f["status"] == 1:
        df = pd.read_excel(f["content"])
    df.insert(0,'KEY',np.nan)
    for i in list(df.index):
        df.loc[i,'KEY'] = str(df.loc[i,'Sales document'])+ str(df.loc[i,'Sales Document Item'])
    refer_dlv = df[['KEY','Latest Customer Requested Delivery Date','Latest Confirmed Delivery Date Cust Req']]

    # add delivery info
    FullList_df['KEY'] = np.nan
    for i in list(FullList_df.index):
        FullList_df.loc[i,'KEY'] = str(FullList_df.loc[i,'Order'])+ str(FullList_df.loc[i,'Item']).strip()
        FullList_df.loc[i,'KEY'].replace(" ","")

    FullList_df = pd.merge(FullList_df, refer_dlv, on = 'KEY', how = 'left')
    # adjust dlv time format
    for i in FullList_df.index:
        if pd.isnull(FullList_df.loc[i,'Latest Customer Requested Delivery Date']) == False:
            FullList_df.loc[i,'Latest Customer Requested Delivery Date'] = datetime.datetime.date(FullList_df.loc[i,'Latest Customer Requested Delivery Date']).strftime('%Y-%m-%d')
            FullList_df.loc[i,'Latest Confirmed Delivery Date Cust Req'] = datetime.datetime.date(FullList_df.loc[i,'Latest Confirmed Delivery Date Cust Req']).strftime('%Y-%m-%d')
    # drop column "KEY"
    Raw_FullList_df = FullList_df.drop('KEY', axis = 1)
    # adjust full list column and DLV related name
    colRenameDict = {'Latest Customer Requested Delivery Date':'Latest CRDD','Latest Confirmed Delivery Date Cust Req':'Latest Confirmed Delivery Date'}         
    Raw_FullList_df.rename(columns = colRenameDict,inplace=True)
    FullList_df = Raw_FullList_df.reindex(columns = ['MAD Status','Order','Item','MAD New','MAD','MBDAT Old','MAD New-MAD','MAD New-MBDAT Old','Latest CRDD','Latest Confirmed Delivery Date','Sort Item','Update','Product','Product Short Description','Location','Qty Status','  Rqmt Quantity','  Confirmed new','  Confirmed old','QTY New-QTY','BUn','CSR ZE Partner code','CSR Email Address','Sales Family','Planner','Variant'])
    # insert time tag
    FullList_df['BOP Date'] = file_time
    FullList_df.to_excel('./local.xlsx',sheet_name = 'Full List', index = False)
    lstfull_path = getLatestFolderName(f'BOP Result/{region}/{month_file}',file_time)
    up_folder = f"BOP Result/{region}/{month_file}/{lstfull_path}"
    up_filename = f'{file_time} Full List.xlsx'
    up_filepath = './local.xlsx'
    uploadFile(up_folder,up_filename,up_filepath)

except:
    pass

# BOP Monitoring Result
# Monitoring 1 - check variant running
f=getFile(f"BOP Management Documents/{region} BOP Variant List",f"{region} BOP Variant List.xlsx")
if f["status"] == 1:
    filter_variant = pd.read_excel(f["content"])
filter_variant.to_excel('./local.xlsx', sheet_name = 'Variant List')
lstfolder_path = getLatestFolderName(f'BOP Result/{region}/{month_file}',file_time)
list_file = getFolder(f'BOP Result/{region}/{month_file}/{lstfolder_path}/{file_time}_Raw Data')
dragged_variant = []
for i in range(0,len(list_file)):
    if list_file[i].endswith('.txt'):
        variant = list_file[i]
        variant_name = variant[variant.find('_',variant.find('_',variant.find('_')+1)+1)+len('_'):variant.find('.txt')]
        dragged_variant.append(variant_name)
# Mon and Thur for all variants, the rest for variants except import team
filter_variant.insert(0,'Dragged Variants','unknown')
if now_time.isoweekday() == 1 or now_time.isoweekday() == 4:
    for i in filter_variant.index:
        if filter_variant.loc[i,'Filter Variant'] in dragged_variant:
            filter_variant.loc[i,'Dragged Variants'] = 'hit'
        else:
            filter_variant.loc[i,'Dragged Variants'] = 'miss'
else:
    filter_variant = filter_variant.drop(filter_variant[(filter_variant.Team == 'Import')].index)
    filter_variant.index = range(len(filter_variant))
    for i in filter_variant.index:
        if filter_variant.loc[i,'Filter Variant'] in dragged_variant:
            filter_variant.loc[i,'Dragged Variants'] = 'hit'
        else:
            filter_variant.loc[i,'Dragged Variants'] = 'miss'
filter_variant.to_excel('./local.xlsx',index=False)

up_folder = f"BOP Monitoring Result/{region}/Variant Check"
up_filename = f'{file_time} variant monitoring result.xlsx'
up_filepath = './local.xlsx'
uploadFile(up_folder,up_filename,up_filepath)

# Monitoring 2 - MAD Old not update in the past 3 workdays
def get3DayPastFolderName(get_folder,last_day):
    uploadUrl = f"https://{site_url}/_api/web/GetFolderByServerRelativeUrl('/teams/DCS_Global_BOP_Process_Management_Teams/Shared Documents/General/{get_folder}')/Folders"
    headers = {"Authorization":"Bearer " + json_data['access_token'],"Accept": "application/json;odata=verbose"
    }
    r = requests.get(uploadUrl,headers=headers, verify = False)
    l = json.loads(r.text)["d"]["results"]
    get_folder_list =[]
    for folder in l:
        get_folder_list.append(folder["Name"])
    for folder in get_folder_list:
        if folder.find(lst_file_time)>-1:
            return folder
try:
    if now_time.isoweekday() == 1 or now_time.isoweekday() == 2 or now_time.isoweekday() == 3:
        lst_file_time = now_time-datetime.timedelta(days = 5)
    else:
        lst_file_time = now_time-datetime.timedelta(days = 3)
    lst_file_time = lst_file_time.strftime('%Y%m%d')
    try:
        lst_file = get3DayPastFolderName(f'BOP Result/{region}/{month_file}',lst_file_time)
        get_folder = f'BOP Result/{region}/{month_file}/{lst_file}'
        get_filename = f'{lst_file_time} Full List.xlsx'
        f = getFile(get_folder,get_filename)
        if f["status"] == 1:
            df_lst = pd.read_excel(f["content"], sheet_name = 'Full List')
    except:
        lst_month_file = datetime.datetime(now_time.year, now_time.month - 1, 1).strftime('%Y%m')
        lst_file = get3DayPastFolderName(f'BOP Result/{region}/{lst_month_file}',lst_file_time)
        get_folder = f'BOP Result/{region}/{month_file}/{lst_file}'
        get_filename = f'{lst_file_time} Full List.xlsx'
        f = getFile(get_folder,get_filename)
        if f["status"] == 1:
            df_lst = pd.read_excel(f["content"], sheet_name = 'Full List')

    # find related reports
    lstfull_path = getLatestFolderName(f'BOP Result/{region}/{month_file}',file_time)
    get_folder = f'BOP Result/{region}/{month_file}/{lstfull_path}'
    get_filename = f'{file_time} Full List.xlsx'
    f = getFile(get_folder,get_filename)
    if f["status"] == 1:
        df_td = pd.read_excel(f["content"], sheet_name = 'Full List')
    df_td['KEY'] = np.nan
    df_lst['KEY'] = np.nan

    # key(MAD+Sort Item+Order+Item+  Rqmt Quantity+variant)
    def Pvlookup(df):
        for i in list(df.index):
            df.loc[i,'KEY'] = str(df.loc[i,'Order'])+ str(df.loc[i,'Item']).strip()+str(df.loc[i,'Variant'])+str(df.loc[i,'  Confirmed old'])
            df.loc[i,'KEY'].replace(" ","")

    Pvlookup(df_td)
    Pvlookup(df_lst)

    td_refer_data = df_td[['KEY','MBDAT Old','MAD New']]
    td_refer_data.loc[:,'MBDAT Old'] = td_refer_data.loc[:,'MBDAT Old'].replace(np.nan,"0")
    Comparison_df = pd.merge(df_lst, td_refer_data, on = 'KEY', how = 'left')
    Comparison_df = Comparison_df.drop_duplicates()
    Comparison_df['Remain'] = np.nan
    for i in Comparison_df.index:
        if pd.isnull(Comparison_df.loc[i,'MBDAT Old_y']) == False:
            Comparison_df.loc[i,'Remain'] = "Y"
    Comparison_df['MBDAT no change'] = np.nan
    for i in Comparison_df.index:
        if Comparison_df.loc[i,'MBDAT Old_x'] == Comparison_df.loc[i,'MBDAT Old_y']:
            Comparison_df.loc[i,'MBDAT no change'] = "True"
        if pd.isnull(Comparison_df.loc[i,'MBDAT Old_x']) == True and Comparison_df.loc[i,'MBDAT Old_y'] == "0":
            Comparison_df.loc[i,'MBDAT no change'] = "True"

    # filter Remain &MBDAT no change part
    for i in Comparison_df.index:
        if Comparison_df.loc[i,'Remain'] != 'Y':
            Comparison_df.drop([i], inplace = True)
    for i in Comparison_df.index:
        if Comparison_df.loc[i,'MBDAT no change'] != "True":
            Comparison_df.drop([i], inplace = True)
    for i in Comparison_df.index:
        if Comparison_df.loc[i,'MAD Status'] == "Equal to MAD":
            Comparison_df.drop([i], inplace = True)

    colRenameDict = {'MAD New_x':f'MAD New in {lst_file_time}','MBDAT Old_x':f'MBDAT Old in {lst_file_time}','MAD New_y':f'MAD New in {file_time}','MBDAT Old_y':f'MBDAT Old in {file_time}'}         
    Comparison_df.rename(columns = colRenameDict,inplace=True)
    Comparison_df.drop('KEY', axis = 1, inplace = True)
    Comparison_df.drop('BOP Date', axis = 1, inplace = True)
    Comparison_df.to_excel('./local.xlsx',index=False)
    up_folder = f"BOP Monitoring Result/{region}/MAD Old not update in the past 3 workdays"
    up_filename = f'{file_time}_MAD Old not update in the past 3 workdays.xlsx'
    up_filepath = './local.xlsx'
    uploadFile(up_folder,up_filename,up_filepath)
except:
    pass

# Monitoring 3 - MAD Old in the past (>3 workdays)
try:
    lstfull_path = getLatestFolderName(f'BOP Result/{region}/{month_file}',file_time)
    get_folder = f'BOP Result/{region}/{month_file}/{lstfull_path}'
    get_filename = f'{file_time} Full List.xlsx'
    f = getFile(get_folder,get_filename)
    if f["status"] == 1:
        df_td = pd.read_excel(f["content"], sheet_name = 'Full List')
    df_td['KEY'] = np.nan
    # key(MAD+Sort Item+Order+Item+  Rqmt Quantity+variant)
    def Pvlookup(df):
        for i in list(df.index):
            df.loc[i,'KEY'] = str(df.loc[i,'Order'])+ str(df.loc[i,'Item']).strip()+str(df.loc[i,'Variant'])+str(df.loc[i,'  Confirmed old'])
            df.loc[i,'KEY'].replace(" ","")

    Pvlookup(df_td)
    MBDATIP_df = df_td.copy()

    if now_time.isoweekday() == 1 or now_time.isoweekday() == 2 or now_time.isoweekday() == 3:
        time_point = now_time-datetime.timedelta(days = 6)
    else:
        time_point = now_time-datetime.timedelta(days = 4)

    time_point = time_point.strftime('%Y%m%d')
    for i in MBDATIP_df.index:
        if pd.isnull(MBDATIP_df.loc[i,'MBDAT Old']) == True:
            MBDATIP_df.drop([i], inplace = True)
    for i in MBDATIP_df.index:
        if MBDATIP_df.loc[i,'Update'] == 'Updated':
            MBDATIP_df.drop([i], inplace = True)
    for i in MBDATIP_df.index:
        formatted_date = MBDATIP_df.loc[i,'MBDAT Old'].split('/')
        formatted_date = str(formatted_date[2])+str(formatted_date[0])+str(formatted_date[1])
        if formatted_date > time_point:
            MBDATIP_df.drop([i], inplace = True)
    MBDATIP_df.drop('KEY', axis = 1, inplace = True)
    MBDATIP_df.to_excel('./local.xlsx',index=False)
    up_folder = f"BOP Monitoring Result/{region}/MAD Old in the past (GT 3 workdays)"
    up_filename = f'{file_time}_MAD Old in the past.xlsx'
    up_filepath = './local.xlsx'
    uploadFile(up_folder,up_filename,up_filepath)
except:
    pass
