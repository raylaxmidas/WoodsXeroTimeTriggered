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
    #Refresh Xero API Tokens
    old_refresh_token = woods_key_vault.get_secret(name = 'xero-refresh-token')
    new_tokens = xero_api.XeroRefreshToken(old_refresh_token.value)
    xero_tenant_id = xero_api.XeroTenants(new_tokens[0])
    
    #API CALLS
    #Headers
    HEADERS = { 'xero-tenant-id': xero_tenant_id,
                'Authorization': 'Bearer ' + new_tokens[0],
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
    
    #API Call  
    #Date two years ago from today
    DateFrom = (dt.date.today() - dt.timedelta(days=365*2)).strftime("%Y-%m-%d")

    #Today's date
    DateTo = dt.date.today().strftime("%Y-%m-%d")

    logging.info('Collecting all budget data from Xero from:')
    logging.info(DateFrom)
    logging.info('to')
    logging.info(DateTo)

    URL = '	https://api.xero.com/api.xro/2.0/Budgets'
    response = requests.request('GET', URL, headers=HEADERS).json()

    #Get the list of budget IDs.
    budget_ids = [budget["BudgetID"] for budget in response["Budgets"]]

    #Loop through each BudgetID.
    for budget_id in budget_ids:
        logging.info('Collecting data for budget ID:')
        logging.info(budget_id)

        #Append the BudgetID to the URL.
        budget_url = '	https://api.xero.com/api.xro/2.0/Budgets' + '/' + budget_id + '?dateTo=' + DateTo  + '&dateFrom=' + DateFrom

        #Make the request to the API.
        budget_response = requests.get(budget_url, headers=HEADERS).json()

        # Process the response data
        reshaped_response = reshape.reshape_budget(budget_response)
        
        #Saving raw data to a blob in the container.
        #filename = f'xero_raw_budget_full_{budget_id}.json'
        #container_client.upload_blob(
        #    name=filename,
        #    data=json.dumps(budget_response),
        #    blob_type='BlockBlob',
        #    overwrite=True
        #)

        #Saving reshaped data to a blob in the container.
        filename = f'xero_live_budget_full_{budget_id}.json'
        container_client.upload_blob(
            name=filename,
            data=json.dumps(reshaped_response),
            blob_type='BlockBlob',
            overwrite=True
        )

        # Save the reshaped data to a file
        #with open(f"budget_{budget_id}.json", "w") as file:
            #json.dump(reshaped_response, file)

    logging.info('Completed full budget data import.')  