# Things not done

Hello future developers! Here are some things that are partially implemented or known to have problems.

## Features

### Filtering
Filtering is currently done solely in the frontend. This means that the frontend requests all data at once (all fields for all instruments). So far this has worked fine, but in case some performance issues arise, this could be optimized to be done at least partly in the backend.

### CSV Export
There is currently an endpoint for returning the whole database as a CSV file, and a management command for exporting the CSV locally on the server. However, none of these are accessible for the users the functionality has not been implemented in the frontend. Additionally, none of these provide the possibility to have scheduled backups of the database, as the customer had asked. This probably has to be done using other tools, such as crontab.

### Logout
Logging out has not been implemented in the frontend.

### Error messages
Currently, when for when example adding an instrument or doing another operation fails, the frontend will alert the user with the error message from the API. Some of these might be a bit cryptic or misleading to the end user as they are meant more for the frontend developers.


## Bugs to fix

Adding a new instrument sometimes breaks the search function for the current session. Modifying an instrument does not do this. Sometimes the search works but the newly added instrument is not found in the list of instruments, while sometimes the whole search function breaks in its entirety. No idea at all why or how this happens.

If adding a new instrument succeeds, it is not possible to edit or delete it, as the frontend doesn't know the id of the newly added instrument since it doesn't fetch it from the backend. Currently the frontend notifies the user to reload the page if editing or deleting an instrument fails, as this fixes the problem.

Filters also don't respond to changes made to the instruments during the current session.

## Code cleanup

Some repeated code with the overlays in the frontend.

## Testing

### End to end Testing

There are some Cypress E2E testing things, but nothing that actually tests anything. (I couldn't get it to work)

### Unit tests

The unit tests are also a bit limited. Some functionality also can't really be tested without proper end to end testing frameworks.
