# Woods Xero Time Triggered
The following Azure Function `WoodsXeroTimeTriggered` is used to pull data from the Xero API for Woods. The information from the Xero API is generally heavily nested hence some unnesting is carried out within the `reshape.py` function as well. Once the information is pulled out and reshaped; the JSON files are landed to a container. 

From here the JSON files are picked up by a schduled pipeline and stored in a tablular manner to a Azure SQL Sever. For accounts, contacts and invoices the entire table is dropped from the SQL Sever and the new data from the JSON file is added. In the case of the budget summery, and the profit and loss data the tables are retained in the SQL Sever and additional rows are appended on. This is because for accounts, contacts and invoices the entire history can be pulled from the Xero API.

The PowerBI Dashboard pulls the data from the SQL Sever.

Through out this code tokens and secrets have been stored within an Azure Key Vault so the source code does not hold any sensitive information.

The function will gets/lands data stored within the `lumatrainingstorage` storage account and secrets within the `WoodsKeys` Key Vault. An Azure login will be required which has permission to access both of these reasources in order to run this function locally on your machine.

The function has been set up to run on a weekly basis.

## Notes about debugging / running Azure Functions Locally:
When Azure functions run locally they must have have a `__init__.py` file with a main function. This main function will run during each debugging session. Each time the function is run the `tasks.json` is excuted. These "tasks" mainly relate to intalling the packages found in the requirements.txt file. Azure functions will install the packages everytime the function is trigger in the cloud.

## Helpful Resources:
The following resources may be helpful in udnerstanding some of the concepts used for this Azure Function.

* [Access The Xero API using Python & OAuth2 (Xero Integrations Tutorial)](https://www.youtube.com/watch?v=t0DgAMgN8VY)
* [Microsoft Azure Overview: Creating a Service Principal](https://www.youtube.com/watch?v=J7zb-a8Bjzo)
* [Microsoft Azure Overview: The Azure Python SDK](https://www.youtube.com/watch?v=5oIcT0HCrvI)
* [Azure Functions in Python | Timer Triggers Pt. 1](https://www.youtube.com/watch?v=2QVNJZmE5e0) 
* [Azure Functions in Python | Timer Triggers Pt. 2]( https://www.youtube.com/watch?v=OXnfKYwnoVk)
* [Azure Functions in Python | Timer Triggers Pt. 3](https://www.youtube.com/watch?v=egLrNS0dq50)

## Common Azure Commands Used Throughout Function
### 1. `default_credential = DefaultAzureCredential(exclude_environment_credential = 1)`

This function is at the top of each import module.

This function provides the authentication for the function to communicate to the Azure resources. It uses various credential types. More information can be found here: https://learn.microsoft.com/en-us/dotnet/api/azure.identity.defaultazurecredential?view=azure-dotnet

In our case we have setup a enviroment credential (RayWoods) and also have access via VS Code being logged into Azure using our/my workplace email address. We will use the latter hence enviroment credentials has been excluded using an additional parameter. When deploying the app `exclude_environment_credential = 1` needs to be removed, see the "Deploying the Application to Azure" section for more details.

### 2. `woods_key_vault = SecretClient(vault_url='https://woodskeys.vault.azure.net/' credential = default_credential)`
 
  This function provides methods to manage KeyVaultSecret in the Azure Key Vault. The client supports creating, retrieving, updating, deleting, purging, backing up, restoring, and listing KeyVaultSecret. The main secrets this function uses are:

* `xero-blob-storage-connection-string` is the connection string used to connect to the Azure Storage Account. This can be found in the Azure web portal under: Home > Storage Accounts > lumatrainingstorage > Access keys > key1 > Connection String > Show. The following function is used to collect this secret: `blob_conn_string = woods_key_vault.get_secret(
    name = 'xero-blob-storage-connection-string')`

* `xero-client-id` and `xero-client-secret` these are used to connect to the Xero API. And are found at https://developer.xero.com/ > Log In > MyApps > LumaAnalytics > Configuration. This "app" was setup prior to this function being created. The following functions are used to collect these secrets respectively: `client_id = woods_key_vault.get_secret(name = 'xero-client-id')` and `client_secret = woods_key_vault.get_secret(name = 'xero-client-secret')`.

* `xero-refresh-token` is a constantly refreshing token used to access the Xero API. The refreshing process for tokens can be found in the module `xero_api`. The following functions are used to access and set the refresh token secret respectively: `old_refresh_token = woods_key_vault.get_secret(name = 'xero-refresh-token')` and `woods_key_vault.set_secret('xero-refresh-token',new_refresh_token)` 

### 3. `container_client = ContainerClient.from_connection_string(conn_str=blob_conn_string.value,container_name = 'woodsxerodata')`
Creates a client which allows the function to interact with a specific container. In our case this is `woodsxerodata`.

### 4. `container_client.upload_blob(name=filename, data=json.dumps(reshaped_response), blob_type='BlockBlob', overwrite=True)`
This function allows us to upload a JSON file pulled from the Xero API into the `woodsxerodata` container. In all upload cases the original file is overwritten.

### Downloading to Blob Storage for Profit and Loss Data
The profit and loss is pulled on a monthly level across the last year from the day the function is run. As each month is pulled from API one at a time they need to need to appended together. To achieve within each loop that grabs a month, the JSON file is read from the blob, all historical data is selected and the new month is appended on. This historical data and current month pulled within the loop is then saved to the blob storage. The part of the code which completes this process is shown below:

```
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
```

## Development Environment Setup
In order to run this function locally within VS Code, various extensions, packages and environment variables must be configured correctly. 

### Extensions
For for VS Code ensure that the following extensions have been created.
* Azure Resources.
* Azure Functions.
* Azure CLI Tools Extension and Azure CLI from [here.](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli-windows?tabs=azure-cli)
* Azure Account.
* Dev Containers

Once these are installed log into Azure via opening the terminal using <kbd>Ctrl+J</kbd> and typing the command `az login` ensure you login with an account which has permissions to the to `lumatrainingstorage` Storage Account and `WoodsKeys` Key Vault.

### Creating Service Principal
For the purpose of our local testing we have used a workplace email address / VisualStudioCodeCredential. In other words we are signed in to VS Code with our workplace email which has permissions to the `lumatrainingstorage` Storage Account and `WoodsKeys` Key Vault. Thus the `DefaultAzureCredential(exclude_environment_credential = 1)` will use this as a basis to authenticate the function when running locally.

However, a Service Principal (SP) was setup which has access to these resources should another user need access without a workplace login.

The following command was used to create the RayWoods SP:
```
az ad sp create-for-rbac --name RayWoods --skip-assignment --sdk-auth > RayWoodsAzureSP.json
```
This function creates the SP and stores details in RayWoodsAzureSP.json. This JSON file can be found on `C:\Users\RayLaxmidas\Luma Analytics\Lumineers(Documents\7 Clients\Woods\Data Engineering\RayWoods Service Principal.7z\`. 

Within the JSON file tihe clientID, clientSecret, subscriptionID and tenantID are stored. These values were taken and add to the environment variables by running the following script in a .cmd file.

```
REM Sets the Environment Variables that persist over sessions.
REM Make sure to run this as an administrator and then shut down VS Code
REM and re-open it.

SETX AZURE_SUBSCRIPTION_ID <subscriptionID>
SETX AZURE_TENANT_ID <tenantID>
SETX AZURE_CLIENT_ID <clientID>
SETX AZURE_CLIENT_SECRET <clientSecret>
```
These environment variables have been set up by running this .cmd file from command prompt as adminstrator. Note all VS Code instances need to be closed and reopened for them to take affect. Once complete the environment variables can be verified by running the following Python script.

```
import os

print("Azure Tenant ID is: {id}".format(id=os.environ['Azure_TENANT_ID']))
print("Azure Client ID is: {id}".format(id=os.environ['Azure_CLIENT_ID']))
print("Azure Client Secret ID is: {id}".format(id=os.environ['Azure_CLIENT_SECRET']))
```
Once these environment variables have been set and verified we can connect to Azure Resources using `default_credential = DefaultAzureCredential()`. Note that the SP created must have the appropriate permission setup in Azure.

### Function Setup Setting
The `WoodsXeroTimeTriggered` function used the following setup procedure:

1. Download and install a 64 Bit Version of Python 3.7, 3.8 or 3.9 (https://www.python.org/downloads/windows/). Note Azure functions are not compatible with 32 Bit and newer version of Python.
2. Create a project folder and open this within VS Code.
3. Go to the Azure Extension.
4. Under "WORKSPACE Local" click create function.
5. Select "Timer Trigger", provide a function name, select a trigger cycle using a CRON expression (https://arminreiter.com/2017/02/azure-functions-time-trigger-cron-cheat-sheet/). Note the time trigger cycle can be editted from the function.json file.
6. Add core Azure packages to the requirements file shown below.
7. Install requirments using `pip install -r requirements.txt`. Ensure the virtual environment is activated before running this command.

```
# DO NOT include azure-functions-worker in this file
# The Python Worker is managed by Azure Functions platform
# Manually managing azure-functions-worker may cause unexpected issues

azure-functions
requests

msrest == 0.6.18
msrestazure == 0.6.4
azure-core == 1.7.0
azure-common == 1.1.26
azure-identity == 1.4.0
azure-mgmt-core == 1.2.0
azure-storage-blob == 12.4.0
azure-keyvault-secrets == 4.2.0  
```

### Initializing the Xero API
The main function has the following bit of code which has been commented out. 

```
#Xero API Access Initialization Process:
#tokens = xero_api.XeroFirstAuth()
#xero_api.XeroRefreshToken(tokens[1])
##Run a test request from Xero API:
#xero_api.XeroRequestTest()    
```

These commands assist initialization of the Xero API when the API is accessed for the first time or tokens have expired/lost etc. 

To intialize the Xero API follow the procedure below:

1.  Ensure the `xero-client-id` and `xero-client-secret` sourced from `https://developer.xero.com/ > Log In > MyApps > LumaAnalytics > Configuration` are correct.
2. Uncomment the code shown above in the `__init__.py` file.
3. Enter a break point in the `xero_api.py` file after the line which reads `auth_res_url = 'What is the response URL?'`. This need to happen as we cannot use `input()` in an Azure function. See the code extract below for the location of the breakpoint.
4. Run the Azure function in a debugging session.
5. A web browser will open. Authorise the the Xero application and copy the authorisation URL.
6. Use the variable editor to manually enter the `auth_res_url`, remembering to ''.
7. Once complete let the script continue.

```diff
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
    auth_res_url = 'What is the response URL?'

-<INSERT BREAK POINT HERE>-

    start_number = auth_res_url.find('code=') + len('code=')
    end_number = auth_res_url.find('&scope')
    auth_code = auth_res_url[start_number:end_number]
    logging.info('Auth Code:')
    logging.info(auth_code)
    ...
```

## Deploying the Application to Azure
When deploying this function to Azure we need to consider the function will no longer be running in the local environment. Within the local environment the function is used the Azure Sign In Authentication.

The function will now be running within Azure and require it's own authentication for the resources it uses. The main issue/error which the function will encounter in authorisation of the application. In order to overcome authorisation error the following process was followed:

1. Prior to deployment remove `exclude_environment_credential = 1` from any where in the code that `default_credential = DefaultAzureCredential(exclude_environment_credential = 1)` appears.
2. Adjust the CRON expression in the function.json file. Generally the default CRON expression is `0 */5 * * * *` so that the function runs every 5 mins when debugging locally. Once deployed we'd likely want a different cycle such as `0 0 0 * * 0` which is weekly on Sunday.
3. Deploy the function to Azure to existing function application which has been made and overwrite any existing the initialize function in the cloud.
4. Go to Microsoft Azure Home → Function Apps → [Function Name] → Identity → Status → Set to ON and Save → Copy Object (principal) ID.
5. Go to Microsoft Azure Home → Key Vaults → [Key Vault Name] → Access Policies → Create → Provide Secret Management → Under Principal Search the Object ID Copied → Create Policy.
6. Go to Microsoft Azure Home → Storage Accounts → [Storage Account Name] → [Container Name] → Access Policies → Add Policy → Paste in Identifier (which is the Object (principal) ID from step 4) → Provide All Permission.



