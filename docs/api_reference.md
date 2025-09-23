# API Reference

## General

### Get all instruments
`GET api/instruments/`  
Returns all instruments in the database as JSON objects.

### Add a new instrument
`POST api/instruments/`  
Adds a new instrument to the database. The instrument should be provided as JSON object. Requires authentication.

### Get a specific instrument
`GET api/instruments/<id>/`  
Returns the instrument with the given id as a JSON object.

### Update the information for a specific instrument
`PUT api/instruments/<id>/`  
Updates the information for a given instrument. Functions like adding an instrument. Requires authentication.

### Delete a specific instrument
`DELETE api/instruments/<id>/`  
Deletes the instrument with the given id. Requires authentication.

### Get the filters (all unique values) of a given field
`GET api/instruments/valueset/<fieldname>/`  
Returns all unique values for the given field. Intended to be used for filtering.

### Get instruments as a CSV file
`GET api/instruments/csv/`  
Returns a CSV file with all the instruments.

## Login and register

### Log in
`POST api/login/`  
Logs in and returns a token used for authentication. The login info should be provided as a JSON object with the fields `email` and `password`.

### Log out
`POST api/logout/`  
Logs out.

### Register a new user account
`POST api/register/`  
Registers a new account. The user info should be provided as a JSON object with the fields `invite_code`, `full_name`, `email` and `password`.

## Admin

### Get all users
`GET api/users/`  
Returns all users as JSON objects. Requires authentication.

### Get a specific user
`GET api/users/<id>/`  
Returns a specific user as a JSON object. Requires authentication.

### Generate an invite code
`GET api/invite/`  
Generates and returns a new invite code. Requires authentication.

### Get instruments with service contract info
`GET api/service/`  
Returns the instruments with their service info. Requires authentication.

### Log out all users
`POST api/logoutall/`  
Logs out all users. Requires authentication.

## On authentication

When logging in successfully, the login endpoint returns a token. This token should then be sent with all non-GET requests in a header with the name `Authorization` with the value `Token <token>`. For example:  
```
"Authorization"="Token 917375dfafb2bdb6f2cfe57e1801bef5ce672a10b8861aba58b4982370ed6c02"
```

