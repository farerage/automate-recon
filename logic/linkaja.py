import pandas as pd
import numpy as np
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

def reconcile_data(file1_paths, file2_path):
    # Load the CSV or Excel files into DataFrames
    df1 = pd.read_csv(file1_paths[0]) if file1_paths[0].endswith('.csv') else pd.read_excel(file1_paths[0])
    df2 = pd.read_csv(file2_path[0]) if file2_path[0].endswith('.csv') else pd.read_excel(file2_path[0])

    dashraw = df1.copy()
    gdsraw = df2.copy()
    indexwd = df1[df1['Transaction Type'] == 'Organization Withdraw of Funds with Next Working Day'].index
    wd = df1[df1['Transaction Type'] == 'Organization Withdraw of Funds with Next Working Day']
    df1 = df1.drop(indexwd)
    indexcost = df1[df1['Transaction Scenario'] == 'Physical Merchant Fee 46'].index
    cost = df1[df1['Credit'] == 0.0]
    cost = cost[['Orderid', 'Debit']].copy()
    df1 = df1.drop(indexcost)
    df1 = pd.merge(df1, cost, on ='Orderid', how = 'outer')
    df1 = df1[['Biz Org Name', 'Orderid', 'Trans End Time', 'Transaction Type', 'Transaction Scenario', 'Trans Status',
            'Credit', 'Debit_y']].copy()
    df1.rename(columns = {'Debit_y' : 'Debit'}, inplace = True)
    df1 = df1.add_suffix('_DASH')
    df2 = df2.add_suffix('_GDS')
    
    reconciled_df = pd.merge(df1, df2, left_on = 'Orderid_DASH', right_on = 'tx_serial_number_GDS', how = 'outer', indicator = True )
    reconciled_df['Match?'] = np.where((reconciled_df['Orderid_DASH'] == reconciled_df['tx_serial_number_GDS']) & (reconciled_df['Credit_DASH'] == reconciled_df['amount_GDS']), 'Recon', 'Unrecon')
    
    realtimesettleindex = reconciled_df[reconciled_df['settlement_time_GDS'].isna()].index
    reconciled_df.loc[realtimesettleindex, 'settlement_time_GDS'] = reconciled_df.loc[realtimesettleindex, 'last_updated_datetime_GDS']

    unrecon = reconciled_df[reconciled_df['Match?'] == 'Unrecon']
    indexunrecon = reconciled_df[reconciled_df['Match?'] == 'Unrecon'].index
    reconciled_df = reconciled_df.drop(indexunrecon)

    summary = reconciled_df.copy()
    summary['last_updated_datetime_GDS'] = pd.to_datetime(summary['last_updated_datetime_GDS'], format='%b %d, %Y, %I:%M:%S %p').dt.date
    summary['settlement_time_GDS'] = pd.to_datetime(summary['settlement_time_GDS'], format='%b %d, %Y, %I:%M:%S %p').dt.date
    summary['transaction_datetime_GDS'] = pd.to_datetime(summary['transaction_datetime_GDS'], format='%b %d, %Y, %I:%M:%S %p').dt.date
    summary['last_updated_datetime_GDS'] = pd.to_datetime(summary['last_updated_datetime_GDS'])
    summary['settlement_time_GDS'] = pd.to_datetime(summary['settlement_time_GDS'])
    summary['transaction_datetime_GDS'] = pd.to_datetime(summary['transaction_datetime_GDS'])



    summary = summary.groupby(['last_updated_datetime_GDS', 'transaction_datetime_GDS','settlement_time_GDS', 'username_GDS', 'service_GDS', 'mam_parent_username_GDS', 'mam_child_username_GDS', 'vendor_code_GDS'], dropna = False).agg({'Orderid_DASH':'count','amount_GDS' : 'sum', 'admin_fee_GDS' : 'sum','admin_fee_invoice_GDS' : 'sum', 'Debit_DASH' :'sum', 'deduction_cost_GDS' : 'sum','settlement_amount_GDS' :'sum' })
    summary.rename(columns = {'Orderid_DASH' : "#Trx"}, inplace = True)

    summary = summary.reset_index()

    sheet_dict = {
        "Dashboard Raw" : dashraw,
        "GDS Raw" : gdsraw,
        "Line Per Line": reconciled_df,
        "Unrecon": unrecon,
        "Summary" :summary
        
    }
    
    return sheet_dict
