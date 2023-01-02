
import pandas as pd
import numpy as np
import pathlib
import pickle
import json
import utils

class toolbox:
    v = {}
    comp_data_pairs = {}
    def loadfile(self,target,saveto=None,params=None,**kwargs):
        if params[1] == "CompanionData":
            self.v[saveto[1]] = pd.read_excel(utils.fetch_path("Companion",target[1]),sheet_name=None)
            dc = self.v.get(saveto[1])
            mdata = dc.get("Metadata").set_index("key")
            if mdata.at["SourceType","value"] == "CSV_REDCap_long" or mdata.at["SourceType","value"] == "CSV_REDCap_short":
                dtypemap = {"KEY"       :"string",
                            "META"      :"string",
                            "INSTANCE"  :"UInt16",
                            "INT"       :"Int64",
                            # "DATE"      :"datetime64[ns]",
                            "LETTERS"   :"string",
                            "TEXT"      :"string",
                            # "CATEGORIC" :"",
                            "DOUBLE"    :"float64",
                            # "DATETIME"  :"datetime64[ns]",
                            # "TIME"      :"timedelta64[ns]",
                            }
                vardtypes = dc.get("Vars").set_index("VARNAME")["DATATYPE"].map(dtypemap).dropna().to_dict()
                def f(x):
                    return pd.api.types.CategoricalDtype(list(json.loads(x).keys()),ordered=True)
                categvars = dc.get("Vars")[dc.get("Vars")["DATATYPE"] == "CATEGORIC"].set_index("VARNAME")["CATEGORICCODES"].to_dict()
                categvars = {y: f(x) for y,x in categvars.items()}
                vardtypes.update(categvars)

                datevars = dc.get("Vars")[(dc.get("Vars")["DATATYPE"] == "DATE") | (dc.get("Vars")["DATATYPE"] == "DATETIME")]["VARNAME"].to_list()
                timevars = dc.get("Vars")[(dc.get("Vars")["DATATYPE"] == "TIME")]["VARNAME"].to_list()

                df = pd.read_csv(utils.fetch_path("Data",mdata.at["LocationRawData","value"]),dtype=vardtypes,parse_dates=datevars)
                df[timevars] = df[timevars].apply(lambda x: pd.to_timedelta(x + ":00"))
                print(df.info(verbose=True))
                self.v[saveto[2]] = df
            self.comp_data_pairs[saveto[1]] = saveto[2]
        # self.varlist[saveto] = pd.read_excel(target,sheet_name=None)

    def companion_addstatusvars(self,target,saveto=None,params=None,**kwargs):
        df_to_add = {}
        df_len = self.v.get(target[1]).get("CRFs").shape[0]
        # print(df_len)
        df_to_add["VARNAME"] = self.v.get(target[1]).get("CRFs")["STATUSNAME"].to_list()
        df_to_add["DEFINITION"] = ["Completion of " + a for a in self.v.get(target[1]).get("CRFs")["DEFINITION"].to_list()]
        df_to_add["FORMNAME"] = self.v.get(target[1]).get("CRFs")["FORMNAME"].to_list()
        df_to_add["DATATYPE"] = ["CATEGORIC"] * df_len
        df_to_add["CATEGORICCODES"] = ['{"0":"Incomplete","1":"Partially Complete","2":"Complete",None:"Not done"}'] * df_len
        df_to_add["ANALYSISGROUP"] = ['FORMCOMPLETION'] * df_len

        res = pd.DataFrame.from_dict(df_to_add)
        res.index = pd.Index(list(range(-df_len,0)))
        self.v[saveto[1]]["Vars"] = pd.concat([res,self.v.get(target[1]).get("Vars")])
        pass


    def reform(self,target,saveto,params):
        print("Currently data companion reform is not available")
        if params[1] == "CSV_REDCap_long" and params[2] == "Excel_Analysis_Events": 
            dc = self.v.get(target[1])
            dcvars   = dc.get("Vars")
            dkey = dcvars.loc[dcvars["DATATYPE"] == "KEY","VARNAME"].tolist()[0]
            dcforms  = dc.get("CRFs")
            df = self.v.get(target[2])
            dcvars_notincl = dcvars.loc[(dcvars["DATATYPE"] == "descriptive") | (dcvars["IDENTIFIER"] == True),"VARNAME"]
            dcvars2 = dcvars.drop(index=dcvars_notincl.index)
            # a = dcvars2["VARNAME"].tolist()
            # b = dfvars.tolist()
            # print(len([ai for ai in a if ai in b]))
            # print([ai for ai in a if ai not in b])
            # print(len([bi for bi in b if bi in a]))
            # print([bi for bi in b if bi not in a])
            # print(a)
            # print()
            # print(b)

            dc_final = dc.copy()
            dc_final["Metadata"].loc[dc_final["Metadata"]["key"] == "SourceType","value"] = "Excel_Analysis_Events"
            dc_final["Metadata"].loc[dc_final["Metadata"]["key"] == "LocationRawData","value"] = "??"
            df_final = {}
        #Create a table for every non-repeatable event that has at least one non-repeatble form
            non_r_events = dc.get("Events").loc[dc.get("Events")["REPEATED"] != True,"EVENTNAME"].tolist()
            non_r_pairs = dc.get("CRFinEvent")[(dc.get("CRFinEvent")["REPEATED"] != True) & (dc.get("CRFinEvent")["EVENTNAME"].isin(non_r_events))]
            for i in non_r_pairs["EVENTNAME"].unique():
                #Get list of columns
                forms = non_r_pairs.loc[non_r_pairs["EVENTNAME"] == i,"FORMNAME"].tolist()
                varlist = dcvars[dcvars["FORMNAME"].isin(forms)]
                collist = [dkey] + varlist["VARNAME"].tolist()
                #Subset data
                data = df.loc[(df["redcap_event_name"] == i) & (df["redcap_repeat_instrument"].isna()),df.columns.intersection(collist)].rename(columns={"redcap_repeat_instance":"form_instance"}).reset_index(drop=True)
                #Put to final data file
                real_eventname = dc.get("Events").loc[dc.get("Events")["EVENTNAME"] == i,"DEFINITION"].tolist()[0]
                df_final[real_eventname] = data


        #Create a table for every repeatable event
            for _,i in dc.get("Events")[dc.get("Events")["REPEATED"] == True].iterrows():
                #Get list of columns
                forms = dc.get("CRFinEvent").loc[dc.get("CRFinEvent")["EVENTNAME"] == i["EVENTNAME"],"FORMNAME"].tolist()
                varlist = dcvars[dcvars["FORMNAME"].isin(forms)]
                collist = [dkey,"redcap_repeat_instance"] + varlist["VARNAME"].tolist()
                #Subset data
                data = df.loc[df["redcap_event_name"] == i["EVENTNAME"],df.columns.intersection(collist)].rename(columns={"redcap_repeat_instance":"form_instance"}).reset_index(drop=True)
                #Put to final data file
                df_final[i["DEFINITION"]] = data

        #Create a table for every repeatable form in an event
            for _,i in dc.get("CRFinEvent")[dc.get("CRFinEvent")["REPEATED"] == True].iterrows():
                #Get list of columns
                varlist = dcvars[dcvars["FORMNAME"] == i["FORMNAME"]]
                collist = [dkey,"redcap_repeat_instance"] + varlist["VARNAME"].tolist()
                #Subset data
                data = df.loc[(df["redcap_event_name"] == i["EVENTNAME"]) & (df["redcap_repeat_instrument"] == i["FORMNAME"]),df.columns.intersection(collist)].rename(columns={"redcap_repeat_instance":"form_instance"}).reset_index(drop=True)
                #Put to final data file
                real_eventname = dc.get("Events").loc[dc.get("Events")["EVENTNAME"] == i["EVENTNAME"],"DEFINITION"].tolist()[0]
                real_formname = dc.get("CRFs").loc[dc.get("CRFs")["FORMNAME"] == i["FORMNAME"],"DEFINITION"].tolist()[0]
                df_final[real_eventname +"-"+ real_formname] = data

            #Drop unused META vars
            dc_final["Vars"] = dc_final["Vars"][~dc_final["Vars"]["VARNAME"].isin(["redcap_event_name","redcap_repeat_instrument","redcap_repeat_instance"])].reset_index(drop=True)
            #Store final data file
            self.v[saveto[1]] = dc_final
            self.v[saveto[2]] = df_final
        elif params[1] == "CSV_REDCap_short" and params[2] == "Excel_Analysis_Events":
            dc = self.v.get(target[1])
            dcvars   = dc.get("Vars")
            dkey = dcvars.loc[dcvars["DATATYPE"] == "KEY","VARNAME"].tolist()[0]
            dcforms  = dc.get("CRFs")
            df = self.v.get(target[2])
            dcvars_notincl = dcvars.loc[(dcvars["DATATYPE"] == "descriptive") | (dcvars["IDENTIFIER"] == True),"VARNAME"]
            dcvars2 = dcvars.drop(index=dcvars_notincl.index)

            dc_final = dc.copy()
            dc_final["Metadata"].loc[dc_final["Metadata"]["key"] == "SourceType","value"] = "Excel_Analysis_Events"
            dc_final["Metadata"].loc[dc_final["Metadata"]["key"] == "LocationRawData","value"] = "??"
            dc_final["Events"] = pd.DataFrame({"EVENTNAME":["non_repeat","repeat"],"POSITION":[1,2],"STATUSNAME":[np.nan,np.nan],"DEFINITION":["Non-repeating","Repeating"]})
            crf_list = dc.get("CRFs")["FORMNAME"].tolist()
            repeat_list = dc.get("CRFs")["REPEATED"].tolist()
            dc_final["CRFinEvent"] = pd.DataFrame({"EVENTNAME":["repeat" if a else "non_repeat" for a in repeat_list],"FORMNAME":crf_list,"REPEATED":repeat_list})
            dc_final["CRFs"] = dc_final["CRFs"].drop(columns=["REPEATED"])

            df_final = {}
        #Create a table including all non-repeatable event
            forms = dc.get("CRFs").loc[dc.get("CRFs")["REPEATED"] == False,"FORMNAME"].tolist()
            varlist = dcvars[dcvars["FORMNAME"].isin(forms)]
            collist = [dkey] + ["redcap_data_access_group"] + varlist["VARNAME"].tolist()
            #Subset data
            data = df.loc[:,df.columns.intersection(collist)].reset_index(drop=True)
            #Put to final data file
            df_final["Non-repeating"] = data
        #Create a table for every repeatable event
            for _,i in dc.get("CRFs")[dc.get("CRFs")["REPEATED"] == True].iterrows():
                #Get list of columns
                varlist = dcvars[dcvars["FORMNAME"] == i]
                collist = [dkey] + varlist["VARNAME"].tolist()
                #Subset data
                data = df.loc[:,df.columns.intersection(collist)].reset_index(drop=True)
                #Put to final data file
                df_final["Repeating-"+i["DEFINITION"]] = data

            #Store final data file
            self.v[saveto[1]] = dc_final
            self.v[saveto[2]] = df_final
        elif params[1] == "Excel_Clires" and params[2] == "Excel_Analysis_Events":
            pass
        elif params[1] == "Excel_Analysis_Events" and params[2] == "CSV_REDCap_long":
            pass
        else:
            print("Format reform not available, or not recognized")
        
    def savedata(self,target,saveto,params):
        datatype = params[1]
        savetype = params[2]
        if savetype == "Excel":
            with pd.ExcelWriter(utils.fetch_path(datatype,saveto[1])) as writer:
                for df_name, df in self.v.get(target[1]).items():
                    df.to_excel(writer, sheet_name=df_name[:31])
        elif savetype == "Pickle":
            with open(utils.fetch_path(datatype,saveto[1]),"wb") as f:
                pickle.dump(self.v.get(target[1]),f,protocol=pickle.HIGHEST_PROTOCOL)
        else:
            print(f"Data savetype {params[2]} unsupported")
            
    def populatevarmap(self,target,saveto,params):
        dc = self.v.get(target[1])
        pass

    def matchdata2companion(self,target,saveto,params):
        df = self.v.get(target[1])
        dc = self.v.get(saveto[1])
        
        pass
    
    
    def add_vars():
        pass
    def del_vars():
        pass
    