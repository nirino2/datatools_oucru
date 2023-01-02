import pandas as pd
import numpy as np

# TODO: allow taking multiple variables at once
# TODO: add ability to use regex
# TODO: make sure this works with non-longitudinal and non-dag databases
# TODO: check if this is usable on non-REDCap dbs

def get_from_eav(eavfile,fname,eventname = None,repeatinstrument = None, repeatinstance = None,dc=None,filtervalue=None):
    conditions = {}

    cond_true = pd.Series(data={a:True for a in eavfile.index})
    # if fname == "invite_id":
        # print(cond_true.index.to_list())
    conditions[0] = (eavfile.field_name == fname)
    if eventname != None:
        conditions[1] = (eavfile.redcap_event_name == eventname)
    else:
        conditions[1] = cond_true
    if repeatinstrument != None:
        # print(repeatinstrument)
        conditions[2] = (eavfile.redcap_repeat_instrument == repeatinstrument)
    else:
        conditions[2] = cond_true
    if repeatinstance != None:
        conditions[3] = (eavfile.redcap_repeat_instance == repeatinstance)
    else:
        conditions[3] = cond_true
    if filtervalue != None:
        if type(filtervalue) is not list:
            filtervalue = [filtervalue]
        conditions[4] = (eavfile.value.isin(filtervalue))
    else:
        conditions[4] = cond_true


    res = eavfile[conditions[0] & conditions[1] & conditions[2] & conditions[3] & conditions[4]]
    # res2 = res.index.to_list()
    res = res.set_index("record")["value"]
    if res.index.duplicated().any():
        print(f"There is a duplicate index. {fname}")
    if dc is not None:
        datatype = dc.set_index("field_name").loc[fname,"field_type"]
    
    return res

# TODO: Create this fn
def append_to_eav(eavfile,newdata,extrarows={}):
    # Newdata needs to have the SAME indexing method as the original eav data. Columns with None need to be explicitly mentioned
    # Do cursory check that the new var is NOT in the table
    data_to_append = newdata.to_frame("value").astype("string")
    data_to_append["record"] = data_to_append.index
    for k,v in extrarows.items():
        data_to_append[k] = v
    return pd.concat([eavfile,data_to_append],ignore_index=True)

    
def append2_to_eav(eavfile,newdata,field_name,redcap_event_name = None,redcap_repeat_instrument = None,redcap_repeat_instance = None):
    # Wrapper for append_to_eav
    extrarows = {"field_name":field_name}
    if redcap_event_name is not None and redcap_event_name is not np.nan: 
        extrarows.update({"redcap_event_name":redcap_event_name})
    if redcap_repeat_instrument is not None and redcap_repeat_instrument is not np.nan:
        extrarows.update({"redcap_repeat_instrument":redcap_repeat_instrument})
    if redcap_repeat_instance is not None and redcap_repeat_instance is not np.nan:
        extrarows.update({"redcap_repeat_instance":redcap_repeat_instance})
    # print(extrarows)
    return append_to_eav(eavfile,newdata,extrarows)

def create_new_eav():
    cols = ["record","redcap_event_name","redcap_repeat_instrument","redcap_repeat_instance","field_name","value"]
    return pd.DataFrame({a:[] for a in cols})
