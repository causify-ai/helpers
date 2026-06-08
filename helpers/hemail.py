"""
Import as:

import helpers.hemail as hemail
"""

import email.mime.multipart as emmult
import email.mime.text as emtext
import os
import smtplib
from typing import Optional


def send_email(
    subject: str,
    message: str,
    to_adr: str,
    email_address: str = "",
    email_password: str = "",
    html: bool = False,
) -> None:
    """
    Send mail to specified e-mail addresses.

    :param message: Message to be sent
    :param to_adr: Mail to which to send messages
    :type list
    :return: None
    """
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    if email_address == "":
        email_address = os.environ["AM_EMAIL_ADDRESS"]
    if email_password == "":
        email_password = os.environ["AM_EMAIL_PASSWORD"]
    server.login(email_address, email_password)
    msg = emmult.MIMEMultipart()
    msg["From"] = email_address
    msg["To"] = ", ".join(to_adr)
    msg["Subject"] = subject
    if html:
        msg.attach(emtext.MIMEText(message, "html"))
    else:
        msg.attach(emtext.MIMEText(message, "plain"))

    text = msg.as_string()
    server.sendmail(email_address, to_adr, text)
