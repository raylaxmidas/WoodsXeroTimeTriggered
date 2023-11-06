import re
import datetime as dt
import calendar
from dateutil.relativedelta import relativedelta as datedelta

#-------------------------------------------------------------------------------
#Helper Functions:
# EPOCH TO YMD
def epoch_ymd(x):
    s = re.findall('(?<=\().*?(?=\+)', x)[0]
    date = dt.datetime.utcfromtimestamp(float(s)/1000.)
    return date.strftime("%Y-%m-%d")

# Adjusted version of your function to handle date strings both with and without the `+` symbol
def epoch_ymd_adjusted(x):
    s = re.findall('(?<=\().*?(?=\+|\))', x)[0]
    date = dt.datetime.utcfromtimestamp(float(s)/1000.)
    return date.strftime("%Y-%m-%d")

# Converts period strings of the format "YYYY-MM" into "YYYY-MM-DD", 
# where DD is the last day of the respective month
def convert_period_to_last_day(period_str):
    year, month = map(int, period_str.split('-'))
    _, last_day = calendar.monthrange(year, month)
    return f"{year}-{month:02d}-{last_day:02d}"

# UNNEST - RETURN ITEMS ONLY
def unnest_short(_dic):
    _items = []
    # Account Name & Values
    _line = [x['Value'] for x in _dic['Cells']]
    # Account ID
    if _line[0] == 'Total':
        _line.append(None)
    else:
        _line.append(_dic['Cells'][0]['Attributes'][0]['Value'])
    _items.append(_line)
    return _items

# UNPACK
def unnest_report(_dic):
    _title = []
    _items = []
    _accID = []
    for i in _dic['Rows']:
        # Account Name
        _line = [x['Value'] for x in i['Cells']]
        _items.append(_line)
        # Account ID
        if len(i['Cells'][0]) > 1:
            _id = i['Cells'][0]['Attributes'][0]['Value']
        else:
            _id = None
        _accID.append(_id)
        # Account Type
        if len(_dic['Title']) == 0:
            _title.append(_items[0][0])
        else:
            _title.append(_dic['Title'])
        if len(_items) == 0:
            _items.append([_title])

    return _title, _items, _accID

#-------------------------------------------------------------------------------
#Reshaping function for contacts:
def reshape_contacts(_dic):
    # Get report
    CONTACTS = _dic['Contacts']
    # Convert to readable date
    for i in CONTACTS:
        for key in ['UpdatedDateUTC']:
            try:
                i[key] = epoch_ymd(i[key])
            except:
                i[key] = None
    return CONTACTS

#Reshaping function for accounts:
def reshape_accounts(_dic):
    # Get report
    ACCOUNTS = _dic['Accounts']
    # Convert to readable date
    for i in ACCOUNTS:
        for key in ['UpdatedDateUTC']:
            try:
                i[key] = epoch_ymd(i[key])
            except:
                i[key] = None
    return ACCOUNTS

#Reshaping function for bank accounts:
def reshape_bank(_dic, _date):
    # Separate columns from values
    CONTENTS = [x for x in [x['Value'] for x in _dic['Reports'][0]['Rows'][0]['Cells']] if x!='']
    COLUMNS = ['Bank Accounts', 'AccID', 'Month', 'Type', 'Amount']
    REPORT = _dic['Reports'][0]['Rows'][1]['Rows']
    # Unnest
    ITEMS = []
    for i in range(0, len(REPORT)):
        _ITEM = unnest_short(REPORT[i])
        ITEMS += _ITEM
    # Reshape
    RESHAPED = []
    for values in ITEMS:
        for i in range(1,len(values)-1):
            DIC = {'Bank Accounts': values[0]}
            DIC['AccID'] = values[5]
            DIC['Month'] = _date
            DIC['Type'] = CONTENTS[i]
            DIC['Amount'] = values[i]
            RESHAPED.append(DIC)
    return RESHAPED

#Reshaping function for bank transfers:
def reshape_bank_transfers(_dic):
    # Get report
    BANKTRANSFERS = _dic['BankTransfers']
    # Convert to readable date
    for i in BANKTRANSFERS:
        for key in ['CreatedDateUTC', 'Date']:
            try:
                i[key] = epoch_ymd(i[key])
            except:
                i[key] = None
    return BANKTRANSFERS

#Reshaping function for budget summary:
def reshape_budget_summary(_dic):
    # Get report
    REPORT = _dic['Reports'][0]['Rows']
    # Separate dates
    DATES = [x for x in [x['Value'] for x in REPORT[0]['Cells']] if x!=''][1:]
    DATES = [(dt.datetime.strptime(x, '%b-%y') + datedelta(day=31)).strftime("%Y-%m-%d") for x in DATES]
    # Unnest
    NAMES = []
    ITEMS = []
    ACCID = []
    for i in range(1, len(REPORT)):
        _NAME, _ITEM, _ACCID = unnest_report(REPORT[i])
        NAMES += _NAME
        ITEMS += _ITEM
        ACCID += _ACCID
    # Reshape
    COLUMNS = ['Type', 'Account', 'AccID', 'Month', 'Amount']
    BUDGET_SUMMARY = []
    for i in range(0, len(ITEMS)):
        for j in range(1, len(ITEMS[i])):
            DIC = {'Type':NAMES[i]}
            DIC['Account'] = ITEMS[i][0]
            DIC['AccID'] = ACCID[i]
            DIC['Month'] = DATES[j-1]
            DIC['Amount'] = ITEMS[i][j]
            BUDGET_SUMMARY.append(DIC)

    return BUDGET_SUMMARY

#Reshaping function for invoices:
def reshape_invoices(_dic):
    # Get report
    INVOICES = _dic['Invoices']
    # Convert to readable date
    for i in INVOICES:
        i['Payments'] = len(i['Payments'])
        for key in ['Date', 'DueDate', 'UpdatedDateUTC', 'FullyPaidOnDate', 'ExpectedPaymentDate']:
            try:
                i[key] = epoch_ymd(i[key])
            except:
                i[key] = None
        for key in i['Contact']:
            i['Contact.' + key] = str(i['Contact'][key])
        del i['Contact']

    return INVOICES

#Reshaping function for profit and loss statement:
def reshape_pnl(_dic, FROM_DATE, TO_DATE):
    # Get report
    REPORT = _dic['Reports'][0]['Rows']
    # Separate out the TrackingOption
    TRACKINGOPTION = [x for x in [x['Value'] for x in REPORT[0]['Cells']] if x!=''][0:]
    # Unnest
    NAMES = []
    ITEMS = []
    ACCID = []
    for i in range(1, len(REPORT)):
        _NAME, _ITEM, _ACCID = unnest_report(REPORT[i])
        NAMES += _NAME
        ITEMS += _ITEM
        ACCID += _ACCID
    # Reshape
    COLUMNS = ['Type', 'Account', 'AccID', 'TrackingOption', 'Amount', 'FromDate', 'ToDate']
    PNL = []
    for i in range(0, len(ITEMS)):
        for j in range(1, len(ITEMS[i])):
            DIC = {'Type':NAMES[i]}
            DIC['Account'] = ITEMS[i][0]
            DIC['AccID'] = ACCID[i]
            DIC['TrackingOption'] = TRACKINGOPTION[j-1]
            DIC['Amount'] = ITEMS[i][j]
            DIC['FromDate'] = FROM_DATE
            DIC['ToDate'] = TO_DATE
            PNL.append(DIC)
    
    return PNL

#Reshaping function for credit notes:
def reshape_creditnotes(_dic):
    CREDITNOTES = []
    NOTES = _dic['CreditNotes']
    for i in NOTES:
    # Convert to readable date
        for key in ['Date', 'DueDate', 'UpdatedDateUTC', 'FullyPaidOnDate', 'ExpectedPaymentDate', 'Allocations.Date']:
            try:
                i[key] = epoch_ymd(i[key])
            except:
                i[key] = None
    
    for i in NOTES:
        # 1+ Allocations: Allocations + Contacts
        if len(i['Allocations']) > 0:
            for ALLOCATION in i['Allocations']:
                NOTE = {}
                NOTE.update(i)
                # Unlist Allocations
                for key in ['Amount', 'Date']:
                    NOTE['Allocations.' + key] = str(ALLOCATION[key])
                NOTE['Allocations.InvoiceID'] = ALLOCATION['Invoice']['InvoiceID']
                NOTE['Allocations.InvoiceNumber'] = ALLOCATION['Invoice']['InvoiceNumber']
                del NOTE['Allocations']
                # Unlist contacts
                for key in NOTE['Contact']:
                    NOTE['Contact.' + key] = str(NOTE['Contact'][key])
                del NOTE['Contact']
                CREDITNOTES.append(NOTE)
        # No Allocations: Contacts + None Allocations
        else:
            for key in ['Amount', 'Date', 'InvoiceID', 'InvoiceNumber']:
                i['Allocations.' + key] = None
            del i['Allocations']
            # Unlist contacts
            for key in i['Contact']:
                i['Contact.' + key] = str(i['Contact'][key])
            del i['Contact']
            CREDITNOTES.append(i)

    return CREDITNOTES

#Reshaping the Budget Data
def reshape_budget(data):
    # Extract the top-level DateTimeUTC
    top_level_datetime_utc = data.get('DateTimeUTC', None)
    if top_level_datetime_utc:
        top_level_datetime_utc = epoch_ymd_adjusted(top_level_datetime_utc)
    
    # Initialize an empty list to store flattened records
    BUDGET_FULL = []
    
    # Iterate over each budget
    for budget in data['Budgets']:
        # Extract values from the budget level using the .get() method for consistency
        description = budget.get('Description', "Unknown Description")
        updated_date_utc = budget.get('UpdatedDateUTC', None)
        if updated_date_utc:
            updated_date_utc = epoch_ymd_adjusted(updated_date_utc)
        
        # Extract other common fields from the budget and include the top-level DateTimeUTC
        budget_common_fields = {
            'DateTimeUTC': top_level_datetime_utc,
            'BudgetID': budget.get('BudgetID', None),
            'Status': budget.get('Status', None),
            'Type': budget.get('Type', None),
            'UpdatedDateUTC': updated_date_utc,
            'Description': description
        }
        
        # Check for tracking data and get up to two sets of tracking information
        tracking_fields = {
            'TrackingName1': None,
            'TrackingOption1': None,
            'TrackingID1': None,
            'TrackingName2': None,
            'TrackingOption2': None,
            'TrackingID2': None
        }

        # If tracking data is available, fill in the tracking fields
        if 'Tracking' in budget and len(budget['Tracking']) > 0:
            tracking_fields['TrackingName1'] = budget['Tracking'][0].get('Name')
            tracking_fields['TrackingOption1'] = budget['Tracking'][0].get('Option')
            tracking_fields['TrackingID1'] = budget['Tracking'][0].get('TrackingCategoryID')
            if len(budget['Tracking']) > 1:
                tracking_fields['TrackingName2'] = budget['Tracking'][1].get('Name')
                tracking_fields['TrackingOption2'] = budget['Tracking'][1].get('Option')
                tracking_fields['TrackingID2'] = budget['Tracking'][1].get('TrackingCategoryID')

        # Iterate over each budget line
        for line in budget['BudgetLines']:
            # Extract common fields from the budget line
            line_common_fields = {
                'AccountID': line.get('AccountID', None),
                'AccountCode': line.get('AccountCode', None)
            }
            
            # Iterate over each budget balance
            for balance in line['BudgetBalances']:
                # Convert period to the desired format
                final_period = convert_period_to_last_day(balance['Period'])
                
                # Construct a flattened record by combining common fields with balance details
                record = {
                    **budget_common_fields,
                    **line_common_fields,
                    **tracking_fields,
                    'Period': final_period,
                    'Amount': balance['Amount']
                }
                
                # Append the flattened record to the list
                BUDGET_FULL.append(record)
                
    return BUDGET_FULL

# Function to flatten the JSON structure manually
def reshape_tracking_categories(tracking_categories):
    # List to hold the flattened data
    TRACKING_CATEGORIES = []

    # Go through each tracking category
    for category in tracking_categories['TrackingCategories']:
        # Extract category details
        category_details = {
            'Category_Name': category['Name'],
            'Category_Status': category['Status'],
            'Category_TrackingCategoryID': category['TrackingCategoryID']
        }
        
        # Go through each option in the tracking category
        for option in category['Options']:
            # Create a new record for each option, including the category details
            record = {**category_details, **option}
            # Add the record to our list
            TRACKING_CATEGORIES.append(record)
    
    return TRACKING_CATEGORIES