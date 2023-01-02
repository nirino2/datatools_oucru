import pandas as pd

def savetoexcel(dfs,saveto):
    with pd.ExcelWriter(saveto) as writer:
        for df_name, df in dfs.items():
            if isinstance(df,pd.DataFrame) or isinstance(df,pd.Series):
                df.to_excel(writer, sheet_name=df_name[:31])
            elif isinstance(df,dict):
                pd.DataFrame.from_dict(df).to_excel(writer, sheet_name=df_name[:31])
            elif isinstance(df,list) or isinstance(df,set):
                pd.Series(df).to_excel(writer, sheet_name=df_name[:31])
            elif isinstance(df,str) or isinstance(df,int) or isinstance(df,float):
                pd.Series(df).to_excel(writer, sheet_name=df_name[:31])

def savetopickle(dfs,saveto):
    import pickle
    with open(saveto,'wb') as handle:
        pickle.dump(dfs, handle, protocol=pickle.HIGHEST_PROTOCOL)