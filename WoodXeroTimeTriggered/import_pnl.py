import json
import requests
import logging
import datetime as dt
from dateutil.relativedelta import relativedelta as datedelta

from . import xero_api
from . import reshape

import azure.functions as func
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
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

#Connect to the Container client:
container_client = ContainerClient.from_connection_string(
    conn_str=blob_conn_string.value,
    container_name = 'woodsxerodata')

def get_pnl():
    logging.info('Getting profit and loss data from Xero.')
    
    # 1) Refresh Xero API Tokens
    old_refresh_token = woods_key_vault.get_secret(name = 'xero-refresh-token')
    new_tokens = xero_api.XeroRefreshToken(old_refresh_token.value)
    xero_tenant_id = xero_api.XeroTenants(new_tokens[0])

    #Pull data for the past year from today's date:
    i = 12
    while i >= 0:
               
        # 2) API CallS
        # 2.1) Headers
        headers = { 'xero-tenant-id': xero_tenant_id,
                    'Authorization': 'Bearer ' + new_tokens[0],
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                }
        
        # 2.2) API Call
        FROM_DATE = (dt.date.today() + dt.timedelta(hours=12) + datedelta(day=1) - datedelta(months=i)).strftime("%Y-%m-%d")
        TO_DATE = (dt.date.today() + dt.timedelta(hours=12) + datedelta(day=31) - datedelta(months=i)).strftime("%Y-%m-%d")
        
        logging.info("Pulling pnl data from: ")
        logging.info(FROM_DATE)
        logging.info("Pulling pnl data to: ")
        logging.info(TO_DATE)

        URL = 'https://api.xero.com/api.xro/2.0/Reports/ProfitAndLoss' + '?fromDate=' + FROM_DATE + '&toDate=' + TO_DATE + '&trackingCategoryID=1e6e1469-e019-4dba-a45f-38b6bdeb93a6' + '&trackingCategoryID2=6cade25f-8681-4501-9911-227af23affff'
        response = requests.request('GET', URL, headers=headers).json()

        # 3) Reshape response JSON.
        reshaped_response = reshape.reshape_pnl(response, FROM_DATE, TO_DATE)

        # 4) Downloading existing PnL JSON and appending data pulled within loop.

        # 4.1) Establishing Connection to PnL Blob
        filename = "xero_live_profit_and_loss.json"
        container_name="woodsxerodata"
        connection_string = blob_conn_string.value

        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        blob_client = container_client.get_blob_client(filename)

        # 4.2) Download the blob.
        streamdownloader = blob_client.download_blob()

        # 4.3) Read into local variable as JSON.
        all = json.loads(streamdownloader.readall())
        
        # 4.4) Select and store historical data ONLY to avoid duplication within the JSON file.
        historical = [i for i in all if dt.datetime.strptime(i['ToDate'], '%Y-%m-%d') < dt.datetime.strptime(FROM_DATE, '%Y-%m-%d')]
        
        # 4.5) Appending the existing data with the most current pull of from the API.
        pnl = historical + reshaped_response
        
        # 5) Saving data to a new blob in the container.
        filename = 'xero_live_profit_and_loss.json'
        container_client.upload_blob(
            name=filename,
            data=json.dumps(pnl),
            blob_type='BlockBlob',
            overwrite=True
        )

        i = i - 1 

    logging.info('Completed profit and loss data import.')