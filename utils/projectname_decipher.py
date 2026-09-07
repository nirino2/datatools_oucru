from . import config

class prjobj():
    prjcttype = None
    apikey = None
    apilink = None

def projectname_decipher(projectname):
    details = prjobj()
    # archs = json.load(Path.cwd().parent / "DM Metadata" / "archs.json")
    # edc_choices = archs.get("EDC Service Providers")
    # for prjcts in archs.get("Projects"):
    #     if prjcts["Project Name"] == projectname:
    #         edcs = prjcts.get("EDC")
    if projectname == "SSAT":
        details.prjcttype = "REDCap"
        details.apikey = config.api_key_oucru_ssat
        details.apilink = config.link_api_oucru
    elif projectname == "INVITE OUCRU":
        details.prjcttype = "REDCap"
        details.apikey = config.api_key_oucru_invite
        details.apilink = config.link_api_oucru
    elif projectname == "INVITE OX":
        details.prjcttype = "REDCap"
        details.apikey = config.api_key_oxmedsci_invite
        details.apilink = config.link_api_oxmedsci
    elif projectname == "MetLep":
        details.prjcttype = "REDCap"
        details.apikey = config.api_key_oucru_metlep
        details.apilink = config.link_api_id
    elif projectname == "MetLep SiteInf":
        details.prjcttype = "REDCap"
        details.apikey = config.api_key_oucru_metlep_siteinf
        details.apilink = config.link_api_id
    elif projectname == "INVITE IDTRIAL UAT":
        details.prjcttype = "REDCap"
        details.apikey = config.api_key_idtrial_invite2
        details.apilink = config.link_api_idtrial
    elif projectname == "IBIS REDCap JKT":
        details.prjcttype = "REDCap"
        details.apikey = config.api_key_oucru_ibis
        details.apilink = config.link_api_id
    elif projectname == "INTERACT":
        details.prjcttype = "REDCap"
        details.apikey = config.api_key_oucru_interact
        details.apilink = config.link_api_id
    elif projectname == "Sumba":
        details.prjcttype = "REDCap"
        details.apikey = config.api_key_oucru_sumba
        details.apilink = config.link_api_id
    elif projectname == "IBIS2":
        details.prjcttype = "REDCap"
        details.apikey = config.api_key_oucru_ibis20
        details.apilink = config.link_api_id
    elif projectname == "INTERCEPT":
        details.prjcttype = "REDCap"
        details.apikey = config.api_key_oucru_intercept
        details.apilink = config.link_api_id
    elif projectname == "IMOVA":
        details.prjcttype = "REDCap"
        details.apikey = config.api_key_oucru_imova
        details.apilink = config.link_api_id
    else:
        raise ValueError
    return details