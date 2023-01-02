import pandas as pd
import numpy as np
import json
from bs4 import BeautifulSoup

def strchoice_to_json(text):
    lis = text.split("|")
    lis = [l.split(",",1) for l in lis]
    # print(lis)
    lis = {l[0].strip() : l[1].strip() for l in lis}
    return json.dumps(lis)
def strchoice_to_list(text):
    lis = text.split("|")
    lis = [l.split(",",1) for l in lis]
    lis = [[a.strip() for a in l] for l in lis]
    return lis

def process_clires_datadict(df_list):
    df_final = {}
    #Create metadata
    df_final["Metadata"] = pd.DataFrame.from_dict({"key":["SourceType","LocationRawData"],"value":["Excel_Clires","??"]})

    #Copy Events and CRFs
    df_final["Events"] = df_list.get("Events")[["Event","Position","Event name"]].rename(columns={"Event":"EVENTNAME","Position":"POSITION","Event name":"DEFINITION"}).assign(STATUSNAME="??",REPEATED="??")[["EVENTNAME","POSITION","STATUSNAME","DEFINITION","REPEATED"]]
    df_final["CRFs"] = df_list.get("CRFs")[["CRF","Repeated form","Caption"]].rename(columns={"CRF":"FORMNAME","Repeated form":"REPEATED","Caption":"DEFINITION"}).assign(STATUSNAME=lambda df:df["FORMNAME"]+ '_complete')[["FORMNAME","STATUSNAME","DEFINITION","REPEATED"]]

    #Create CRFinEvent
    df_final["CRFinEvent"] = pd.DataFrame.from_dict({"EVENTNAME":["??"],"FORMNAME":["??"],"REPEATED":["??"]})

    dfs_header = ["Events","CRFs","Pages","Grids","Categories"]
    #Merge DataDict, tables not named in header
    df_varkeys = [x for x in df_list.keys() if x not in dfs_header]
    varheader_to_remove = ["USUBJID","STUDYID","SITEID","SUBJID","INITIAL"]
    varheader_df = {"VARNAME":varheader_to_remove + ["EVENT"],
            "DATATYPE":["KEY","META","META","META","META","META"],
            "FORMNAME":[None]*6,
            "DEFINITION":["Unique Subject ID","Study ID","Site ID","Subject ID","Subject Initial","Visit Number"],
            "CATEGORICCODES":[None,None,'{"??":"??"}',None,None,None]}
    toappend_crflist = pd.DataFrame.from_dict({"FORMNAME":[],"STATUSNAME":[],"DEFINITION":[],"REPEATED":[]})
    for idx, srs in df_list.get('CRFs').iterrows():
        ddict = df_list.get(srs['CRF']).assign(FORMNAME=srs['CRF']).rename(columns={"Variable":"VARNAME","Data type":"DATATYPE","Caption":"DEFINITION","Category":"CATEGORICCODES"})
        #Drop Varheader
        ddict = ddict[~ddict["VARNAME"].str.upper().isin(varheader_to_remove)]
        if idx == 0:
            df_list['Vars'] = pd.DataFrame.from_dict(varheader_df)
        #Find _SEQ, reassign to DATATYPE instance
        ddict.loc[ddict["VARNAME"] == srs["CRF"] + "_SEQ","DATATYPE"] = "INSTANCE"
        #Merge Categories
        df_ctg = df_list.get("Categories")
        for idy, srs2 in ddict[ddict['CATEGORICCODES'].notna()].iterrows():
            ctg_list = df_ctg.loc[df_ctg['Category'] == srs2['CATEGORICCODES'],["Submission value", "Caption"]].set_index("Submission value").to_dict().get("Caption")
            ddict.at[idy,"CATEGORICCODES"] = json.dumps(ctg_list, ensure_ascii=False).encode('utf-8-sig').decode()
        #Split Grid
        min_idy = None
        for idy, gridinfo in df_list.get("Grids")[df_list.get("Grids")["CRF"] == srs["CRF"]].iterrows():
            ddict.loc[ddict["Grid"] == gridinfo["Grid"],"FORMNAME"] = "_".join([srs["CRF"],gridinfo["Grid"]])
            #Append new SEQ
            gridseq_df = {"VARNAME":["_".join([srs["CRF"],gridinfo["Grid"],"SEQ"])],
                    "DATATYPE":["INSTANCE"],
                    "FORMNAME":["_".join([srs["CRF"],gridinfo["Grid"]])],
                    "idx":[ddict[ddict["Grid"] == gridinfo["Grid"]].index.min() - 0.5]}
            gridseq_df = pd.DataFrame.from_dict(gridseq_df).set_index("idx")
            #Append inherited SEQ
            oriseq_df = ddict.loc[ddict["VARNAME"] == srs["CRF"] + "_SEQ",:]
            # print(oriseq_df.shape[0])
            if oriseq_df.shape[0] != 0:
                oriseq_df.loc[:,"FORMNAME"] = "_".join([srs["CRF"],gridinfo["Grid"]])
                oriseq_df.loc[:,"idx"] = ddict[ddict["Grid"] == gridinfo["Grid"]].index.min() - 0.5001
                oriseq_df = oriseq_df.set_index("idx")
            ddict = pd.concat([gridseq_df,ddict,oriseq_df]).sort_index()
            #Add Grid to Formlist
            add_crflist_df = {"FORMNAME":["_".join([srs["CRF"],gridinfo["Grid"]])],       "STATUSNAME":["_".join([srs["CRF"],gridinfo["Grid"],"complete"])],
                    "REPEATED":[True],
                    "idx":[idx + 0.001 * idy + 0.001]} 

            toappend_crflist = pd.concat([toappend_crflist,pd.DataFrame.from_dict(add_crflist_df).set_index("idx")]).drop_duplicates()
        
        rows_with_html = ["DEFINITION"]
        ddict[rows_with_html] = ddict[rows_with_html].astype(str).applymap(lambda txt: BeautifulSoup(txt,"lxml").text).replace("nan",np.nan)

        ddict.loc[ddict["DATATYPE"] == "Free Text","DATATYPE"] = "TEXT"
        ddict.loc[ddict["DATATYPE"] == "Category","DATATYPE"] = "CATEGORIC"
        ddict.loc[ddict["DATATYPE"] == "RadioList","DATATYPE"] = "CATEGORIC"
        ddict["Format"] = ddict["Format"].astype("str").str.replace("nan","")
        ddict.loc[(ddict["DATATYPE"] == "DateTime") & (ddict["Format"].str.contains("^(?:[yY].*[dD]|[dD].*[yY])$", na=False)),"DATATYPE"] = "DATE"
        ddict.loc[(ddict["DATATYPE"] == "DateTime") & (ddict["Format"].str.contains("^[hH]+.[mM]", na=False)),"DATATYPE"] = "TIME"
        ddict.loc[(ddict["DATATYPE"] == "DateTime") & (ddict["Format"].str.contains("^(?:[yY].*[dD]|[dD].*[yY]).*[hH]+.[mM]", na=False)),"DATATYPE"] = "DATETIME"
        ddict.loc[ddict["DATATYPE"] == "Check",["DATATYPE","CATEGORICCODES"]] = ["CATEGORIC",'{"1":"Yes","0":"No"}']
        ddict.loc[ddict["DATATYPE"] == "Number","DATATYPE"] = "DOUBLE"

        ddict = ddict.drop(ddict[ddict["DATATYPE"] == "Title"].index)

        ddict = ddict.drop(columns=["Submission value","Prompt"])[["VARNAME","FORMNAME","DATATYPE","Format","DEFINITION","CATEGORICCODES","Grid"]]

        df_list['Vars'] = pd.concat([df_list['Vars'],ddict])
    df_final['Vars'] = df_list['Vars']
    df_final["CRFs"] = pd.concat([df_final.get("CRFs"),toappend_crflist]).sort_index().astype({"REPEATED":"bool"})
    return df_final
    df_list.get('Vars').to_csv(output,index=False, encoding="utf-8-sig")