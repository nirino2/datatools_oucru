import pathlib
import pandas as pd
import numpy as np
import json
from pathlib import Path
import datatools_oucru.utils as utils
from datatools_oucru import getfromredcap as frdcp
from datatools_oucru.analysis.redcap_eav_to_readable import reform_eav_split_visits, reform_eav_to_wide
from datatools_oucru.analysis.eav_data_pull import get_from_eav
import datetime
import os
import re
from copy import deepcopy

def fetch_raw_data(projectname,data_format,with_reformat=False,reformat_id_variable=None):
    prjtdb = utils.projectname_decipher(projectname)
    if prjtdb.prjcttype == "REDCap":
        redcapdata = frdcp.fetch_redcap_all_projectinfo(prjtdb,data_format=data_format,rawOrLabel="label")
        # metadf = frdcp.get_normalized_metadata(redcapdata,data_format)
    elif prjtdb.prjcttype == "CliRes":
        pass
    # redcapdata["data"] = redcapdata["data"][redcapdata["data"].]
    if with_reformat:    
        rcdc = deepcopy(redcapdata)
        if reformat_id_variable != None:
            padlen = get_from_eav(redcapdata["data"],reformat_id_variable).str.len()
            # print(padlen)
            padlen = int(padlen.max())
            rcdc["data"]["record"] = rcdc["data"]["record"].replace(get_from_eav(redcapdata["data"],reformat_id_variable).to_dict()).str.pad(width=padlen,side="left",fillchar="0")

        return redcapdata, reform_eav_split_visits(rcdc), reform_eav_to_wide(rcdc)
    else:
        return redcapdata

def fetch_raw_latest(projectname,direc=None,selection="recent",selectdayslimit=30,data_format='eav'):
    if selection == "recent" or selection == "latest":
        if direc == None:
            direc = pathlib.Path(__file__).parents[1] / "Data Repo" / projectname
        dirlist = [a.name for a in direc.iterdir() if a.is_dir()]
        mtext = f"^{projectname}_(\w+)_(\d\d\w\w\w\d\d\d\d)_\d\d\d\d\d\d"
        matchlist = [re.search(mtext,a) for a in dirlist]
        dirlist = [a.groups() for a in matchlist if a is not None]
        print(dirlist)
    elif selection == "new":
        ct = datetime.datetime.now().strftime("%d%b%Y_%H%M%S")
        dataformat = "eav"
        fname = f"{projectname}_{dataformat}_{ct}"
        if not os.path.exists(utils.fetch_path("test",fname)):
            os.makedirs(utils.fetch_path("test",fname))
        origdata, metadf = fetch_raw_data(projectname,dataformat)
        utils.savetoexcel(origdata,utils.fetch_path("test",f"{fname}\origdata.xlsx"))
        utils.savetoexcel(metadf,utils.fetch_path("test",f"{fname}\metadf.xlsx"))
        utils.savetopickle(origdata,utils.fetch_path("test",f"{fname}\origdata.pkl"))
        utils.savetopickle(metadf,utils.fetch_path("test",f"{fname}\metadf.pkl"))
    return


if __name__ == "__main__":
    pname = "INTERCEPT"
    ct = datetime.datetime.now().strftime("%d%b%Y_%H%M%S")
    dataformat = "eav"
    fname = f"{pname}_{dataformat}_{ct}"
    origdata, reformeddata, widedata = fetch_raw_data(pname,dataformat,with_reformat=True)
    
    if not os.path.exists(utils.fetch_path("test",fname)):
        os.makedirs(utils.fetch_path("test",fname)) 
    utils.savetoexcel(origdata,utils.fetch_path("test",f"{fname}\\origdata.xlsx"))
    utils.savetoexcel(reformeddata,utils.fetch_path("test",f"{fname}\\visdata.xlsx"))
    utils.savetoexcel(widedata,utils.fetch_path("test",f"{fname}\\widedata.xlsx"))
    utils.savetopickle(origdata,utils.fetch_path("test",f"{fname}\\origdata.pkl"))
    utils.savetopickle(reformeddata,utils.fetch_path("test",f"{fname}\\visdata.pkl"))
    utils.savetopickle(widedata,utils.fetch_path("test",f"{fname}\\widedata.pkl"))
