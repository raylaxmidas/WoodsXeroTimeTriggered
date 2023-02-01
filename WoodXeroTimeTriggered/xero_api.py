import json
import requests
import webbrowser
import base64
import logging

import azure.functions as func
from azure.storage.blob import ContainerClient
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

#Initialize our credentials for Azure so we can access Keys.
default_credential = DefaultAzureCredential(
    exclude_environment_credential = 1)

#Connnect to the key vault and authenticate:
woods_key_vault = SecretClient(
    vault_url='https://woodskeys.vault.azure.net/',
    credential = default_credential)

#Grab the Xero Client id:
client_id = woods_key_vault.get_secret(
    name = 'xero-client-id')

#Grab the Xero Client id:
client_secret = woods_key_vault.get_secret(
    name = 'xero-client-secret')

#Other non - sensitive information for Xero API Connection:
redirect_url = 'https://xero.com/'
scope = 'offline_access accounting.transactions accounting.settings accounting.reports.read accounting.contacts accounting.budgets.read'
b64_id_secret = base64.b64encode(bytes(client_id.value + ':' + client_secret.value, 'utf-8')).decode('utf-8')

#First time authorisation:
def XeroFirstAuth():
    # 1. Send a user to authorize your app:
    auth_url = ('''https://login.xero.com/identity/connect/authorize?''' +
                '''response_type=code''' +
                '''&client_id=''' + client_id.value +
                '''&redirect_uri=''' + redirect_url +
                '''&scope=''' + scope +
                '''&state=123''')
    webbrowser.open_new(auth_url)
    
    # 2. Users are redirected back to you with a code:
    
    #Manual input is not possible via Azure Function
    #auth_res_url = input('What is the response URL? ')
    auth_res_url = 'What is the response URL? '

    start_number = auth_res_url.find('code=') + len('code=')
    end_number = auth_res_url.find('&scope')
    auth_code = auth_res_url[start_number:end_number]
    logging.info('Auth Code:')
    logging.info(auth_code)
    
    #logging.info(auth_code)
    #logging.info('\n')
    
    # 3. Exchange the code:
    exchange_code_url = 'https://identity.xero.com/connect/token'
    response = requests.post(exchange_code_url, 
                            headers = {
                                'Authorization': 'Basic ' + b64_id_secret
                            },
                            data = {
                                'grant_type': 'authorization_code',
                                'code': auth_code,
                                'redirect_uri': redirect_url
                            })
    json_response = response.json()
    
    #logging.info('JSON Response for Access and Refresh Token:')
    #logging.info(json_response)
      
    # 4. Receive your tokens
    return [json_response['access_token'], json_response['refresh_token']]

# 5. Check the full set of tenants you've been authorized to access:
def XeroTenants(access_token):
    connections_url = 'https://api.xero.com/connections'
    response = requests.get(connections_url,
                           headers = {
                               'Authorization': 'Bearer ' + access_token,
                               'Content-Type': 'application/json'
                           })
    json_response = response.json()
    #logging.info(json_response)
    
    for tenants in json_response:
        json_dict = tenants
    return json_dict['tenantId']

#Function to refresh tokens:
def XeroRefreshToken(refresh_token):
    token_refresh_url = 'https://identity.xero.com/connect/token'
    response = requests.post(token_refresh_url,
                            headers = {
                                'Authorization' : 'Basic ' + b64_id_secret,
                                'Content-Type': 'application/x-www-form-urlencoded'
                            },
                            data = {
                                'grant_type' : 'refresh_token',
                                'refresh_token' : refresh_token
                            })
    json_response = response.json()
    #logging.info(json_response)
    
    #Store the refresh token:
    new_refresh_token = json_response['refresh_token']

    #Storing new refresh token:
    woods_key_vault.set_secret('xero-refresh-token',new_refresh_token)
   
    return [json_response['access_token'], json_response['refresh_token']]

#Test call for the API:
def XeroRequestTest():
    old_refresh_token = woods_key_vault.get_secret(name = 'xero-refresh-token')
    new_tokens = XeroRefreshToken(old_refresh_token.value)
    xero_tenant_id = XeroTenants(new_tokens[0])
    
    get_url = 'https://api.xero.com/api.xro/2.0/Invoices'
    response = requests.get(get_url,
                           headers = {
                               'Authorization': 'Bearer ' + new_tokens[0],
                               'Xero-tenant-id': xero_tenant_id,
                               'Accept': 'application/json'
                           })
    json_response = response.json()
    #logging.info(json_response)
