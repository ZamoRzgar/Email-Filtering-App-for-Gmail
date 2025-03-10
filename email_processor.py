import os
import json
from datetime import datetime
from gmail_client import GmailClient
from ai_model import EmailClassifier

class EmailProcessor:
    def __init__(self, data_dir='app_data'):
        """Initialize the email processor"""
        self.data_dir = data_dir
        self.sender_history_path = os.path.join(data_dir, 'sender_history.json')
        self.processed_emails_path = os.path.join(data_dir, 'processed_emails.json')
        
        # Create data directory if it doesn't exist
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        # Initialize components
        self.gmail_client = GmailClient()
        self.email_classifier = EmailClassifier()
        
        # Load sender history
        self.sender_history = self._load_sender_history()
        
        # Load processed emails record
        self.processed_emails = self._load_processed_emails()
    
    def _load_sender_history(self):
        """Load sender history from file or create a new one"""
        if os.path.exists(self.sender_history_path):
            with open(self.sender_history_path, 'r') as f:
                return json.load(f)
        else:
            return {}
    
    def _save_sender_history(self):
        """Save sender history to file"""
        with open(self.sender_history_path, 'w') as f:
            json.dump(self.sender_history, f, default=lambda o: str(o))
    
    def _load_processed_emails(self):
        """Load processed emails record from file or create a new one"""
        if os.path.exists(self.processed_emails_path):
            with open(self.processed_emails_path, 'r') as f:
                return json.load(f)
        else:
            return {}
    
    def _save_processed_emails(self):
        """Save processed emails record to file"""
        with open(self.processed_emails_path, 'w') as f:
            json.dump(self.processed_emails, f, default=lambda o: str(o))
    
    def _update_sender_history(self, sender, responded=False):
        """Update history for a sender"""
        if sender not in self.sender_history:
            self.sender_history[sender] = {
                'email_count': 0,
                'response_count': 0,
                'last_email': datetime.now().isoformat(),
                'first_seen': datetime.now().isoformat()
            }
        
        self.sender_history[sender]['email_count'] += 1
        if responded:
            self.sender_history[sender]['response_count'] += 1
        
        self.sender_history[sender]['last_email'] = datetime.now().isoformat()
        self._save_sender_history()
    
    def get_sender_statistics(self, sender):
        """Get statistics for a specific sender"""
        if sender not in self.sender_history:
            return {
                'email_count': 0,
                'response_count': 0,
                'response_rate': 0.0
            }
        
        data = self.sender_history[sender]
        email_count = data['email_count']
        response_count = data['response_count']
        
        return {
            'email_count': email_count,
            'response_count': response_count,
            'response_rate': response_count / email_count if email_count > 0 else 0.0
        }
    
    def extract_email_features(self, message):
        """Extract features from a Gmail message"""
        # Get message ID
        message_id = message['id']
        
        # Get message details
        sender = self.gmail_client.get_header(message, 'From')
        subject = self.gmail_client.get_header(message, 'Subject')
        date = self.gmail_client.get_header(message, 'Date')
        body = self.gmail_client.get_email_body(message)
        
        # Check for unsubscribe text
        contains_unsubscribe = 'unsubscribe' in body.lower()
        
        # Get sender statistics
        sender_stats = self.get_sender_statistics(sender)
        
        return {
            'message_id': message_id,
            'sender': sender,
            'subject': subject,
            'date': date,
            'body': body,
            'contains_unsubscribe': contains_unsubscribe,
            'sender_frequency': sender_stats['email_count'],
            'user_response_rate': sender_stats['response_rate']
        }
    
    def process_unread_emails(self, max_emails=200):
        """Process unread emails from Gmail inbox"""
        # Get unread messages (increased limit)
        unread_messages = self.gmail_client.get_unread_messages(max_results=max_emails)
        
        if not unread_messages:
            return []
        
        results = []
        
        # Create a progress counter
        total_emails = len(unread_messages)
        processed = 0
        
        for msg in unread_messages:
            # Skip already processed emails
            if msg['id'] in self.processed_emails:
                continue
            
            # Get full message details
            message = self.gmail_client.get_message_details(msg['id'])
            
            # Extract features
            email_features = self.extract_email_features(message)
            
            # Predict importance
            is_important, importance_score = self.email_classifier.predict_importance(email_features)
            
            # Take action based on prediction
            action = self._take_action(
                message_id=email_features['message_id'],
                is_important=is_important,
                contains_unsubscribe=email_features['contains_unsubscribe']
            )
            
            # Update sender history
            self._update_sender_history(email_features['sender'])
            
            # Record the processed email
            self.processed_emails[email_features['message_id']] = {
                'timestamp': datetime.now().isoformat(),
                'is_important': is_important,
                'importance_score': importance_score,
                'action': action
            }
            
            # Save periodically (every 10 emails)
            processed += 1
            if processed % 10 == 0:
                self._save_processed_emails()
            
            # Collect results
            results.append({
                'message_id': email_features['message_id'],
                'sender': email_features['sender'],
                'subject': email_features['subject'],
                'is_important': is_important,
                'importance_score': importance_score,
                'action': action
            })
        
        # Final save
        self._save_processed_emails()
        
        return results
    
    def _take_action(self, message_id, is_important, contains_unsubscribe):
        """Take action on an email based on its classification"""
        # First check if it's spam
        message = self.gmail_client.get_message_details(message_id)
        email_features = self.extract_email_features(message)
        
        # Get spam prediction
        is_spam, spam_score = self.email_classifier.predict_spam_likelihood(email_features)
        
        if is_spam:
            # Move to spam folder
            self.gmail_client.mark_as_spam(message_id)
            return "marked_spam"
        elif not is_important and contains_unsubscribe:
            # Move to trash for newsletters that are not important
            self.gmail_client.trash_message(message_id)
            return "trashed"
        elif is_important:
            # Mark important emails
            self.gmail_client.mark_as_important(message_id)
            self.gmail_client.apply_label(message_id, "AI-Important")
            return "marked_important"
        else:
            # Archive other emails
            self.gmail_client.archive_message(message_id)
            return "archived"
    
    def provide_feedback(self, message_id, is_actually_important):
        """Provide feedback to train the model"""
        if message_id not in self.processed_emails:
            return False
        
        # Get the message details
        message = self.gmail_client.get_message_details(message_id)
        
        # Extract features
        email_features = self.extract_email_features(message)
        
        # Add training example
        self.email_classifier.add_training_example(email_features, is_actually_important)
        
        # Update the processed email record
        self.processed_emails[message_id]['user_feedback'] = is_actually_important
        self.processed_emails[message_id]['feedback_time'] = datetime.now().isoformat()
        self._save_processed_emails()
        
        # If the user indicated this sender is important, update the response rate
        sender = email_features['sender']
        if is_actually_important and sender in self.sender_history:
            self._update_sender_history(sender, responded=True)
        
        return True
    
    def retrain_model(self):
        """Retrain the model with accumulated feedback"""
        return self.email_classifier.retrain_model()
    
    def get_stats(self):
        """Get application statistics"""
        # Count the number of emails in each action category
        actions = {}
        for email_id, data in self.processed_emails.items():
            action = data['action']
            if action in actions:
                actions[action] += 1
            else:
                actions[action] = 1
        
        # Get model training stats
        model_stats = self.email_classifier.get_training_stats()
        
        # Count unique senders
        unique_senders = len(self.sender_history)
        
        return {
            'processed_emails': len(self.processed_emails),
            'actions': actions,
            'unique_senders': unique_senders,
            'model_stats': model_stats
        }

# Example usage
if __name__ == "__main__":
    processor = EmailProcessor()
    
    # Process unread emails
    results = processor.process_unread_emails(max_emails=10)
    
    # Print results
    for result in results:
        print(f"Email: {result['subject']}")
        print(f"From: {result['sender']}")
        print(f"Importance score: {result['importance_score']:.2f}")
        print(f"Action taken: {result['action']}")
        print("---")
    
    # Print stats
    stats = processor.get_stats()
    print(f"Processed emails: {stats['processed_emails']}")
    print(f"Unique senders: {stats['unique_senders']}")