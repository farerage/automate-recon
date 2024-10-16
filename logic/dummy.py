import pandas as pd
import numpy as np


db_uri = 'postgresql://postgres:fgerry@localhost:5432/dummy'
def reconcile_data(file1_path, file2_path):

    

    df1 = pd.read_csv(file1_path) if file1_path.endswith('.csv') else pd.read_excel(file1_path)
    df2 = pd.read_csv(file2_path) if file2_path.endswith('.csv') else pd.read_excel(file2_path)

    df2 = df2[df2['TransactionStatus'] == "Success" ]
    notsuccess = df2[df2['TransactionStatus'] != "Success" ]

    data_compare = pd.merge(df1, df2, left_on='ID', right_on= 'Reference', how= 'outer', indicator=True)
    data_compare['Match?'] = np.where((data_compare['ID'] == data_compare['Reference']) & (data_compare['Trx Amount'] == data_compare['Amount']), 'Recon', 'Unrecon')

    indexunrecon = data_compare[data_compare['Match?'] == 'Unrecon'].index
    unrecon  = data_compare[data_compare['Match?'] == 'Unrecon']
    data_compare = data_compare.drop(indexunrecon)

    sheet_dict = {
        "Line Per Line": data_compare,
        "Unrecon": unrecon
       
        
    }

    
    return sheet_dict

