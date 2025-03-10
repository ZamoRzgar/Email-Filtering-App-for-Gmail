import os
import numpy as np
import tensorflow as tf
from sklearn.feature_extraction.text import TfidfVectorizer
import pickle
from datetime import datetime
import json

class EmailClassifier:
    def __init__(self, model_dir='model_data'):
        """Initialize the email classifier model"""
        self.model_dir = model_dir
        self.vectorizer_path = os.path.join(model_dir, 'vectorizer.pkl')
        self.model_path = os.path.join(model_dir, 'email_model')
        
        # Create model directory if it doesn't exist
        if not os.path.exists(model_dir):
            os.makedirs(model_dir)
        
        # Initialize the vectorizer
        self.vectorizer = self._load_or_create_vectorizer()
        
        # Initialize the model
        self.model = self._load_or_create_model()
        
        # Training data storage
        self.training_data_path = os.path.join(model_dir, 'training_data.json')
        self.training_data = self._load_training_data()
    
    def _load_or_create_vectorizer(self):
        """Load the existing TF-IDF vectorizer or create a new one"""
        if os.path.exists(self.vectorizer_path):
            with open(self.vectorizer_path, 'rb') as f:
                return pickle.load(f)
        else:
            # Create a new vectorizer with reasonable defaults for emails
            return TfidfVectorizer(
                max_features=5000,
                stop_words='english',
                min_df=2,
                max_df=0.95
            )
    
    def _load_or_create_model(self):
        """Load the existing model or create a new one"""
        if os.path.exists(self.model_path):
            return tf.keras.models.load_model(self.model_path)
        else:
            # Create a new model
            model = tf.keras.Sequential([
                # Input shape will be vectorized text + additional features
                # 5000 (TF-IDF features) + 3 (custom features)
                tf.keras.layers.Dense(256, activation='relu', input_shape=(5003,)),
                tf.keras.layers.Dropout(0.3),
                tf.keras.layers.Dense(128, activation='relu'),
                tf.keras.layers.Dropout(0.3),
                tf.keras.layers.Dense(64, activation='relu'),
                tf.keras.layers.Dense(1, activation='sigmoid')
            ])
            
            model.compile(
                optimizer='adam',
                loss='binary_crossentropy',
                metrics=['accuracy']
            )
            
            return model
    
    def _load_training_data(self):
        """Load existing training data or initialize an empty list"""
        if os.path.exists(self.training_data_path):
            with open(self.training_data_path, 'r') as f:
                return json.load(f)
        else:
            return []
    
    def _save_training_data(self):
        """Save the current training data to disk"""
        with open(self.training_data_path, 'w') as f:
            json.dump(self.training_data, f)
    
    def _save_vectorizer(self):
        """Save the current vectorizer to disk"""
        with open(self.vectorizer_path, 'wb') as f:
            pickle.dump(self.vectorizer, f)
    
    def _save_model(self):
        """Save the current model to disk"""
        self.model.save(self.model_path)
    
    def fit_vectorizer(self, email_bodies):
        """Fit the vectorizer on a corpus of email bodies"""
        self.vectorizer.fit(email_bodies)
        self._save_vectorizer()
    
    def vectorize_text(self, email_body):
        """Convert email body text to TF-IDF vector"""
        # Check if the vectorizer is already fitted
        if not hasattr(self.vectorizer, 'vocabulary_'):
            # If not fitted, we'll return zeros for now
            # In a real application, you'd want to handle this better
            return np.zeros(5000)
        
        # Transform the text to a TF-IDF vector
        text_vector = self.vectorizer.transform([email_body]).toarray()[0]
        return text_vector
    
    def prepare_features(self, email_data):
        """
        Prepare feature vector for prediction
        
        email_data: Dictionary containing:
            - body: email body text
            - contains_unsubscribe: boolean, True if email contains "unsubscribe"
            - sender_frequency: int, how many emails received from this sender
            - user_response_rate: float, rate at which user responds to this sender
        """
        # Vectorize the email body
        text_vector = self.vectorize_text(email_data['body'])
        
        # Create additional features
        additional_features = np.array([
            1 if email_data['contains_unsubscribe'] else 0,
            email_data['sender_frequency'],
            email_data['user_response_rate']
        ])
        
        # Combine all features
        features = np.hstack([text_vector, additional_features])
        
        return features
    
    def predict_spam_likelihood(self, email_data):
        """
        Predict whether an email is likely spam based on features
        This is a simplified approach - in a real app you'd train a dedicated spam model
        """
        # Spam indicators (simple heuristics)
        spam_score = 0.0
        
        # Check for common spam indicators in the body
        body = email_data['body'].lower()
        spam_phrases = [
            "you've won", "congratulations! you won", "lottery winner", 
            "million dollars", "nigeria", "inheritance", "wire transfer",
            "bank details", "urgent business", "forex", "investment opportunity",
            "unclaimed", "hot singles", "meet singles", "enlargement", "viagra",
            "pharmacy", "pills", "discount meds", "casino", "betting", "gambling"
        ]
        
        for phrase in spam_phrases:
            if phrase in body:
                spam_score += 0.2  # Each spam phrase increases the score
        
        # Cap the score at 1.0
        spam_score = min(spam_score, 1.0)
        
        # Return boolean classification and score
        is_spam = spam_score > 0.3  # Threshold for spam classification
        
        return is_spam, spam_score

    def predict_importance(self, email_data):
        """
        Predict whether an email is important
        
        Returns: (is_important, importance_score)
            - is_important: boolean classification
            - importance_score: float confidence score (0-1)
        """
        features = self.prepare_features(email_data)
        
        # Make prediction
        score = self.model.predict(features.reshape(1, -1))[0][0]
        
        # Threshold for classification (can be tuned)
        is_important = score > 0.5
        
        return is_important, float(score)
    
    def add_training_example(self, email_data, is_important):
        """
        Add a new training example
        
        email_data: Same format as in prepare_features
        is_important: Boolean indicating if the email is important
        """
        # Get features
        features = self.prepare_features(email_data)
        
        # Store email data with user feedback
        example = {
            'features': features.tolist(),
            'is_important': is_important,
            'timestamp': datetime.now().isoformat()
        }
        
        self.training_data.append(example)
        self._save_training_data()
    
    def retrain_model(self, min_examples=20):
        """
        Retrain the model with accumulated training data
        
        min_examples: Minimum number of training examples required
        
        Returns: True if model was retrained, False otherwise
        """
        if len(self.training_data) < min_examples:
            return False
        
        # Prepare training data
        X = np.array([example['features'] for example in self.training_data])
        y = np.array([1 if example['is_important'] else 0 for example in self.training_data])
        
        # Retrain the model
        history = self.model.fit(
            X, y,
            epochs=15,
            batch_size=8,
            validation_split=0.2,
            verbose=1
        )
        
        # Save the retrained model
        self._save_model()
        
        return True
    
    def get_training_stats(self):
        """Return statistics about the training data"""
        total = len(self.training_data)
        
        if total == 0:
            return {
                'total_examples': 0,
                'important_ratio': 0,
                'last_retrain': None
            }
        
        important_count = sum(1 for example in self.training_data if example['is_important'])
        
        # Sort by timestamp and get the most recent
        self.training_data.sort(key=lambda x: x['timestamp'])
        last_timestamp = self.training_data[-1]['timestamp']
        
        return {
            'total_examples': total,
            'important_count': important_count,
            'unimportant_count': total - important_count,
            'important_ratio': important_count / total,
            'last_example_added': last_timestamp
        }

# Example usage
if __name__ == "__main__":
    classifier = EmailClassifier()
    
    # Example email data
    sample_email = {
        'body': "Hello, we have a special offer for you. Click here to unsubscribe if you don't want to receive these emails.",
        'contains_unsubscribe': True,
        'sender_frequency': 5,
        'user_response_rate': 0.1
    }
    
    # Make a prediction
    is_important, score = classifier.predict_importance(sample_email)
    print(f"Is important: {is_important}, Score: {score:.2f}")
    
    # Add as training example
    classifier.add_training_example(sample_email, is_important=False)
    
    # Get stats
    stats = classifier.get_training_stats()
    print(f"Training examples: {stats['total_examples']}")