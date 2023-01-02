import datatools_oucru.analysis.eav_data_pull as eavpull
import datatools_oucru.utils.savedict as savedict
import datatools_oucru.datadict_prep as datadict_prep
import pandas as pd
import numpy as np
import pathlib
import datetime
import requests
from copy import deepcopy

def remapdata(df,mapdf):
    res = eavpull.create_new_eav()
    # res2 = eavpull.create_new_eav()
    for idx, mpr in mapdf.iterrows():
        mprd = mpr.replace({np.nan:None}).to_dict()
        if mprd["action"] == "add" or mprd["action"] == "move":
            d = eavpull.get_from_eav(df,mprd["var1"],mprd["event1"],mprd["rep1"],mprd["rrep1"],filtervalue=mprd["value1"])
            
            if mprd["value2"] == " ":
                d = pd.Series(data={k:"" for k in d.index.to_list()},index=d.index)
                # print(mprd["var1"], d.shape)
                # print(d.head())
            elif mprd["value2"] is not None:
                d = pd.Series(data={k:mprd["value2"] for k in d.index.to_list()},index=d.index,dtype="object")
            res = eavpull.append2_to_eav(res,d,mprd["var2"],mprd["event2"],mprd["rep2"],mprd["rrep2"])
            # print(mpr["var1"], d.shape)
        if mprd["action"] == "delete" or mprd["action"] == "move":
            d = eavpull.get_from_eav(df,mprd["var1"],mprd["event1"],mprd["rep1"],mprd["rrep1"],filtervalue=mprd["value1"])
            d = pd.Series(data={k:"" for k in d.index.to_list()},index=d.index)
            res = eavpull.append2_to_eav(res,d,mprd["var1"],mprd["event1"],mprd["rep1"],mprd["rrep1"])
            # print(mpr["var1"], d.shape)
        # print(mprd["var1"], res.shape)
    print(df.shape)
    print(res.shape)
    return res

def uploaddata(remapdf,apikey,apilink,dagmap,overwriteB="normal"):
    remapdf = remapdf.astype("string").assign(
        h_dag=lambda dx: dx["record"].str.split("-").str[0].map(dagmap),
        h_idx=lambda dx: dx["record"].str.split("-").str[2])
    # if addasnew:
    #     tmp = pd.to_numeric(remapdf["h_idx"]) + 5000
    #     remapdf["h_idx"] = tmp.astype("string").replace("\.0","",regex=True)
    # remapdf["record"] = remapdf["h_dag"] + "-" + remapdf["h_idx"]
    for dag_name, dfdag in remapdf.sort_values("record").groupby("h_dag"):
        print("DAG: ",dag_name)
        fields = {
            'token': apikey,
            'content': 'dag',
            'action': 'switch',
            'dag': dag_name,
            'returnFormat': 'json'
        }
        r = requests.post(apilink,data=fields)
        print(r.text)

        for dftosend in (dfdag.drop(columns=["h_dag","h_idx"]).iloc[i:i+10000,:] for i in range(0, len(dfdag),10000)):
            print(dftosend.shape)
            fields = {
                'token': apikey,
                'content': 'record',
                'format': 'csv',
                'type': 'eav',
                'forceAutoNumber': False,
                'data': dftosend.to_csv(),
                "overwriteBehavior": overwriteB
            }
            dti = datetime.datetime.now().strftime("%d%m%Y_%H%M%S")
            print(datetime.datetime.now())
            r = requests.post(apilink,data=fields)
            if r.status_code != 200:
                f = open(pathlib.Path(__file__).parents[2] / "Data Visualization" / "MetLep Data Map" / "log" / f"log_{dti}.txt","w")
                f.write(str(r.status_code))
                f.write(r.text)
                f.close()
            print(datetime.datetime.now())
            print()

if __name__ == "__main__":

    apikey = "126000BDCA58639D27B60306EC65C5A2" #actual
    apilink = "https://redcap.oucru.id/api/"

    # apikey = "05A3DEEC381C298B191DE60D3D460E95" #draft
    # apilink = "https://redcap.oucru.id/api/"

    # apikey = "76C04980AE50626FD410BEDA261E56FA"   #trial
    # apilink = "https://redcap.oucru.id/api/"

    # rcdf = datadict_prep.fetch_raw_data("MetLep","eav")
    # dfd = rcdf["data"]

    # savedict.savetoexcel({"origdata":dfd},pathlib.Path(__file__).parents[2] / "Data Visualization" / "MetLep Data Map" / "MetLep_origdata.xlsx")

    # # ========================================================
    # # Remap
    # # ========================================================
    # mapperdf = pd.read_excel(pathlib.Path(__file__).parents[2] / "Data Visualization" / "MetLep Data Map" / "mapper_movetoscreening.xlsx",dtype="object")
    # # "Data Visualization\MetLep Data Map\mapper_movetoscreening.xlsx"
    # # print(dfd.columns)
    # res = remapdata(dfd,mapperdf)

    
    # savedict.savetoexcel({"res":res},pathlib.Path(__file__).parents[2] / "Data Visualization" / "MetLep Data Map" / "MetLep_remapped_movetoscr_final.xlsx")

    # resread = pd.read_excel(pathlib.Path(__file__).parents[2] / "Data Visualization" / "MetLep Data Map" / "MetLep_remapped_movetoscr_final.xlsx", usecols=lambda x: 'Unnamed' not in x)
    # savedict.savetoexcel({"res":resread},pathlib.Path(__file__).parents[2] / "Data Visualization" / "MetLep Data Map" / "MetLep_remapped_cc_final.xlsx")
    resread = pd.read_excel(pathlib.Path(__file__).parents[2] / "Data Visualization" / "MetLep Data Map" / "MetLep_remapped_missing_u_final.xlsx", usecols=lambda x: 'Unnamed' not in x)
    # savedict.savetoexcel({"res":resread},pathlib.Path(__file__).parents[2] / "Data Visualization" / "MetLep Data Map" / "MetLep_remapped_cc_final.xlsx")

    dagmap = {"101":5,"102":4,"103":6}
    uploaddata(resread,apikey,apilink,dagmap,overwriteB="overwrite")

