import os, smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders


fromaddr = 'contact.adamantmedia@gmail.com'

def emailer(subject, extra, fle=None):
    toaddr = 'contact.adamantmedia@gmail.com'
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = subject
    msg.attach(MIMEText(extra))

    if fle:
        f = MIMEBase('application', "octet-stream")
        f.set_payload(open(fle, "rb").read())
        encoders.encode_base64(f)
        f.add_header('Content-Disposition', 'attachment; filename = "{}"'.format(os.path.basename(fle)))
        msg.attach(f)
    sendmail(toaddr,msg)

def textmessenger(text,subject=None):
    toaddr='2673941683@vzwpix.com'
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    if subject:
        msg['Subject'] = subject
    msg.attach(MIMEText(text))
    sendmail(toaddr,msg)

def sendmail(toaddr,msg):
    username = 'contact.adamantmedia@gmail.com'
    password = 'LmmSlijjoK'

    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login(username, password)
    server.sendmail(fromaddr, toaddr, msg.as_string())
    server.quit()

if __name__=='__main__':
    emailer("hello","World")
