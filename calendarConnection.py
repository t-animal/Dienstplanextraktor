#!/usr/bin/python

from __future__ import print_function
import httplib2
import os
import sys

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client import clientsecrets
from oauth2client.file import Storage
import googleapiclient

import datetime

from util import _CONFIG_DIR

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/calendar-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/calendar'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Dienstplan Extraktor'

class FuckYourFlags:
         auth_host_name  = "localhost"
         noauth_local_webserver  = False
         auth_host_port  = [8080, 8090]
         logging_level  = "ERROR"


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    if not os.path.exists(_CONFIG_DIR):
        os.makedirs(_CONFIG_DIR)
    credential_path = os.path.join(_CONFIG_DIR, 'calendar_credentials.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = flow_from_json(CLIENT_SECRET, SCOPES)
        flow.user_agent = APPLICATION_NAME

        credentials = tools.run_flow(flow, store, FuckYourFlags())

        print('Storing credentials to ' + credential_path)
    return credentials

def _getCalendarId(service, calendar):
    calendar_id = None
    page_token = None
    while True:
        calendar_list = service.calendarList().list(pageToken=page_token).execute()
        for calendar_list_entry in calendar_list['items']:
            if calendar_list_entry["summary"] == calendar:
                calendar_id = calendar_list_entry["id"]
                break
        page_token = calendar_list.get('nextPageToken')
        if not page_token:
            break
    return calendar_id

def clearAllEvents(year, month, day, calendar="test"):
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)

    calendar_id = _getCalendarId(service, calendar)
    page_token = None

    if calendar_id == None:
        raise Exception("Kalender nicht gefunden.")
        sys.exit(1)

    endyear, endmonth, endday = getEndDate(year, month, day)
    timeMin = "{}-{}-{}T00:00:00+00:00".format(year, month, day)
    timeMax = "{}-{}-{}T00:00:00+00:00".format(endyear, endmonth, endday)

    while True:
      events = service.events().list(calendarId=calendar_id,
        pageToken=page_token,
        timeMin=timeMin, timeMax=timeMax).execute()
      for event in events['items']:
        service.events().delete(calendarId=calendar_id, eventId=event['id']).execute()
      page_token = events.get('nextPageToken')
      if not page_token:
        break

def getEndDate(year, month, day):
    endyear = year
    endmonth = month
    endday = day + 1
    maxDays = [31,29 if ((year%4 == 0 and not year%100 == 0) or year%400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    if endday > maxDays[month-1]:
        endday = 1
        if month == 12:
            endmonth = 1
            endyear += 1
        else:
            endmonth += 1

    return (endyear, endmonth, endday)

def insertEvent(year, month, day, name, calendar="test"):
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)

    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time

    calendar_id = _getCalendarId(service, calendar)

    if calendar_id == None:
        raise Exception("Kalender nicht gefunden.")
        sys.exit(1)

    endyear, endmonth, endday = getEndDate(year, month, day)

    event = {
        "summary": name,
        "start": {
            "date": "{}-{}-{}".format(year, month, day)
        },
        "end": {
            "date": "{}-{}-{}".format(endyear, endmonth, endday)
        }
    }

    event = service.events().insert(calendarId=calendar_id, body=event).execute()

    return event


def flow_from_json(json, scope, redirect_uri=None,
                    message=None, cache=None, login_hint=None,
                    device_uri=None, pkce=None, code_verifier=None):
    """Create a Flow from a clientsecrets json (mostly copied from oauth2client.client)

    Will create the right kind of Flow based on the contents of the
    clientsecrets json or will raise InvalidClientSecretsError for unknown
    types of Flows.

    Args:
        filename: string, the json containing the client secrets.
        scope: string or iterable of strings, scope(s) to request.
        redirect_uri: string, Either the string 'urn:ietf:wg:oauth:2.0:oob' for
                      a non-web-based application, or a URI that handles the
                      callback from the authorization server.
        message: string, A friendly string to display to the user if the
                 clientsecrets file is missing or invalid. If message is
                 provided then sys.exit will be called in the case of an error.
                 If message in not provided then
                 clientsecrets.InvalidClientSecretsError will be raised.
        cache: An optional cache service client that implements get() and set()
               methods. See clientsecrets.loadfile() for details.
        login_hint: string, Either an email address or domain. Passing this
                    hint will either pre-fill the email box on the sign-in form
                    or select the proper multi-login session, thereby
                    simplifying the login flow.
        device_uri: string, URI for device authorization endpoint. For
                    convenience defaults to Google's endpoints but any
                    OAuth 2.0 provider can be used.

    Returns:
        A Flow object.

    Raises:
        UnknownClientSecretsFlowError: if the file describes an unknown kind of
                                       Flow.
        clientsecrets.InvalidClientSecretsError: if the clientsecrets file is
                                                 invalid.
    """
    try:
        client_type, client_info = clientsecrets.loads(json)
        if client_type in (clientsecrets.TYPE_WEB,
                           clientsecrets.TYPE_INSTALLED):
            constructor_kwargs = {
                'redirect_uri': redirect_uri,
                'auth_uri': client_info['auth_uri'],
                'token_uri': client_info['token_uri'],
                'login_hint': login_hint,
            }
            revoke_uri = client_info.get('revoke_uri')
            optional = ('revoke_uri', 'device_uri', 'pkce', 'code_verifier')
            for param in optional:
                if locals()[param] is not None:
                    constructor_kwargs[param] = locals()[param]

            return client.OAuth2WebServerFlow(
                client_info['client_id'], client_info['client_secret'],
                scope, **constructor_kwargs)

    except clientsecrets.InvalidClientSecretsError as e:
        if message is not None:
            if e.args:
                message = ('The client secrets were invalid: '
                           '\n{0}\n{1}'.format(e, message))
            sys.exit(message)
        else:
            raise
    else:
        raise client.UnknownClientSecretsFlowError(
            'This OAuth 2.0 flow is unsupported: {0!r}'.format(client_type))