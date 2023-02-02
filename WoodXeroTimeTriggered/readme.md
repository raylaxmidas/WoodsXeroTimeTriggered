# Woods Xero Time Triggered

The following Azure Function `WoodsXeroTimeTriggered` is used to pull from the Xero API for Woods. The information from the Xero API is generally heavily nested hence some unnested is carried out within the `reshape.py` function as well. Once the information is pulled out the information is pulled out and reshaped; the JSON files are landed to container. 

From here the JSON files are picked up by a schduled pipeline and stored in a tablular manner to a Azure SQL Sever from which the PowerBI Dashboard access the information.

## Development Environment Setup
In order to run this function within a locally within VS Code, various extension, packages and environment variables must be configured correctly. 


## How it works

For a `TimerTrigger` to work, you provide a schedule in the form of a [cron expression](https://en.wikipedia.org/wiki/Cron#CRON_expression)(See the link for full details). A cron expression is a string with 6 separate expressions which represent a given schedule via patterns. The pattern we use to represent every 5 minutes is `0 */5 * * * *`. This, in plain text, means: "When seconds is equal to 0, minutes is divisible by 5, for any hour, day of the month, month, day of the week, or year".

## Learn more

<TODO> Documentation
