import datatools_oucru.utils as utils
from . import redcap_apimodules
import json
import pandas as pd
import numpy as np
import datetime
from bs4 import BeautifulSoup
import re

def fetch_redcap_all_projectinfo(prjtdb,data_format='eav',rawOrLabel='raw'):
    dictall = {}
    if prjtdb.prjcttype == "REDCap":
        response = redcap_apimodules.e_metadata(prjtdb.apilink,prjtdb.apikey)
        if response.status_code == 200:
            r = json.loads(response.text)     #Results in list of n variables
            df_vars = pd.DataFrame(r)
            # print(dff.columns)
            
    #             ['field_name', 'form_name', 'section_header', 'field_type',
    #    'field_label', 'select_choices_or_calculations', 'field_note',
    #    'text_validation_type_or_show_slider_number', 'text_validation_min',
    #    'text_validation_max', 'identifier', 'branching_logic',
    #    'required_field', 'custom_alignment', 'question_number',
    #    'matrix_group_name', 'matrix_ranking', 'field_annotation']
            dictall["metadata"] = df_vars
        else:
            raise Exception(f"API Error: Status code {response.status_code}" )

        #Project Info      
        # 'project_id', 'project_title', 'creation_time', 'production_time', 'in_production', 'project_language', 'purpose', 'purpose_other', 'project_notes', 'custom_record_label', 'secondary_unique_field', 'is_longitudinal', 'has_repeating_instruments_or_events', 'surveys_enabled', 'scheduling_enabled', 'record_autonumbering_enabled','randomization_enabled', 'ddp_enabled', 'project_irb_number', 'project_grant_number', 'project_pi_firstname', 'project_pi_lastname','display_today_now_button', 'missing_data_codes', 'external_modules','bypass_branching_erase_field_prompt'
        info_project = pd.Series(json.loads(redcap_apimodules.e_project(prjtdb.apilink,prjtdb.apikey).text))
        dictall['info_project'] = info_project
        # DC form_name
        # 'instrument_name', 'instrument_label'
        df_inst = pd.DataFrame(json.loads(redcap_apimodules.e_instrument(prjtdb.apilink,prjtdb.apikey).text))      
        dictall['instrument'] = df_inst         
        if info_project.has_repeating_instruments_or_events == 1:
            # DC Event + VarInEvent Repeated
            # 'event_name', 'form_name', 'custom_form_label'
            df_repeatedforms = pd.DataFrame(json.loads(redcap_apimodules.e_repeatingFormsEvents(prjtdb.apilink,prjtdb.apikey).text))      
            dictall['repeatedforms'] = df_repeatedforms  
        # Version number
        info_redcapver = redcap_apimodules.e_version(prjtdb.apilink,prjtdb.apikey).text 
        dictall['info_ver'] = info_redcapver  
        info_dag = json.loads(redcap_apimodules.e_dag(prjtdb.apilink,prjtdb.apikey).text)
        if type(info_dag) is list:
            dictall['dag'] = pd.DataFrame(info_dag)
        if info_project.is_longitudinal == 1:  
            #Event List 
            # 'event_name', 'arm_num', 'unique_event_name', 'custom_event_label'
            df_event = pd.DataFrame(json.loads(redcap_apimodules.e_event(prjtdb.apilink,prjtdb.apikey).text))
            dictall['event'] = df_event  
            # Instrument Designations
            # 'arm_num', 'unique_event_name', 'form'
            if info_project.has_repeating_instruments_or_events == 1:
                df_forminevent = pd.DataFrame(json.loads(redcap_apimodules.e_formEventMapping(prjtdb.apilink,prjtdb.apikey).text))  
                dictall['forminevent'] = df_forminevent 
        dictall['data'] = pd.DataFrame(json.loads(redcap_apimodules.e_data(prjtdb.apilink,prjtdb.apikey,dlformat=data_format,rawOrLabel=rawOrLabel).text))
        # print(dictall['data'].head(10))
        return dictall
    else:
        print("Invalid Project Type")
        raise


def get_normalized_metadata(redcapdata,data_format):
    
    metadf = {}
    def pull_metainfo(redcapdata,data_format):
        metainfo = {}
        sideinfo = {}
        metainfo['Project Name'] = (redcapdata['info_project'].project_title)
        metainfo['EDC Source'] = 'REDCap'
        metainfo['REDCap Version'] = redcapdata['info_ver']
        metainfo['Longitudinal Project (split to visits)'] = (redcapdata['info_project'].is_longitudinal == 1)
        metainfo['Has Data Access Groups (separate sites)'] = ("dag" in redcapdata)
        metainfo['Data Format'] = data_format
        metainfo['Metadata Retreival Date'] = datetime.datetime.now().strftime("%d-%b-%Y %H:%M:%S")
        sideinfo['Secondary Unique'] = (redcapdata['info_project'].secondary_unique_field)
        return (metainfo, sideinfo)
    
    metainfo, sideinfo = pull_metainfo(redcapdata=redcapdata,data_format=data_format)
    metadf['Metadata'] = pd.Series(metainfo)
    metadf['CRFs'] = redcapdata['instrument'].rename(columns={"instrument_name":"FORMNAME","instrument_label":"DEFINITION"}).assign(STATUSNAME=lambda df: df["FORMNAME"] + "_complete")
    #MISSING - repeated form if non-longitudinal
    if "event" in redcapdata:
        metadf['Events'] = redcapdata['event'][["event_name","unique_event_name"]].rename(columns={"unique_event_name":"EVENTNAME","event_name":"DEFINITION"})
        metadf['CRFinEvent'] = redcapdata['forminevent'].rename(columns={"form":"FORMNAME","unique_event_name":"EVENTNAME"})
        if "repeatedforms" in redcapdata:
            metadf['Events']['REPEATED'] = metadf['Events']['EVENTNAME'].isin(redcapdata['repeatedforms'].loc[redcapdata['repeatedforms']['form_name'] == "","event_name"])
            metadf['CRFinEvent']["REPEATED"] = (metadf['CRFinEvent'].index.isin(pd.merge(metadf['CRFinEvent'].reset_index(),redcapdata['repeatedforms'].rename(columns={"form_name":"FORMNAME","event_name":"EVENTNAME"}),how="inner").set_index("index").index.tolist()))
        else:
            metadf['Events']['REPEATED'] = False
            metadf['CRFinEvent']["REPEATED"] = False

    #Soupify =========================================================================================
    df = redcapdata['metadata']
    rows_with_html = ["section_header","field_label","select_choices_or_calculations"]
    df[rows_with_html] = df[rows_with_html].astype(str).applymap(lambda txt: BeautifulSoup(txt,"lxml").text).replace("nan",np.nan)

    #Rename field_types =========================================================================================
    df.loc[(df["field_type"] == "text") & (df["text_validation_type_or_show_slider_number"].isna()),"field_type"] = "TEXT"
    df.loc[(df["field_type"] == "notes"),"field_type"] = "TEXT"
    df.loc[(df["field_type"] == "text") & (df["text_validation_type_or_show_slider_number"] == "integer"),"field_type"] = "INT"
    df.loc[(df["field_type"] == "text") & (df["text_validation_type_or_show_slider_number"] == "number"),"field_type"] = "DOUBLE"
    df.loc[(df["field_type"] == "text") & (df["text_validation_type_or_show_slider_number"] == "date_dmy"),"field_type"] = "DATE"
    df.loc[(df["field_type"] == "text") & (df["text_validation_type_or_show_slider_number"] == "datetime_dmy"),"field_type"] = "DATETIME"
    df.loc[(df["field_type"] == "text") & (df["text_validation_type_or_show_slider_number"] == "datetime_ymd"),"field_type"] = "DATETIME"
    df.loc[(df["field_type"] == "text") & (df["text_validation_type_or_show_slider_number"] == "time"),"field_type"] = "TIME"
    df.loc[(df["field_type"] == "text") & (df["text_validation_type_or_show_slider_number"] == "alpha_only"),"field_type"] = "LETTERS"
    df.loc[(df["field_type"] == "radio"),"field_type"] = "CATEGORIC"
    df.loc[(df["field_type"] == "dropdown"),"field_type"] = "CATEGORIC"
    df.loc[(df["field_type"] == "yesno"),"select_choices_or_calculations"] = "1, Yes | 0, No"
    df.loc[(df["field_type"] == "yesno"),"field_type"] = "CATEGORIC"
    df.loc[(df["field_type"] == "slider"),"text_validation_type_or_show_slider_number"] = np.nan
    df.loc[(df["field_type"] == "slider"),"select_choices_or_calculations"] = np.nan
    df.loc[(df["field_type"] == "slider"),"field_type"] = "DOUBLE"
    df.loc[(df["field_type"] == "calc"),"select_choices_or_calculations"] = np.nan
    df.loc[(df["field_type"] == "calc"),"field_type"] = "DOUBLE"
    # Process Checkboxes =========================================================================================
    df_cbox = df[(df["field_type"] == "checkbox")]
    
    def strchoice_to_list(text):
        lis = text.split("|")
        lis = [l.split(",",1) for l in lis]
        lis = [[a.strip() for a in l] for l in lis]
        return lis
    
    for idx, row in df_cbox.iterrows():
        cbox_options = strchoice_to_list(row["select_choices_or_calculations"])
        dict_orig = {k:[v] * len(cbox_options) for k,v in row.to_dict().items()}
        dict_cbox = {"field_name":["___".join([row["field_name"],l[0].lower()]) for l in cbox_options],
                     "field_type":["CATEGORIC"] * len(cbox_options),
                     "field_label":[" ".join([row["field_label"]," (",l[1],")"]) for l in cbox_options],
                     "select_choices_or_calculations" : ["1, Yes | 0, No"] * len(cbox_options),
                     "matrix_group_name" : [row["field_name"]] * len(cbox_options)}
        dict_orig.update(dict_cbox)
        df_cbox_long = pd.DataFrame(data=dict_orig,columns=df.columns,index=[x/1000 for x in range(idx*1000+1,idx*1000+len(cbox_options)+1)])
        # print(df_cbox_long)
        df = pd.concat([df,df_cbox_long])
        df.drop(index=idx,inplace=True)
    df.sort_index(inplace=True)

    #Add UNUSED column =========================================================================================
    # df["UNUSED"] = (df["field_type"] == "descriptive") & (df["identifier"] == "y")
    df = df.assign(UNUSED       = lambda x: ((x["field_type"] == "descriptive") | (x["identifier"] == "y") |  \
                                            (x["field_annotation"].astype(str).str.find("@CALCTEXT") >= 0) | \
                                            (x["field_annotation"].astype(str).str.find("@HIDDEN") >= 0) | \
                                            (x["field_annotation"].astype(str).str.find("eocru:data:hidden") >= 0) | \
                                            (x["field_name"].astype(str).str.find("_calc") >= 0) | \
                                            (x["field_name"].astype(str).str.find("_text") >= 0)) &
                                            ~(x["field_annotation"].astype(str).str.find("eocru:data:accept") >= 0))
                #    HAS_HIDDEN   = lambda x: (x["field_annotation"].astype(str).str.find("@HIDDEN") >= 0))
    df[["identifier","required_field"]] = df[["identifier","required_field"]].replace({"y":True})

    #Fix header =========================================================================================
    dict_longitudinal_start = {"field_name":["redcap_event_name","redcap_repeat_instrument","redcap_repeat_instance","redcap_data_access_group"],
                            "field_type":["META","META","INSTANCE","META"],
                            "field_label":["Event Name","Repeat form_name","Repeat Form No.","Site Name"],
                            "UNUSED":[False]*4}
    df_longitudinal_start = pd.DataFrame(data=dict_longitudinal_start,columns=df.columns,index=[0.1,0.2,0.3,0.4])
    if "dag" in redcapdata:
        df_longitudinal_start = df_longitudinal_start.drop(index=0.4)
    df = pd.concat([df,df_longitudinal_start]).sort_index()
    df.loc[0,["form_name", "field_type"]] = ["","KEY"]

    #Add form _complete VARNAMEs =========================================================================================
    compl_list = metadf.get("CRFs")["STATUSNAME"].tolist()
    dict_completes = {"field_name":compl_list,
                "form_name":metadf.get("CRFs")["FORMNAME"].tolist(),
                "field_type":["CATEGORIC"]*len(compl_list),
                "select_choices_or_calculations":["0, Incomplete | 1, Unverified | 2, Complete"]*len(compl_list),
                "matrix_group_name":["FormCompletion"]*len(compl_list),
                "UNUSED":[False]*len(compl_list)}
    df = pd.concat([df,pd.DataFrame.from_dict(dict_completes)]).reset_index(drop=True)

    #Change CategoricCodes to JSON format  =========================================================================================
    
    def strchoice_to_json(text):
        lis = text.split("|")
        lis = [l.split(",",1) for l in lis]
        # print(lis)
        lis = {l[0].strip() : l[1].strip() for l in lis}
        return json.dumps(lis)

    df.loc[(df["field_type"] == "CATEGORIC") & (df["select_choices_or_calculations"].notna()),"select_choices_or_calculations"] = df.loc[(df["field_type"] == "CATEGORIC") & (df["select_choices_or_calculations"].notna()),"select_choices_or_calculations"].astype(str).apply(strchoice_to_json)

    #Final Rename and Drop =========================================================================================
    df = df[~(df["field_type"] == "descriptive")]
    df = (df.rename(columns={"field_name":"VARNAME",
            "form_name":"FORMNAME",
            "field_type":"DATATYPE",
            "field_label":"DEFINITION",
            "select_choices_or_calculations":"CATEGORICCODES",
            "identifier":"IDENTIFIER",
            "branching_logic":"BRANCHLOGIC",
            "required_field":"REQUIRED",
            "field_annotation":"NOTES",
            "matrix_group_name":"ANALYSISGROUP"})
            .drop(columns=["section_header","field_note","text_validation_min","text_validation_max","question_number","custom_alignment","text_validation_type_or_show_slider_number","matrix_ranking"]))
    metadf["Vars"] = df
    return metadf

def fetch_cdisc(projectname):
    prjtdb = utils.projectname_decipher(projectname)
    if prjtdb.prjcttype == "REDCap":
        response = redcap_apimodules.e_metadata(prjtdb.apilink,prjtdb.apikey)
        if response.status_code == 200:
            r = response.text
            return r

