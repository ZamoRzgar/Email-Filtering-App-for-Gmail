# Gmail AI Filter

An intelligent email filtering application that uses machine learning to automatically organize your Gmail inbox based on importance and content.



## Features

- **AI-Powered Filtering**: Automatically determines email importance using machine learning
- **Smart Actions**: Archives, marks as important, or trashes emails based on AI analysis
- **Newsletter Detection**: Automatically identifies and handles subscription emails with "unsubscribe" links
- **Spam Detection**: Identifies potential spam and moves it to the spam folder
- **Sender History Tracking**: Learns from your interaction patterns with senders
- **User Feedback**: Continuously improves through your feedback
- **Auto-refresh**: Option to automatically process new emails every 5 minutes

## Installation

### Prerequisites

- Python 3.8 or higher
- A Google account with Gmail
- Google Cloud project with Gmail API enabled

### Step 1: Clone the repository

```bash
git clone https://github.com/zamorzgar/gmail-ai-filter.git
cd gmail-ai-filter
```

### Step 2: Set up a virtual environment (recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python -m venv venv
source venv/bin/activate
```

### Step 3: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Set up Google Cloud project and enable Gmail API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Navigate to "APIs & Services" > "Library"
4. Search for "Gmail API" and enable it
5. Go to "APIs & Services" > "OAuth consent screen"
   - Select "External" (or "Internal" if you have Google Workspace)
   - Fill in the required information
   - Add the scope `https://www.googleapis.com/auth/gmail.modify` 
   - Add your email as a test user
6. Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Select "Desktop app" as the application type
   - Download the JSON file

### Step 5: Configure the application

1. Rename the downloaded JSON file to `credentials.json`
2. Place `credentials.json` in the project's root directory

## Usage

### First Run

1. Run the application
   ```bash
   python main.py
   ```
2. A browser window will open, asking you to log in to your Google account
3. Grant the requested permissions
4. The application will create a `token.pickle` file to store your credentials

### Main Features

- **Process Unread Emails**: Click this button to process all unread emails in your inbox
- **Auto-refresh**: Enable this checkbox to automatically process new emails every 5 minutes
- **Retrain Model**: After providing feedback, click this to improve the AI model
- **View Stats**: View statistics about processed emails and model training

### Providing Feedback

1. Double-click on any email in the list
2. A dialog will appear
3. Select whether the email was actually important or not
4. This feedback will be used to improve the AI model

### Retraining the Model

After providing feedback on 20 or more emails:
1. Click "Retrain Model"
2. The model will update based on your feedback
3. Future email processing will use the improved model

## How It Works

1. **Authentication**: Securely connects to your Gmail account using OAuth
2. **Email Analysis**: Extracts features from emails (content, sender, patterns)
3. **AI Classification**: Uses a TensorFlow model to predict importance and detect spam
4. **Automated Actions**: 
   - Important emails: Labeled as "AI-Important"
   - Unimportant newsletters: Moved to trash
   - Potential spam: Moved to spam folder
   - Other emails: Archived
5. **Learning**: Improves over time based on your feedback

## Customization

You can customize the application by modifying these files:

- `ai_model.py`: Adjust the AI model architecture or features
- `email_processor.py`: Change how emails are processed
- `user_interface.py`: Modify the user interface

## Privacy & Security

- Your email data never leaves your computer
- Authentication is handled securely through Google OAuth
- No email content is shared with third parties
- The application runs locally on your machine

## Troubleshooting

### Authentication Issues

If you encounter authentication problems:
1. Delete the `token.pickle` file
2. Restart the application
3. Go through the OAuth flow again

### Gmail API Quota Limits

The Gmail API has usage limits. If you hit them:
1. Reduce the frequency of auto-refresh
2. Process fewer emails at once

### Package Installation Issues

If you have trouble installing the required packages:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Google API Python Client](https://github.com/googleapis/google-api-python-client)
- [TensorFlow](https://www.tensorflow.org/)
- [scikit-learn](https://scikit-learn.org/)
