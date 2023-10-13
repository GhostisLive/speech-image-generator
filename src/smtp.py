import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import src.colours as colours

__smtp = None
__sender = os.environ["EMAILADDR"]
__pass = os.environ["APPPASSWD"]

def create_smtp_conn():
    global __smtp
    if __smtp is not None:
        print(colours.yellow("A connection existed, but may have disconnected."))
    
    print(colours.blue("Creating SMTP connection..."))
    context = ssl.create_default_context()
    __smtp = smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context)
    __smtp.login(__sender, __pass)
    print(colours.green("Created."))

    #return __smtp We perhaps dont want to expose the connection to the user

def send_email(to_send, msg, subject="Image Generator Verification Code"):
    try:
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = __sender
        message["To"] = to_send

        # Create the plain-text and HTML version of your message
        text = html = msg

        # Turn these into plain/html MIMEText objects
        part1 = MIMEText(text, "plain")
        part2 = MIMEText(html, "html")

        # Add HTML/plain-text parts to MIMEMultipart message
        # The email client will try to render the last part first
        message.attach(part1)
        message.attach(part2)

        __smtp.sendmail(
            __sender, to_send, message.as_string()
        )
    except smtplib.SMTPServerDisconnected: # Seems to disconnect automatically after 10 mins
        # Reconnect back and re send, we only handle this exception
        create_smtp_conn()
        send_email(to_send, msg, subject)
