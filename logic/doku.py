import pandas as pd
import numpy as np
import datetime as dt
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

dfs = []


def reconcile_data(file1_paths, file2_path):
    for file_path in file1_paths:
        if file_path.endswith('.csv'):
            
            df = pd.read_csv(file_path,  dtype = {'Recon Code' : 'str', 'Invoice Number' : 'str'}, skiprows = 2)
        elif file_path.endswith('.xlsx'):
            
            df = pd.read_excel(file_path, dtype = {'Recon Code' : 'str', 'Invoice Number' : 'str'}, skiprows = 2)
        else:
            
            continue
        
        dfs.append(df)
    
    
    if dfs:
        dash = pd.concat(dfs, ignore_index=True)
    else:
        raise ValueError("No valid files found in Source Data 1.")
    
    gds = pd.read_csv(file2_path[0], dtype = {'va_number' : 'str'}) if file2_path[0].endswith('.csv') else pd.read_excel(file2_path[0], dtype = {'va_number' : 'str'})

    dash['Total Amount'] = dash['Total Amount'].str.replace(',','')
    dash['Total Amount'] = dash['Total Amount'].astype(str).astype(float)

    dash['Total Fee'] = dash['Total Fee'].str.replace(',','')
    dash['Total Fee'] = dash['Total Fee'].astype(str).astype(float)

    dash['Net Amount'] = dash['Net Amount'].str.replace(',','')
    dash['Net Amount'] = dash['Net Amount'].astype(str).astype(float)

    dashraw = dash.copy()
    gdsraw = gds.copy()

    gds = gds.add_suffix('_GDS')
    dash = dash.add_suffix('_DASH')

    reconciled_df = pd.merge(dash,gds, left_on='Invoice Number_DASH', right_on='unique_id_GDS', how='outer', indicator=True)

    reconciled_df['Match?'] = np.where((reconciled_df['Invoice Number_DASH'] == reconciled_df['unique_id_GDS']) & (reconciled_df['Total Amount_DASH'] == reconciled_df['amount_GDS']) , "Recon", "Unrecon")

    realtimesettleindex = reconciled_df[reconciled_df['settlement_time_GDS'].isna()].index

    reconciled_df.loc[realtimesettleindex, 'settlement_time_GDS'] = reconciled_df.loc[realtimesettleindex, 'last_updated_datetime_GDS']

    unrecon = reconciled_df[reconciled_df['Match?'] == 'Unrecon']
    index_unrecon = reconciled_df[reconciled_df['Match?'] == 'Unrecon'].index
    reconciled_df = reconciled_df.drop(index_unrecon)

    summary = reconciled_df.copy()

    summary['last_updated_datetime_GDS'] = pd.to_datetime(summary['last_updated_datetime_GDS'], format='%b %d, %Y, %I:%M:%S %p').dt.date
    summary['settlement_time_GDS'] = pd.to_datetime(summary['settlement_time_GDS'], format='%b %d, %Y, %I:%M:%S %p').dt.date
    summary['transaction_datetime_GDS'] = pd.to_datetime(summary['transaction_datetime_GDS'], format='%b %d, %Y, %I:%M:%S %p').dt.date
    summary['last_updated_datetime_GDS'] = pd.to_datetime(summary['last_updated_datetime_GDS'])
    summary['settlement_time_GDS'] = pd.to_datetime(summary['settlement_time_GDS'])
    summary['transaction_datetime_GDS'] = pd.to_datetime(summary['transaction_datetime_GDS'])

    summary = summary.groupby(['transaction_datetime_GDS', 'last_updated_datetime_GDS', 'settlement_time_GDS', 'username_GDS', 'Acquirer_DASH', 'service_GDS', 'vendor_GDS'], dropna = False).agg({'Invoice Number_DASH':'count','amount_GDS' : 'sum', 'admin_fee_GDS' : 'sum','admin_fee_invoice_GDS' : 'sum', 'Total Fee_DASH' :'sum', 'deduction_cost_GDS' : 'sum', 'settlement_amount_GDS' :'sum' })
    summary.rename(columns = {'Invoice Number_DASH' : "#Trx"}, inplace = True)
    summary = summary.reset_index()


    sheet_dict = {
        "dashboard_raw" : dashraw,
        "gds_raw" : gdsraw,
        "reconciled": reconciled_df,
        "unrecon": unrecon,
        "summary" : summary
       
    }

    return sheet_dict

    