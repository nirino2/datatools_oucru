import requests
import pandas as pd

# print('HTTP Status: ' + str(r.status_code))
# print(r.text)
def e_metadata(apilink,apikey):
    fields = {
        'token': apikey,
        'content': 'metadata',
        'format': 'json'
    }
    r = requests.post(apilink,data=fields)
    return r

def e_instrument(apilink,apikey):
    fields = {
        'token': apikey,
        'content': 'instrument',
        'format': 'json'
    }
    r = requests.post(apilink,data=fields)
    return r

def e_formEventMapping(apilink,apikey):
    fields = {
        'token': apikey,
        'content': 'formEventMapping',
        'format': 'json'
    }
    r = requests.post(apilink,data=fields)
    return r

def e_repeatingFormsEvents(apilink,apikey):
    fields = {
        'token': apikey,
        'content': 'repeatingFormsEvents',
        'format': 'json'
    }
    r = requests.post(apilink,data=fields)
    return r

def e_version(apilink,apikey):
    fields = {
        'token': apikey,
        'content': 'version'
    }
    r = requests.post(apilink,data=fields)
    return r

def e_project(apilink,apikey):
    fields = {
        'token': apikey,
        'content': 'project',
        'format': 'json'
    }
    r = requests.post(apilink,data=fields)
    return r

def e_event(apilink,apikey):
    fields = {
        'token': apikey,
        'content': 'event',
        'format': 'json',
        'arms': '',
        'returnFormat':'json'
    }
    r = requests.post(apilink,data=fields)
    return r

def e_data(apilink,apikey,dlformat='eav',rawOrLabel='raw'):
    fields = {
        'token': apikey,
        'content': 'record',
        'format': 'json',
        # 'type': 'eav',
        'exportDataAccessGroups': True,
        'exportBlankForGrayFormStatus': True,
        'rawOrLabel':rawOrLabel
    }
    # dlformat = 'flat' (standard table format, 1 row per personevent) 
    # or 'eav' (unstacked, )
    fields['type'] = dlformat
    r = requests.post(apilink,data=fields)
    return r

def e_dag(apilink,apikey):
    fields = {
        'token': apikey,
        'content': 'dag',
        'format': 'json'
    }
    r = requests.post(apilink,data=fields)
    return r

def e_dag_sw(apilink,apikey,dag_to_switch):
    fields = {
        'token': apikey,
        'content': 'dag',
        'action':'switch',
        'dag':dag_to_switch
    }
    r = requests.post(apilink,data=fields)
    return r

def e_cdisc(apilink,apikey):
    fields = {
        'token': apikey,
        'content':'project_xml',
        'exportDataAccessGroups':True,
        }
    r = requests.post(apilink,data=fields)
    return r