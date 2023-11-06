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
from . import import_budget_summary
from . import import_contacts
from . import import_invoices
from . import import_credit_notes
from . import import_pnl
from . import import_budget_full
from . import import_tracking_categories

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
    import_contacts.get_contacts()
    import_invoices.get_invoices()
    import_credit_notes.get_credit_notes()
    import_pnl.get_pnl()
    import_budget_full.get_budget_full()
    import_tracking_categories.get_tracking_categories()

    utc_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()

    if mytimer.past_due:
        logging.info('The timer is past due!')

    logging.info('Woods Xero data pull timer trigger function ran at %s', utc_timestamp)

