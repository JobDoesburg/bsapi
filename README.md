# BSAPI

A basic Python wrapper for the [D2LValence Brightspace API](https://docs.valence.desire2learn.com).

## Installation

The package can be installed using `pip` by running `python -m pip install brightspace-api`.

## Example usage

To construct a `bsapi.BSAPI` instance, you need the LMS host URL and an OAuth access token (see below for how to obtain one).

```python
access_token = '<your OAuth access token>'
lms_url = '<your LMS host URL>'
le_version = '1.79'
lp_version = '1.47'

api = bsapi.BSAPI(access_token, lms_url, le_version, lp_version)
whoami = api.whoami()

print(f'Identified as: {whoami.first_name} {whoami.last_name}')
```

If you want to verify whether the configured LE and LP product versions are supported, call the `api.check_versions()` method.
It is also possible to forcibly use the latest supported versions by calling `api.check_versions(use_latest=True)`.
This will overwrite the configured LE and LP product versions with the latest ones according to the LMS host.
Generally you want to specify explicit versions.
Even though updates are typically backwards compatible, it may still have unexpected results or cause issues with this wrapper.
As such, testing and using explicit versions may provide better long term stability.

The `bsapi.APIConfig` class provides a way to collect the various configuration parameters, which can easily be serialized to and deserialized from JSON.
Using this configuration instance, a convenience method can be called to create `bsapi.BSAPI` instances via `BSAPI.from_config(config, access_token)`.

## OAuth Authentication

To obtain an access token, use the OAuth 2.0 flow:

```python
import bsapi
from bsapi import oauth

# Step 1: Create authorization URL
client_id = '<your client id>'
redirect_uri = '<your redirect URI>'
auth_url = oauth.create_auth_url(client_id, redirect_uri)
print(f'Visit: {auth_url}')

# Step 2: After user authorizes, extract code from callback URL
callback_url = '<URL user was redirected to>'
authorization_code = oauth.parse_callback_url(callback_url)

# Step 3: Exchange code for access token
client_secret = '<your client secret>'
token_response = oauth.exchange_code_for_token(
    client_id, client_secret, redirect_uri, authorization_code
)
access_token = token_response['access_token']

# Step 4: Use access token with API
api = bsapi.BSAPI(access_token, lms_url)
```

## Design

The `bsapi.BSAPI` class provides wrappers for a subset of commonly used API endpoints and uses OAuth authentication via Bearer tokens.
Endpoints that send data via DELETE/POST/PUT HTTP methods are typically implemented directly as public methods.
Endpoints that get data via a GET HTTP method typically are implemented as a private method (e.g. `_whoami()`) that return the raw JSON object.
The public method equivalent (e.g. `whoami()`) will call the private method and attempt to interpret this JSON object into a properly typed object as defined in `bsapi.types` (e.g. `bsapi.types.WhoAmIUser`).
Generally you should use the public method, but there could be reasons to use the private method instead, namely:

- A newer version of the API has added more fields to JSON objects returned that are not included by the typed version.
- A newer version of the API has made non-backwards compatible changes that cause interpreting the JSON object to fail.
- The JSON object returned does not match the API documentation, and hence interpreting it fails.

Ideally these last two cases do not occur, or are quickly fixed, but sadly the Brightspace API documentation is not entirely correct/consistent with the actual responses observed during testing.
It also tends to be outdated at times, where responses contain additional fields not (yet) described by the API documentation.

## Feedback

The `bsapi.feedback` module contains several `FeedbackEncoder` implementations that allow feedback plain-text to be formatted as HTML.
This formatted HTML can then be provided as rich-text HTML input for the `bsapi.BSAPI.set_dropbox_folder_submission_feedback` endpoint using the `feedback_html` parameter.
The use case for this module is graders writing student feedback in plain-text with some Markdown influence, which allows them to insert objects such as code blocks that are then nicely rendered to students.

## Helper

The `bsapi.helper` module defines an `APIHelper` class that wraps around a `bsapi.BSAPI` instance.
It extends the API by providing helper methods to perform common operations not directly supported by the API.

## Building

Execute `python3 -m build` to build the Python wheel, which can then be installed using `python3 -m pip install <bsapi-...-py3-none-any.whl>`.