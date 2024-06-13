import json
import pytz
import time
import schedule
import openai
from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime
import base64
from email.mime.text import MIMEText


with open('openai_credentials.json', 'r') as file:
    data = json.load(file)
    openai.api_key = data['openai_api_key']

with open('config.json', 'r') as file:
    data = json.load(file)
    DELEGATED_EMAIL = data['DELEGATED_EMAIL']
    NAME = data['NAME']
    USER_EMAIL = data['USER_EMAIL']

SERVICE_ACCOUNT_FILE = 'google_credentials.json'

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly',
          'https://www.googleapis.com/auth/gmail.send']

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
delegated_credentials = credentials.with_subject(DELEGATED_EMAIL)


def get_calendar_events():
    service = build('calendar', 'v3', credentials=delegated_credentials)
    now = datetime.datetime.now(datetime.timezone.utc)
    start_of_day = datetime.datetime.combine(
        now.date(), datetime.time(0, 0), tzinfo=datetime.timezone.utc)
    end_of_day = datetime.datetime.combine(
        now.date(), datetime.time(23, 59, 59), tzinfo=datetime.timezone.utc)

    calendar_list = service.calendarList().list().execute()

    events = []

    for calendar in calendar_list.get('items', []):
        events_result = service.events().list(calendarId=calendar['id'], timeMin=start_of_day.isoformat(
        ), timeMax=end_of_day.isoformat(), singleEvents=True, orderBy='startTime').execute()
        events.extend(events_result.get('items', []))

    return events


def generate_message(events):
    if not events:
        events_details = "No events for today"
    else:
        events_details = "\n".join(
            [f"{event.get('summary', 'No Title')} at {event['start'].get('dateTime', event['start'].get('date'))}" for event in events])

    system_prompt = (
        """You are a helpful and supportive assistant.
        You are sending a message to f{}."""
    )

    prompt = f"Good morning message. Details about today's events:\n{events_details}. Add an encouraging/light note for each event. Integrate these events naturally in the message. Keep it short and sweet"

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content.strip()


def send_email(message):
    service = build('gmail', 'v1', credentials=delegated_credentials)
    email_msg = MIMEText(message)
    email_msg['to'] = USER_EMAIL
    email_msg['subject'] = 'Good Morning!'

    raw = {'raw': base64.urlsafe_b64encode(email_msg.as_bytes()).decode()}
    service.users().messages().send(userId='me', body=raw).execute()


def main():
    events = get_calendar_events()
    message = generate_message(events)
    send_email(message)


def job():
    print("Executing!")
    main()


if __name__ == '__main__':
    schedule.every().day.at("07:00:00", "Europe/Rome").do(job)
    
    while True:
        schedule.run_pending()
        time.sleep(300)