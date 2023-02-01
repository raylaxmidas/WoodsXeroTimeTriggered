import json
import requests
import datetime
import logging

import azure.functions as func
from azure.storage.blob import ContainerClient
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

#from . import xero_api
from . import import_accounts
from . import import_budget_summary

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
    import_budget_summary.get_budget_summary()

    utc_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()

    if mytimer.past_due:
        logging.info('The timer is past due!')

    logging.info('Python timer trigger function ran at %s', utc_timestamp)

