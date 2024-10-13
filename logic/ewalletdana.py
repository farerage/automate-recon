import pandas as pd
import numpy as np

def reconcile_data(file1_paths, file2_path):
    
    dana_ewallet_report = pd.read_csv(file1_paths[0]) if file1_paths[0].endswith('.csv') else pd.read_excel(file1_paths[0])
    dana_ewallet_gds = pd.read_csv(file2_path[0]) if file2_path[0].endswith('.csv') else pd.read_excel(file2_path[0])

    dana_ewallet_gds_raw = dana_ewallet_gds.copy()
    dana_ewallet_report_raw = dana_ewallet_report.copy()


    dana_ewallet_gds = dana_ewallet_gds.drop(['tx_serial_number','source_of_fund','vendor_service'], axis=1)

    dana_ewallet_report = dana_ewallet_report.drop(['SETTLEMENT_TXN_ID','TXN_ID','MID','ACQUIREMENT_ID','MERCHANT_NAME','MERCHANT_REQUEST_ID','MERCHANT_CUST_ID','SHOP_ID','BUYER_MOBILE_NO','DIVISION_ID','TXN_CURRENCY'],axis=1)


    refund = dana_ewallet_report[dana_ewallet_report['TXN_TYPE'] == 'REFUND']
    refundindex = dana_ewallet_report[dana_ewallet_report['TXN_TYPE'] == 'REFUND'].index
    dana_ewallet_report = dana_ewallet_report.drop(refundindex)

    dana_ewallet_report['MERCHANT_COMMISSION_EDIK'] = dana_ewallet_report['MERCHANT_COMMISSION_EDIK']/100
    dana_ewallet_report['SERVICE_TAX_EDIK'] = dana_ewallet_report['SERVICE_TAX_EDIK']/100
    dana_ewallet_report['SETTLE_AMOUNT'] = dana_ewallet_report['SETTLE_AMOUNT']/100
    dana_ewallet_report['TXN_AMOUNT'] = dana_ewallet_report['TXN_AMOUNT']/100

    agg_functions = {'MERCHANT_TRANS_ID': 'first', 'TXN_AMOUNT': 'sum', 'MERCHANT_COMMISSION_EDIK' :'sum', 'SERVICE_TAX_EDIK' : 'sum', 'SETTLE_AMOUNT':'sum'}

    new_dana_ewallet_report = dana_ewallet_report.groupby(dana_ewallet_report['MERCHANT_TRANS_ID']).aggregate(agg_functions)

    new_dana_ewallet_report.rename(columns={"MERCHANT_TRANS_ID": "Unique"}, inplace=True)

    coupon = dana_ewallet_report[dana_ewallet_report['PAY_METHOD'] == 'COUPON']

    i = dana_ewallet_report[dana_ewallet_report['PAY_METHOD'] == 'COUPON'].index

    dana_ewallet_report = dana_ewallet_report.drop(i)

    new_dana_ewallet_report = pd.merge(dana_ewallet_report ,new_dana_ewallet_report, left_on='MERCHANT_TRANS_ID', right_on='Unique', how='outer')

    new_dana_ewallet_report = new_dana_ewallet_report.drop(['TXN_AMOUNT_x','MERCHANT_COMMISSION_EDIK_x','SERVICE_TAX_EDIK_x','WITHHOLDING_TAX_EDIK','SETTLE_AMOUNT_x'],axis=1)

    new_dana_ewallet_report = new_dana_ewallet_report.add_suffix('_DASH')
    dana_ewallet_gds = dana_ewallet_gds.add_suffix('_GDS')

    data_compare = pd.merge(new_dana_ewallet_report,dana_ewallet_gds, left_on='MERCHANT_TRANS_ID_DASH', right_on='tx_ref_number_GDS', how='outer', indicator=True)

    data_compare['Match?'] = np.where((data_compare['MERCHANT_TRANS_ID_DASH'] == data_compare['tx_ref_number_GDS']) & (data_compare['TXN_AMOUNT_y_DASH'] == data_compare['amount_GDS']) , "Recon", "Unrecon")

    realtimesettleindex = data_compare[data_compare['settlement_time_GDS'].isna()].index
    data_compare.loc[realtimesettleindex, 'settlement_time_GDS'] = data_compare.loc[realtimesettleindex, 'last_updated_datetime_GDS']


    unrecon = data_compare[data_compare['Match?'] == 'Unrecon']
    indexunrecon = data_compare[data_compare['Match?'] == 'Unrecon'].index
    data_compare = data_compare.drop(indexunrecon)
    summary = data_compare.copy()

    summary['last_updated_datetime_GDS'] = pd.to_datetime(summary['last_updated_datetime_GDS'], format='%b %d, %Y, %I:%M:%S %p').dt.date
    summary['settlement_time_GDS'] = pd.to_datetime(summary['settlement_time_GDS'], format='%b %d, %Y, %I:%M:%S %p').dt.date
    summary['transaction_datetime_GDS'] = pd.to_datetime(summary['transaction_datetime_GDS'], format='%b %d, %Y, %I:%M:%S %p').dt.date
    summary['last_updated_datetime_GDS'] = pd.to_datetime(summary['last_updated_datetime_GDS'])
    summary['settlement_time_GDS'] = pd.to_datetime(summary['settlement_time_GDS'])
    summary['transaction_datetime_GDS'] = pd.to_datetime(summary['transaction_datetime_GDS'])


    summary = summary.groupby(['transaction_datetime_GDS', 'last_updated_datetime_GDS', 'settlement_time_GDS', 'username_GDS', 'service_GDS', 'mam_parent_username_GDS', 'mam_child_username_GDS', 'vendor_code_GDS'], dropna = False).agg({'tx_ref_number_GDS':'count','amount_GDS' : 'sum', 'admin_fee_GDS' : 'sum','admin_fee_invoice_GDS' : 'sum', 'MERCHANT_COMMISSION_EDIK_y_DASH' :'sum', 'SERVICE_TAX_EDIK_y_DASH' : 'sum', 'deduction_cost_GDS' : 'sum','settlement_amount_GDS' :'sum' })
    summary.rename(columns = {'tx_ref_number_GDS' : "#Trx"}, inplace = True)
    summary = summary.reset_index()

    sheet_dict = {
        "Dashboard Raw" : dana_ewallet_report_raw,
        "GDS Raw" : dana_ewallet_gds_raw,
        "Line Per Line": data_compare,
        "Unrecon": unrecon,
        "Summary" :summary,
        "Refund" : refund
    }
        # Add more sheets as required
    return sheet_dict

