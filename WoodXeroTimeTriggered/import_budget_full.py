import json
import requests
import logging
import datetime as dt
from dateutil.relativedelta import relativedelta as datedelta

from . import xero_api
from . import reshape

import azure.functions as func
from azure.storage.blob import ContainerClient
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

#Initialize our credentials:
default_credential = DefaultAzureCredential()

#Connnect to the key vault and authenticate:
woods_key_vault = SecretClient(
    vault_url='https://woodskeys.vault.azure.net/',
    credential = default_credential)

#Grab the blob connection string:
blob_conn_string = woods_key_vault.get_secret(
    name = 'blob-storage-connection-string')

#Connect to the container client:
container_client = ContainerClient.from_connection_string(
    conn_str=blob_conn_string.value,
    container_name = 'woodsxerodata')

def get_budget_full():
    logging.info('Getting full budget data from Xero for the past 24 months.')  
    
    # 1) Refresh Xero API Tokens
    old_refresh_token = woods_key_vault.get_secret(name = 'xero-refresh-token')
    new_tokens = xero_api.XeroRefreshToken(old_refresh_token.value)
    xero_tenant_id = xero_api.XeroTenants(new_tokens[0])
    
    # 2) API CALLS
    # 2.1) Headers
    HEADERS = { 'xero-tenant-id': xero_tenant_id,
                'Authorization': 'Bearer ' + new_tokens[0],
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
    
    # 2.2) API Call  
    #From the last 12 months: 
    from_date = (dt.date.today() + dt.timedelta(hours=12) + datedelta(day=1) - datedelta(months=12)).strftime("%Y-%m-%d")
    logging.info('Collecting full budget data from Xero from:')
    logging.info(from_date)

    #Using the revised budget frrom woods
    BudgetID = '/8fe9c821-7eaf-453f-abd6-a15ce1f6620c'

    URL = '	https://api.xero.com/api.xro/2.0/Budgets' + '?date=' + from_date + '&periods=12&timeframe=1' + BudgetID
    response = requests.request('GET', URL, headers=HEADERS).json()

    #with open('response.json', 'w') as f:
    #    json.dump(response, f)

    logging.info('Getting full budget data from Xero for the past 12 months.')  