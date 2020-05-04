## Builtin
import base64
from email.mime.multipart import MIMEMultipart
import pathlib
##### For Attachments
import mimetypes
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
## 3rd Party
import httplib2
from apiclient.discovery import build
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client import tools
## Custom Module
from alcustoms import methods as almethods

myphone='2673941683@vzwpix.com'
PHONELOOKUP={'Verizon':'vzwpix.com','T-Mobile':'tmomail.net'}
myemail='contact.adamantmedia@gmail.com'

DIRE = pathlib.Path(__file__).resolve().parent

CLIENT_SECRET_FILE = DIRE / r"client_secrets.json"
STORAGE = DIRE / 'gmail.storage'

# Check https://developers.google.com/gmail/api/auth/scopes for all available scopes
OAUTH_SCOPE = 'https://www.googleapis.com/auth/gmail.compose'

def get_credentials():
    # Location of the credentials storage file
    storage = Storage(STORAGE)
        
    # Try to retrieve credentials from storage or run the flow to generate them
    credentials = storage.get()
    if credentials is None or credentials.invalid:
        # Start the OAuth flow to retrieve credentials
        flow = flow_from_clientsecrets(CLIENT_SECRET_FILE, scope=OAUTH_SCOPE, redirect_uri="urn:ietf:wg:oauth:2.0:oob")
        credentials = tools.run_flow(flow, storage)

    return credentials

def get_attachment(file):
    """ Creates a MIME-Object from the file (to be attached to a multipart Email) """
    content_type, encoding = mimetypes.guess_type(file)

    if content_type is None or encoding is not None:
        content_type = 'application/octet-stream'
    main_type, sub_type = content_type.split('/', 1)
    if main_type in ('text','image','audio'):
        if main_type == 'text': MIMEObj = MIMEText
        elif main_type == 'image': MIMEObj = MIMEImage
        elif main_type == 'audio': MIMEObj = MIMEAudio
        with open(file,'rb') as f:
            msg = MIMEObj(f.read(),_subtype=sub_type,_charset = "utf-8")
    else:
        with open(path, 'rb') as f:
            msg = MIMEBase(main_type, sub_type)
            msg.set_payload(f.read())
    msg.add_header('Content-Disposition', 'attachment', filename=file)
    return msg

def get_alternative(html):
    """ """
    msg = MIMEBase("text","html")
    msg.set_payload(html)
    return msg

class Messenger():
    def __init__(self,fromaddress = None):
        if fromaddress is None: fromaddress = myemail
        self.fromaddress = fromaddress
        credentials = get_credentials()
        # Authorize the httplib2.Http object with our credentials
        #self.http = credentials.authorize(http)

        #auth_uri=flow.step1_get_authorize_url()
        #credentials = flow.step2_exchange(auth_uri)

        http = httplib2.Http()
        self.http=credentials.authorize(http)
        # Build the Gmail service from discovery
        self.gmail_service = build('gmail', 'v1', http=self.http)

    def createemail(self,subject="", body="", fromaddr=None, toaddr=None, html=None, files=None):
        if not fromaddr: fromaddr=self.fromaddress
        if not toaddr: toaddr=self.fromaddress
        msg = MIMEMultipart('alternative')
        msg['from'] = fromaddr
        msg['to'] = toaddr
        msg['subject'] = subject
        
        att = MIMEText(body)
        msg.attach(att)

        if files:
            if not almethods.isiterable(files):
                files = [files,]
            for file in files:
                att = get_attachment(file)
                msg.attach(att)
        if html:
            att = get_alternative(html)
            msg.attach(att)
                
        return {'raw': base64.urlsafe_b64encode(msg.as_string().encode()).decode()}

    #def createtextmessage(self,text, subject=None, fromaddr=None, toaddr=myphone):
    #    if not fromaddr: fromaddr=self.username
    #    msg = MIMEMultipart()
    #    msg['From'] = fromaddr
    #    msg['To'] = toaddr
    #    if subject:
    #        msg['Subject'] = subject
    #    msg.attach(MIMEText(text))
    #    body = {'raw': base64.b64encode(msg.as_string())}
    #    return body

    def sendmail(self,body):
        message = (self.gmail_service.users().messages().send(userId="me", body=body).execute())
        return message

if __name__=='__main__':
    mess=Messenger()
    msg=mess.createemail(subject="Hello World",body="This is a test")
    mess.sendmail(msg)
