#!/usr/bin/python

from __future__ import print_function
import httplib2
import os
import sys

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
import googleapiclient

import datetime

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
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'calendar-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME

        credentials = tools.run_flow(flow, store, FuckYourFlags())

        print('Storing credentials to ' + credential_path)
    return credentials

def insertEvent(year, month, day, name, calendar="Dienstplan"):
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)

    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time

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

    if calendar_id == None:
        print("Kalender nicht gefunden.")
        sys.exit(1)

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