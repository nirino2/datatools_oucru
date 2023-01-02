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
        if mprd["action"] == "add":
            d = eavpull.get_from_eav(df,mprd["var1"],mprd["event1"],mprd["rep1"],mprd["rrep1"],filtervalue=mprd["value1"])
            if mprd["var1"] == "invite_id":
                d = d.astype("string").str.replace(" ","").str.replace("-","")
            if mprd["var1"] == "record_id":
                d = d.astype("string").str[:4].map({"1662":"(01) RSUD PASAR MINGGU",
                                                    "1663":"(02) RS ST. CAROLOUS",
                                                    "1664":"(03) PUSKESMAS CAKUNG",
                                                    "1665":"(04) PUSKESMAS CIRACAS",
                                                    "1666":"(05) PUSKESMAS DUREN SAWIT",
                                                    })
            if mprd["value2"] == " ":
                d = pd.Series(data={k:"" for k in d.index.to_list()},index=d.index)
                # print(mprd["var1"], d.shape)
                # print(d.head())
            elif mprd["value2"] is not None:
                d = pd.Series(data={k:mprd["value2"] for k in d.index.to_list()},index=d.index,dtype="object")
            res = eavpull.append2_to_eav(res,d,mprd["var2"],mprd["event2"],mprd["rep2"],mprd["rrep2"])
            print(mpr["var1"], d.shape)
        else:
            # d = eavpull.get_from_eav(df,mprd["var1"],mprd["event1"],mprd["rep1"],mprd["rrep1"],filtervalue=mprd["value1"])
            # res2 = eavpull.append2_to_eav(res2,d,mprd["var1"],mprd["event1"],mprd["rep1"],mprd["rrep1"])
            pass
        # print(mprd["var1"], res.shape)
    print(df.shape)
    print(res.shape)
    return res

def uploaddata(remapdf,dagmap,apikey,apilink,addasnew=False,overwriteB="normal"):
    remapdf = remapdf.astype("string").assign(
        h_dag=lambda dx: dx["record"].str.split("-").str[0].map(dagmap),
        h_idx=lambda dx: dx["record"].str.split("-").str[1])
    if addasnew:
        tmp = pd.to_numeric(remapdf["h_idx"]) + 5000
        remapdf["h_idx"] = tmp.astype("string").replace("\.0","",regex=True)
    remapdf["record"] = remapdf["h_dag"] + "-" + remapdf["h_idx"]
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
                f = open(pathlib.Path(__file__).parents[2] / "Data Visualization" / "INVITE Data Transfer" / "log" / f"log_{dti}.txt","w")
                f.write(str(r.status_code))
                f.write(r.text)
                f.close()
            print(datetime.datetime.now())
            print()

if __name__ == "__main__":

    # apikey = "8848B04AE3F34A2DD03F61433E00A3AD"
    # apilink = "https://trial.oucru.id/api/"

    apikey = "D5947BCCD49F2CA1BCD17E3B87B69986"
    apilink = "https://redcap.oucru.org/redcap/api/"

    # ========================================================
    # INVITE OUCRU Data Transfer (simulates original data from OUCRU redcap)
    # ========================================================
    # rcdf = datadict_prep.fetch_raw_data("INVITE OUCRU","eav")
    # dfd = rcdf["data"]
    # dfd2 = deepcopy(dfd)

    # cbox_with_issue = ["eli_ethnicity","eli_comorbidities","covhist_symp_1","covhist_symp_2","covhist_symp_3","covhist_symp_4","covhist_symp_5","covhist_symp_6","exvis_symp","end_death_infosource"]
    # dfd2["field_name_ext"] = dfd2.apply(lambda dx: dx["field_name"] + "___oth" if ((dx["value"] == "OTH") & (dx["field_name"] in cbox_with_issue)) else dx["field_name"],axis=1)
    # dfd2["value_ext"] = dfd2.apply(lambda dx: "1" if ((dx["value"] == "OTH") & (dx["field_name"] in cbox_with_issue)) else dx["value"],axis=1)

    # dfd2["field_name"] = dfd2["field_name_ext"]
    # dfd2 = dfd2.drop(columns="field_name_ext")
    # dfd2["value"] = dfd2["value_ext"]
    # dfd2 = dfd2.drop(columns="value_ext")


    # daglist = {"116":"20",
    #            "115":"21",
    #            "112":"22",
    #            "113":"23",
    #            "114":"24"}
    # uploaddata(dfd2,daglist,apikey,apilink)

    # ========================================================
    # INVITE OUCRU Remap Data Transfer (adds new vaccine dose qns)
    # ========================================================
    # mapperdf = pd.read_excel(pathlib.Path(__file__).parents[2] / "Data Visualization" / "INVITE Data Transfer" / "mapper_fromOUCRU.xlsx",dtype="object")
    # res = remapdata(dfd,mapperdf)
    
    # savedict.savetoexcel({"res":res},pathlib.Path(__file__).parents[2] / "Data Visualization" / "INVITE Data Transfer" / "INVITE_OUCRU_remapped.xlsx")

    # daglist = {"116":"116",
    #            "115":"115",
    #            "112":"112",
    #            "113":"113",
    #            "114":"114"}
    # uploaddata(res,daglist,apikey,apilink)

    # ========================================================
    # INVITE OXFORD Remap Data Transfer (transfers from OXFORD)
    # ========================================================
    rcdf = datadict_prep.fetch_raw_data("INVITE OX","eav")
    dfd = rcdf["data"]
    # mapperdf = pd.read_excel(pathlib.Path(__file__).parents[2] / "Data Visualization" / "INVITE Data Transfer" / "mapper_fromOXFORD.xlsx",dtype="object")
    # res = remapdata(dfd,mapperdf)
    
    # savedict.savetoexcel({"res":res},pathlib.Path(__file__).parents[2] / "Data Visualization" / "INVITE Data Transfer" / "INVITE_OXFORD_remapped.xlsx")

    # daglist = {"1662":"116",
    #            "1663":"115",
    #            "1664":"112",
    #            "1665":"113",
    #            "1666":"114"}
    # uploaddata(res,daglist,apikey,apilink,addasnew=True)

    # ========================================================
    # INVITE OXFORD Remap Data Transfer (transfers from OXFORD)
    # ========================================================
    mapperdf = pd.read_excel(pathlib.Path(__file__).parents[2] / "Data Visualization" / "INVITE Data Transfer" / "mapper_fromOXFORD - dob transfer.xlsx",dtype="object")
    res = remapdata(dfd,mapperdf)
    
    savedict.savetoexcel({"res":res},pathlib.Path(__file__).parents[2] / "Data Visualization" / "INVITE Data Transfer" / "INVITE_OXFORD_remapped_trans.xlsx")

    daglist = {"1662":"116",
               "1663":"115",
               "1664":"112",
               "1665":"113",
               "1666":"114"}
    uploaddata(res,daglist,apikey,apilink,addasnew=True,overwriteB="overwrite")

