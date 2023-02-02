import json
import requests
import logging

from . import xero_api
from . import reshape

import azure.functions as func
from azure.storage.blob import ContainerClient
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

#Initialize our credentials:
default_credential = DefaultAzureCredential(
    exclude_environment_credential = 1)

#Connnect to the key vault and authenticate yourself:
woods_key_vault = SecretClient(
    vault_url='https://woodskeys.vault.azure.net/',
    credential = default_credential)

#Grab the blob connection string:
blob_conn_string = woods_key_vault.get_secret(
    name = 'xero-blob-storage-connection-string')

#Connect to the Container client:
container_client = ContainerClient.from_connection_string(
    conn_str=blob_conn_string.value,
    container_name = 'woodsxerodata')

def get_contacts():
    logging.info('Getting contacts data from Xero.')  
    
    # 1) Refresh Xero API Tokens
    old_refresh_token = woods_key_vault.get_secret(name = 'xero-refresh-token')
    new_tokens = xero_api.XeroRefreshToken(old_refresh_token.value)
    xero_tenant_id = xero_api.XeroTenants(new_tokens[0])

    # 2) API CALLS
    get_url = 'https://api.xero.com/api.xro/2.0/Contacts'
    response = requests.get(get_url,
                            headers = {
                                'Authorization': 'Bearer ' + new_tokens[0],
                                'Xero-tenant-id': xero_tenant_id,
                                'Accept': 'application/json'
                            }).json()

    # 3) Reshape response JSON.
    reshaped_response = reshape.reshape_contacts(response)

    # 4) Saving data to a blob in the container.
    filename = 'xero_live_contacts.json'
    container_client.upload_blob(
        name=filename,
        data=json.dumps(reshaped_response),
        blob_type='BlockBlob',
        overwrite=True
    )

    logging.info('Completed contacts data import')  