import pandas as pd
import pathlib
import logging

def remap(df,remap_vars,remap_values):
    #rename and replace variables with known mapping
    pass

def pivot(df,pivot):
    pass

def add_logic(logic):
    pass

def log_setup(logpath):
    logging.basicConfig(filename=logpath, encoding='utf-8', level=logging.DEBUG,format='%(asctime)s :: %(message)s')

    pass

if __name__ == "__main__":
    excelpath = ""
    excelskiprows = 0
    logpath = pathlib.Path(__file__).parents[0] / "log.txt"
    log_setup(logpath=logpath)
    logging.info("test")
    # excelfile = pd.read_excel(excelpath,skiprows=excelskiprows)
