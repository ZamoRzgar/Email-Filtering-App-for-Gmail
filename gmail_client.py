import os
import pickle
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import base64
import email
from datetime import datetime

class GmailClient:
    def __init__(self):
        # If modifying these scopes, delete the token.pickle file
        self.SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
        self.service = None
        self.authenticate()
    
    def authenticate(self):
        """Authenticate with Gmail API and create a service object"""
        creds = None
        # The file token.pickle stores the user's access and refresh tokens
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('gmail', 'v1', credentials=creds)
        return self.service is not None
    
    def get_unread_messages(self, max_results=500):
        """Get unread messages from Gmail inbox, sorted by date (newest first)"""
        if not self.service:
            raise Exception("Gmail API service not initialized")
        
        results = self.service.users().messages().list(
            userId='me',
            q='is:unread',
            maxResults=max_results
        ).execute()
        
        messages = results.get('messages', [])
        
        # If there are more messages than the max_results, get them with pagination
        while 'nextPageToken' in results and len(messages) < 1000:  # Set a reasonable upper limit
            page_token = results['nextPageToken']
            results = self.service.users().messages().list(
                userId='me',
                q='is:unread',
                maxResults=max_results,
                pageToken=page_token
            ).execute()
            messages.extend(results.get('messages', []))
    
        return messages
    
    def get_message_details(self, message_id):
        """Get full details of a specific message"""
        if not self.service:
            raise Exception("Gmail API service not initialized")
        
        message = self.service.users().messages().get(
            userId='me', id=message_id
        ).execute()
        
        return message
    
    def get_header(self, message, header_name):
        """Extract a specific header value from a message"""
        headers = message['payload']['headers']
        for header in headers:
            if header['name'] == header_name:
                return header['value']
        return ""
    
    def get_email_body(self, message):
        """Extract the body text from an email message"""
        if 'parts' in message['payload']:
            for part in message['payload']['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        data = part['body']['data']
                        return base64.urlsafe_b64decode(data).decode('utf-8')
        elif 'body' in message['payload'] and 'data' in message['payload']['body']:
            data = message['payload']['body']['data']
            return base64.urlsafe_b64decode(data).decode('utf-8')
        return ""
    
    def mark_as_important(self, message_id):
        """Mark a message as important"""
        if not self.service:
            raise Exception("Gmail API service not initialized")
        
        self.service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'addLabelIds': ['IMPORTANT']}
        ).execute()
    
    def archive_message(self, message_id):
        """Archive a message (remove from inbox)"""
        if not self.service:
            raise Exception("Gmail API service not initialized")
        
        self.service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'removeLabelIds': ['INBOX']}
        ).execute()
    
    def mark_as_spam(self, message_id):
        """Move a message to the spam folder"""
        if not self.service:
            raise Exception("Gmail API service not initialized")
        
        self.service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'addLabelIds': ['SPAM']}
        ).execute()
        
        # Also remove from inbox
        self.service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'removeLabelIds': ['INBOX']}
        ).execute()
    
    def trash_message(self, message_id):
        """Move a message to trash"""
        if not self.service:
            raise Exception("Gmail API service not initialized")
        
        self.service.users().messages().trash(
            userId='me', id=message_id
        ).execute()
    
    def create_label(self, label_name):
        """Create a new label if it doesn't exist already"""
        if not self.service:
            raise Exception("Gmail API service not initialized")
        
        # First check if the label already exists
        results = self.service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])
        
        for label in labels:
            if label['name'] == label_name:
                return label['id']
        
        # Create the label if it doesn't exist
        label_object = {
            'name': label_name,
            'labelListVisibility': 'labelShow',
            'messageListVisibility': 'show'
        }
        
        created_label = self.service.users().labels().create(
            userId='me', body=label_object
        ).execute()
        
        return created_label['id']
    
    def apply_label(self, message_id, label_name):
        """Apply a label to a message, creating the label if needed"""
        if not self.service:
            raise Exception("Gmail API service not initialized")
        
        # Get or create the label
        label_id = self.create_label(label_name)
        
        # Apply the label to the message
        self.service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'addLabelIds': [label_id]}
        ).execute()
        
        return label_id

# Example usage
if __name__ == "__main__":
    client = GmailClient()
    messages = client.get_unread_messages(max_results=5)
    
    for msg in messages:
        message = client.get_message_details(msg['id'])
        subject = client.get_header(message, 'Subject')
        sender = client.get_header(message, 'From')
        
        print(f"From: {sender}")
        print(f"Subject: {subject}")
        print("---")