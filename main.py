import requests
import os
from dotenv import load_dotenv
from email.message import EmailMessage
from email.utils import formataddr
import ssl
import smtplib
from pathlib import Path
from datetime import datetime


BASE_DIR = Path(__file__).resolve().parent

load_dotenv()

SENDER = os.getenv('EMAIL_HOST_USER')
PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = os.getenv('EMAIL_PORT')
NOTIF_RECIEVER = os.getenv('NOTIF_RECIEVER')
MIN_BALANCE = float(os.getenv('MIN_BALANCE'))



def get_timestamp_str():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return timestamp


def write_log(text, filename="log.txt"):
    log_entry = f"{get_timestamp_str()} - {text}\n"
    filepath = BASE_DIR / filename
    with open(filepath, "a") as file:
        file.write(log_entry)


def entry_last_run():
    with open('last_run.dat', 'w') as f:
        f.write(get_timestamp_str())


def get_balance():
    api_host = os.getenv('API_HOST')
    url = f"{api_host}/v1/user/balance"
    api_key = os.getenv("STABILITY_API_KEY")
    if api_key is None:
        raise Exception("Missing Stability API key.")

    response = requests.get(url, headers={
        "Authorization": f"Bearer {api_key}"
    })

    if response.status_code != 200:
        raise Exception("Non-200 response: " + str(response.text))

    payload = response.json()
    return payload['credits']


def send_html_email(receiver, subject, body):
    em = EmailMessage()
    em['From'] = formataddr(("Appnotrix AI", SENDER))
    em['To'] = receiver
    em['Subject'] = subject
    em.set_content(body, subtype='html')
    
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(EMAIL_HOST, EMAIL_PORT, context=context) as smtp:
        smtp.login(SENDER, PASSWORD)
        smtp.sendmail(SENDER, receiver, em.as_string())


def get_msg(balance):
    msg = f"""<h1>Appnotrix AI image generator's credit is running low.</h1></br>
    <h2>Your current credit balance is <b style="color: red;">{balance}</b>.</h2>
    <p>You are receiving this email because your minimum maintainable balance is set to {MIN_BALANCE} credits.</p>
    """
    return msg


if __name__ == '__main__':
    try:
        balance = get_balance()
    except Exception as e:
        write_log(f'Cannot get the balance: {str(e)}', 'error.txt')
    if balance < MIN_BALANCE:
        message_body = get_msg(balance)
        try:
            send_html_email(
                NOTIF_RECIEVER,
                'Low Balance Alert',
                message_body
            )
        except Exception as e:
            write_log(f'Mail Sending Error: {str(e)}', 'error.txt')
        else:
            write_log(f'Mail sent to {NOTIF_RECIEVER}')
    entry_last_run()