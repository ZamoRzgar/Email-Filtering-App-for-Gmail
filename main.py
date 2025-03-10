import os
import tkinter as tk
from tkinter import ttk, messagebox
import sys
from user_interface import GmailAIFilterUI

def check_dependencies():
    """Check if all required dependencies are installed"""
    # Map from pip package name to actual import module
    package_imports = {
        'google-api-python-client': 'googleapiclient',
        'google-auth-httplib2': 'google_auth_httplib2',
        'google-auth-oauthlib': 'google_auth_oauthlib',
        'tensorflow': 'tensorflow',
        'scikit-learn': 'sklearn',
        'pandas': 'pandas',
        'numpy': 'numpy'
    }
    
    missing_packages = []
    
    for package, import_name in package_imports.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package)
    
    return missing_packages

def setup_app():
    """Initialize the application directories"""
    # Create necessary directories
    os.makedirs('app_data', exist_ok=True)
    os.makedirs('model_data', exist_ok=True)
    
    # Check for credentials file
    if not os.path.exists('credentials.json'):
        messagebox.showerror(
            "Missing Credentials", 
            "credentials.json file not found. Please download the OAuth credentials file from Google Cloud Console."
        )
        return False
    
    return True

def main():
    """Main application entry point"""
    # Check dependencies
    missing_packages = check_dependencies()
    if missing_packages:
        print("Error: Missing required packages:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\nPlease install these packages using:")
        print(f"pip install {' '.join(missing_packages)}")
        return 1
    
    # Check application setup
    if not setup_app():
        return 1
    
    # Create the main window
    root = tk.Tk()
    root.style = ttk.Style()
    
    # Try to set a modern theme if available
    try:
        if 'clam' in root.style.theme_names():
            root.style.theme_use('clam')
    except:
        pass
    
    # Create the application UI
    app = GmailAIFilterUI(root)
    
    # Start the application
    root.mainloop()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())