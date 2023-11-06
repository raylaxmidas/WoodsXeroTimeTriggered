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

def get_tracking_categories():
    logging.info('Getting tracking categories from Xero.')  
    
    #Refresh Xero API Tokens:
    old_refresh_token = woods_key_vault.get_secret(name = 'xero-refresh-token')
    new_tokens = xero_api.XeroRefreshToken(old_refresh_token.value)
    xero_tenant_id = xero_api.XeroTenants(new_tokens[0])
    
    #API CALLS
    #Headers:
    HEADERS = { 'xero-tenant-id': xero_tenant_id,
                'Authorization': 'Bearer ' + new_tokens[0],
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }

    URL = '		https://api.xero.com/api.xro/2.0/TrackingCategories'
    response = requests.request('GET', URL, headers=HEADERS).json()

    #Flatten the tracking categories:
    reshaped_response = reshape.reshape_tracking_categories(response)

    #Saving reshaped data to a blob in the container.
    filename = 'xero_live_tracking_categories.json'
    container_client.upload_blob(
            name=filename,
            data=json.dumps(reshaped_response),
            blob_type='BlockBlob',
            overwrite=True
        )

    # Save the reshaped data to a file:
    #with open(f"TC.json", "w") as file:
    #    json.dump(reshaped_response, file)

    logging.info('Completed tracking categories data import.')  