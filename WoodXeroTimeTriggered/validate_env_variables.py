import os

print("Azure Tenant ID is: {id}".format(id=os.environ['Azure_TENANT_ID']))
print("Azure Client ID is: {id}".format(id=os.environ['Azure_CLIENT_ID']))
print("Azure Client Secret ID is: {id}".format(id=os.environ['Azure_CLIENT_SECRET']))