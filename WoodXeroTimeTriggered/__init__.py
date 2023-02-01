import json
import requests
import datetime
import logging

import azure.functions as func
from azure.storage.blob import ContainerClient
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

from . import xero_api
from . import import_accounts

def main(mytimer: func.TimerRequest) -> None:
    logging.info('Running Woods Xero Data Pull')

    ##Xero API Access Initialization Process:
    #tokens = xero_api.XeroFirstAuth()
    #xero_api.XeroRefreshToken(tokens[1])
    ##Run a test request from Xero API:
    #xero_api.XeroRequestTest()                     
    logging.info('Xero API Access Initialization Process and Test Complete')

    #Importing Data
    import_accounts.get_accounts()

    #Initialize our credentials:
    default_credential = DefaultAzureCredential(exclude_environment_credential = 1)

    #Connnect to the key vault and authenticate yourself:
    woods_key_vault = SecretClient(vault_url='https://woodskeys.vault.azure.net/',credential = default_credential)

    #Grab the blob connection string:
    blob_conn_string = woods_key_vault.get_secret(name = 'xero-blob-storage-connection-string')

    #Connect to the Container client:
    container_client = ContainerClient.from_connection_string(conn_str=blob_conn_string.value,container_name = 'woodsxerodata')

    filename = 'test.json'
    employee_string = '{"first_name": "Ray", "last_name": "Laxmidas", "department": "Data Science"}'
    json_object = json.loads(employee_string)

    #Create a new blob in the container.
    container_client.upload_blob(
        name=filename,
        data=json.dumps(obj=json_object),
        blob_type='BlockBlob'
    )

    utc_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()

    if mytimer.past_due:
        logging.info('The timer is past due!')

    logging.info('Python timer trigger function ran at %s', utc_timestamp)

