import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

from scraper import run
from emailer import build_email

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger(__name__)

def send_email(subject: str, html_body: str):
    send_from = os.environ.get('SEND_FROM_EMAIL')
    password = os.environ.get('SEND_FROM_PASSWORD')
    send_to = os.environ.get('SEND_TO_EMAIL')
    if not all([send_from, password, send_to]):
        log.error("Missing email environment variables!")
        return False
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = f"Contest Hulk <{send_from}>"
    msg['To'] = send_to
    msg.attach(MIMEText(html_body, 'html'))
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(send_from, password)
            server.sendmail(send_from, send_to, msg.as_string())
        log.info(f"Email sent to {send_to}")
        return True
    except Exception as e:
        log.error(f"Email failed: {e}")
        return False

def main():
    log.info(f"Contest Hulk starting - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    contests = run()
    log.info(f"Pipeline complete. {len(contests)} contests to send.")
    subject, html_body = build_email(contests)
    success = send_email(subject, html_body)
    if success:
        log.info("Email sent successfully!")
    else:
        log.error("Email send failed.")
        exit(1)

if __name__ == '__main__':
    main()
