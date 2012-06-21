import string 
import base64 
import sspi 
import smtplib
import sys
import os
from smtplib import SMTPException, SMTPAuthenticationError 
from email.mime.text import MIMEText

# NTLM Guide -- http://curl.haxx.se/rfc/ntlm.html 
 
SMTP_EHLO_OKAY = 250 
SMTP_AUTH_CHALLENGE = 334 
SMTP_AUTH_OKAY = 235 

EMAIL_SENDER_HOST = 'microsoft.com'
 
def asbase64(msg): 
    return string.replace(base64.encodestring(msg), '\n', '') 
 
def connect_to_exchange_as_current_user(smtp): 
    """Example: 
    >>> import smtplib 
    >>> smtp = smtplib.SMTP("my.smtp.server") 
    >>> connect_to_exchange_as_current_user(smtp) 
    """ 
 
    # Send the SMTP EHLO command 
    code, response = smtp.ehlo() 
    if code != SMTP_EHLO_OKAY: 
        raise SMTPException("Server did not respond as expected to EHLO command") 
 
    sspiclient = sspi.ClientAuth('NTLM') 
 
    # Generate the NTLM Type 1 message 
    sec_buffer=None 
    err, sec_buffer = sspiclient.authorize(sec_buffer) 
    ntlm_message = asbase64(sec_buffer[0].Buffer) 
 
    # Send the NTLM Type 1 message -- Authentication Request 
    code, response = smtp.docmd("AUTH", "NTLM " + ntlm_message) 
 
    # Verify the NTLM Type 2 response -- Challenge Message 
    if code != SMTP_AUTH_CHALLENGE: 
        raise SMTPException("Server did not respond as expected to NTLM negotiate message") 
 
    # Generate the NTLM Type 3 message 
    err, sec_buffer = sspiclient.authorize(base64.decodestring(response)) 
    ntlm_message = asbase64(sec_buffer[0].Buffer) 
 
    # Send the NTLM Type 3 message -- Response Message 
    code, response = smtp.docmd("", ntlm_message) 
    if code != SMTP_AUTH_OKAY: 
        raise SMTPAuthenticationError(code, response) 

def send_email_from_current_user(receivers, subject, content):
    sender = os.environ.get("USERNAME")
    send_email(sender, receivers, subject, content)

def send_email(sender, receivers, subject, content):
    msg = MIMEText(content)
    sender = sender + "@" + EMAIL_SENDER_HOST
    receivers = str.join(',',[x + "@" + EMAIL_SENDER_HOST for x in receivers])
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = receivers

    s = smtplib.SMTP('smtphost.redmond.corp.microsoft.com')
    connect_to_exchange_as_current_user(s)
    s.sendmail(sender, receivers, msg.as_string())
    s.quit()

