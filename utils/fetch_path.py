import pathlib

def fetch_path(datatype,where):
    if datatype == "Data":
        dataloc = "Data Repo"
    elif datatype == "Companion":
        dataloc = "Data Dictionaries/Processed DataCompanion"
    elif datatype == "Transformer":
        dataloc = "Data Transformation"
    elif datatype == "test":
        dataloc = "test"
    else:
        return None
    return pathlib.Path(__file__).parents[2] / dataloc / where