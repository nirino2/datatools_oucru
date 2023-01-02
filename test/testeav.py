import datatools_oucru.analysis.eav_data_pull as eavpull
from datatools_oucru.utils.savedict import savetoexcel as savetoexcel
from pandas.api.types import CategoricalDtype
import pandas as pd
import numpy as np
import pathlib
from bs4 import BeautifulSoup
from pprint import pprint

if __name__ == "__main__":
    filepath = pathlib.Path(__file__).parents[2] / "test" / "INVITE OUCRU_eav_17Aug2022_134632" / "origdata.pkl"
    workpath = pathlib.Path(__file__).parents[0]
    rcdf = pd.read_pickle(filepath)
    dc = rcdf["metadata"]
    df = rcdf["data"]
    #Remanage checkbox data
    is_cboxes = dc[dc["field_type"]=="checkbox"]["field_name"].to_list()
    df["cbox"] = df["value"]
    df.loc[~df["field_name"].isin(is_cboxes),"cbox"] = ""
    df.loc[df["field_name"].isin(is_cboxes),"value"] = "Yes"

    #Get Column order
    dc["choices"] = dc["select_choices_or_calculations"]
    dc.loc[dc["field_type"] != "checkbox","choices"] = ""
    def strchoice_to_json(text):
        if text == "": return ""
        lis = text.split("|")
        lis = [l.split(",",1) for l in lis]
        lis = [l[1].strip() for l in lis]   #Choose only the choice labels
        return lis
    dc["choices"] = dc["choices"].apply(lambda txt: BeautifulSoup(txt,"lxml").text).apply(strchoice_to_json)
    dc["Variable Description"] = dc["field_label"].apply(lambda txt: BeautifulSoup(txt,"lxml").text).replace("nan",np.nan)
    col_order = list(dc.set_index("field_name")[["Variable Description","choices"]].explode("choices").reset_index().itertuples(index=False,name=None))
    # print(col_order)

    #Categorize columns
    df["field_name"] = df["field_name"].replace({"record_id":None}).astype(CategoricalDtype(dc["field_name"].to_list(),ordered=True))
    
    df["Variable Description"] = df["field_name"].replace(dc.set_index("field_name")["Variable Description"].to_dict())
    df["redcap_event_name"] = df["redcap_event_name"].astype(CategoricalDtype(rcdf["event"]["event_name"].tolist(),ordered=True))
    df["INVITE ID"] = df["record"].replace(eavpull.get_from_eav(df,"pmi_invite_id_format").to_dict())

    df = df.dropna(subset=["field_name"])
    res = {}
    for name, grp in df.groupby("redcap_event_name"):
        print(name, grp.shape)
        for name2, grp2 in grp.groupby(["redcap_repeat_instrument","redcap_repeat_instance"],dropna=False):
            if name2 == ("",""):
                shtname = name
            else:
                shtname = f"{name}_{name2[0]}_({name2[1]})"
            res[shtname] = grp2.drop(columns=["redcap_event_name"]).pivot("INVITE ID",["field_name","Variable Description","cbox"],"value").sort_index()
            # print(pd.MultiIndex.from_tuples(col_order))
            # pprint(pd.MultiIndex.from_tuples(col_order).intersection(res[shtname].columns).to_list())
            res[shtname] = res[shtname][pd.MultiIndex.from_tuples(col_order).intersection(res[shtname].columns)]
            # print(res[shtname].head())
    # print(res.keys())
    savetoexcel(res,workpath / "testing2.xlsx")
    

