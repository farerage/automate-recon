import pandas as pd
import numpy as np
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

def reconcile_data(file1_paths, file2_path):
    
    danamon_report = pd.read_csv(file1_paths[0], skiprows = 1, dtype = {'Note (Bill ID)' : 'str'}) if file1_paths[0].endswith('.csv') else pd.read_excel(file1_paths[0], skiprows = 1, dtype = {'Note (Bill ID)' : 'str'})
    danamon_gds = pd.read_csv(file2_path[0], dtype = {'qr_id' : 'str'}) if file2_path[0].endswith('.csv') else pd.read_excel(file2_path[0], dtype = {'qr_id' : 'str'})

    danamon_report['Transaction Amount'] = danamon_report['Transaction Amount'].str.replace(',','')
    danamon_report['Transaction Amount'] = danamon_report['Transaction Amount'].astype(str).astype(float)
    danamon_report['MDR'] = danamon_report['MDR'].str.replace(',','')
    danamon_report['MDR'] = danamon_report['MDR'].astype(str).astype(float)
    
    danamon_report_raw = danamon_report.copy()
    danamon_gds_raw = danamon_gds.copy()
    
    danamon_report = danamon_report.drop(['Group Name','Merchant ID','NMID','MPAN','Merchant Name', 'QR ID', "QR Type", 'Terminal ID','Customer PAN', 'Issuer Code','Invoice No.', 'Merchant Partner Acc. No', 'Merchant Partner Acc. Name', 'Note'], axis=1)
    danamon_gds = danamon_gds.drop(['merchant_id','id','Transaction SN'],axis=1)
    
    mask = danamon_report[danamon_report['Note (Bill ID)'].isna()]
    maskindex = danamon_report[danamon_report['Note (Bill ID)'].isna()].index
    danamon_report = danamon_report.drop(maskindex)
    
    danamon_gds[danamon_gds.duplicated('qr_id', keep = False)]
    gds_duplicated = danamon_gds[danamon_gds.duplicated('qr_id')]
    danamon_gds = danamon_gds.drop_duplicates('qr_id')
    danamon_report[danamon_report.duplicated('Note (Bill ID)')]
    dash_duplicated = danamon_report[danamon_report.duplicated('Note (Bill ID)')]
    danamon_report = danamon_report.drop_duplicates('Note (Bill ID)')
    
    danamon_report = pd.concat([danamon_report, mask]).reset_index(drop=True)

    date_format = '%b %d, %Y, %I:%M:%S %p'
    danamon_gds['last_updated_datetime'] = pd.to_datetime(danamon_gds['last_updated_datetime'], format=date_format).dt.date
    danamon_gds['transaction_datetime'] = pd.to_datetime(danamon_gds['transaction_datetime'], format=date_format).dt.date
    danamon_gds['last_updated_datetime'] = pd.to_datetime(danamon_gds['last_updated_datetime'])
    danamon_gds['transaction_datetime'] = pd.to_datetime(danamon_gds['transaction_datetime'])   

    danamon_report = danamon_report.add_suffix('_DASH')
    danamon_gds = danamon_gds.add_suffix('_GDS')

    data_compare = pd.merge(danamon_report,danamon_gds, left_on='Note (Bill ID)_DASH', right_on='qr_id_GDS', how='outer', indicator=True)
    data_compare['Match?'] = np.where((data_compare['Note (Bill ID)_DASH'] == data_compare['qr_id_GDS']) & (data_compare['Transaction Amount_DASH'] == data_compare['transaction_amount_GDS']) , 'Recon', 'Unrecon')
    
    data_compare['_merge'] = data_compare['_merge'].cat.rename_categories({'left_only': 'Dash Only', 'right_only': 'GDS Only'})
    
    realtimesettleindex = data_compare[data_compare['settlement_time_GDS'].isna()].index
    data_compare.loc[realtimesettleindex, 'settlement_time_GDS'] = data_compare.loc[realtimesettleindex, 'last_updated_datetime_GDS']
    data_compare['settlement_time_GDS'] = pd.to_datetime(data_compare['settlement_time_GDS'], format=date_format).dt.date
    data_compare['settlement_time_GDS'] = pd.to_datetime(data_compare['settlement_time_GDS'])

    data_compare['MDR_DASH'] = data_compare['MDR_DASH'].astype(str).astype(float)
    
    unrecon = data_compare[data_compare['Match?'] == 'Unrecon']
    indexunrecon = data_compare[data_compare['Match?'] == 'Unrecon'].index
    data_compare = data_compare.drop(indexunrecon)

    summary = data_compare.copy()
    summary = summary.groupby(['last_updated_datetime_GDS','transaction_datetime_GDS', 'settlement_time_GDS', 'username_GDS', 'product_type_GDS', 'Transaction Channel Type_GDS', 'mam_parent_username_GDS', 'mam_child_username_GDS', 'charge_vendor_code_GDS'], dropna = False).agg({'Note (Bill ID)_DASH':'count','transaction_amount_GDS' : 'sum', 'admin_fee_GDS' : 'sum','admin_fee_invoice_GDS' : 'sum', 'MDR_DASH' :'sum', 'deduction_cost_GDS' : 'sum', 'deduction_cost_gross_GDS' :'sum','settlement_amount_GDS' :'sum' })
    summary.rename(columns = {'Note (Bill ID)_DASH' : "#Trx"}, inplace = True)
    summary = summary.reset_index()
    
    sheet_dict = {
        "Dashboard Raw" : danamon_report_raw,
        "GDS Raw" : danamon_gds_raw,
        "Line Per Line": data_compare,
        "Unrecon": unrecon,
        "Dash Duplicated" : dash_duplicated,
        "GDS Duplicated" : gds_duplicated,
        "Summary" :summary
        # Add more sheets as required
    }

    return sheet_dict
