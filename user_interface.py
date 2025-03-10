import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from email_processor import EmailProcessor

class GmailAIFilterUI:
    def __init__(self, root):
        """Initialize the user interface"""
        self.root = root
        self.root.title("Gmail AI Filter")
        self.root.geometry("800x600")
        self.root.minsize(800, 600)
        
        # Initialize the email processor
        self.email_processor = EmailProcessor()
        
        # Create UI elements
        self._create_widgets()
        
        # Processing flag
        self.is_processing = False
        
        # Auto-refresh thread
        self.auto_refresh_enabled = False
        self.auto_refresh_thread = None
    
    def _create_widgets(self):
        """Create all UI widgets"""
        # Create main frame
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create control frame
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Process button
        self.process_button = ttk.Button(control_frame, text="Process Unread Emails", command=self.process_emails)
        self.process_button.pack(side=tk.LEFT, padx=5)
        
        # Email count selection
        email_count_frame = ttk.Frame(control_frame)
        email_count_frame.pack(side=tk.LEFT, padx=10)
        
        # Add a label
        ttk.Label(email_count_frame, text="Emails to process:").pack(side=tk.LEFT)
        
        # Create a variable to store the number of emails
        self.email_count_var = tk.StringVar(value="20")  # Default value
        
        # Create a spinbox for selecting number of emails
        self.email_count_spinbox = ttk.Spinbox(
            email_count_frame,
            from_=1,
            to=500,
            width=5,
            textvariable=self.email_count_var
        )
        self.email_count_spinbox.pack(side=tk.LEFT, padx=5)
        
        # Auto-refresh checkbox
        self.auto_refresh_var = tk.BooleanVar(value=False)
        self.auto_refresh_check = ttk.Checkbutton(
            control_frame, 
            text="Auto-refresh (5 min)", 
            variable=self.auto_refresh_var,
            command=self.toggle_auto_refresh
        )
        self.auto_refresh_check.pack(side=tk.LEFT, padx=5)
        
        # Retrain model button
        self.retrain_button = ttk.Button(control_frame, text="Retrain Model", command=self.retrain_model)
        self.retrain_button.pack(side=tk.LEFT, padx=5)
        
        # Stats button
        self.stats_button = ttk.Button(control_frame, text="View Stats", command=self.show_stats)
        self.stats_button.pack(side=tk.LEFT, padx=5)
        
        # Status label
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(control_frame, textvariable=self.status_var)
        self.status_label.pack(side=tk.RIGHT, padx=5)
        
        # Create notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Recent emails tab
        self.emails_frame = ttk.Frame(notebook)
        notebook.add(self.emails_frame, text="Recent Emails")
        
        # Create treeview for emails
        columns = ("sender", "subject", "importance", "spam", "action")
        self.emails_tree = ttk.Treeview(self.emails_frame, columns=columns, show="headings")
        
        # Define headings
        self.emails_tree.heading("sender", text="Sender")
        self.emails_tree.heading("subject", text="Subject")
        self.emails_tree.heading("importance", text="Importance")
        self.emails_tree.heading("spam", text="Spam")
        self.emails_tree.heading("action", text="Action")
        
        # Define columns
        self.emails_tree.column("sender", width=150)
        self.emails_tree.column("subject", width=300)
        self.emails_tree.column("importance", width=100, anchor=tk.CENTER)
        self.emails_tree.column("spam", width=100, anchor=tk.CENTER)
        self.emails_tree.column("action", width=100, anchor=tk.CENTER)
        
        # Create scrollbar
        emails_scrollbar = ttk.Scrollbar(self.emails_frame, orient=tk.VERTICAL, command=self.emails_tree.yview)
        self.emails_tree.configure(yscroll=emails_scrollbar.set)
        
        # Pack treeview and scrollbar
        self.emails_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        emails_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind double click event
        self.emails_tree.bind("<Double-1>", self.on_email_double_click)
        
        # Feedback frame (at the bottom)
        feedback_frame = ttk.LabelFrame(main_frame, text="Feedback", padding=10)
        feedback_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Feedback instructions
        feedback_label = ttk.Label(feedback_frame, 
                                   text="Double-click on an email to provide feedback and improve the AI model.")
        feedback_label.pack(fill=tk.X)
    
    def process_emails(self):
        """Process unread emails from Gmail inbox"""
        if self.is_processing:
            return
        
        try:
            # Get the number of emails to process
            email_count = int(self.email_count_var.get())
            # Validate the input
            if email_count < 1:
                email_count = 1
            elif email_count > 500:
                email_count = 500
        except ValueError:
            # If invalid input, use default
            email_count = 20
            self.email_count_var.set("20")
            
        self.is_processing = True
        self.status_var.set(f"Processing up to {email_count} unread emails...")
        self.process_button.configure(state=tk.DISABLED)
        
        # Run in a separate thread to avoid blocking the UI
        threading.Thread(target=self._process_emails_thread, args=(email_count,), daemon=True).start()
    
    def _process_emails_thread(self, email_count):
        """Background thread for processing emails"""
        try:
            # Process up to specified number of unread emails
            results = self.email_processor.process_unread_emails(max_emails=email_count)
            
            # Update the UI in the main thread
            self.root.after(0, lambda: self._update_emails_list(results))
            
        except Exception as e:
            # Show error message in the main thread
            self.root.after(0, lambda: messagebox.showerror("Error", f"An error occurred: {str(e)}"))
        finally:
            # Re-enable the process button in the main thread
            self.root.after(0, lambda: self._processing_complete())
    
    def _processing_complete(self):
        """Called when email processing is complete"""
        self.is_processing = False
        self.status_var.set("Ready")
        self.process_button.configure(state=tk.NORMAL)
    
    def _update_emails_list(self, results):
        """Update the emails treeview with processing results"""
        # Clear existing items
        for item in self.emails_tree.get_children():
            self.emails_tree.delete(item)
        
        # Add new items
        for result in results:
            # Format the importance score as a percentage
            importance = f"{result['importance_score']:.0%}"
            
            _, spam_score = self.email_processor.email_classifier.predict_spam_likelihood(
            self.email_processor.extract_email_features(
                self.email_processor.gmail_client.get_message_details(result['message_id'])
                )
            )   
            spam = f"{spam_score:.0%}"

            # Add the item to the treeview
            self.emails_tree.insert(
                "", 
                tk.END, 
                values=(
                    result['sender'], 
                    result['subject'], 
                    importance, 
                    spam,
                    result['action']
                ),
                tags=(result['message_id'],)
            )
        
        # Set status message
        if results:
            self.status_var.set(f"Processed {len(results)} emails")
        else:
            self.status_var.set("No new emails to process")
    
    def on_email_double_click(self, event):
        """Handle double-clicking on an email in the list"""
        # Get the selected item
        selection = self.emails_tree.selection()
        if not selection:
            return
        
        # Get the item values
        item = self.emails_tree.item(selection[0])
        values = item['values']
        
        # Get the message ID from tags
        message_id = self.emails_tree.item(selection[0], 'tags')[0]
        
        # Show feedback dialog
        self._show_feedback_dialog(message_id, values)
    
    def _show_feedback_dialog(self, message_id, values):
        """Show dialog for providing feedback on an email"""
        sender, subject, importance, spam, action = values
        
        # Create a dialog window
        dialog = tk.Toplevel(self.root)
        dialog.title("Email Feedback")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Make dialog modal
        dialog.focus_set()
        
        # Create dialog content
        frame = ttk.Frame(dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Email info
        ttk.Label(frame, text=f"From: {sender}").pack(anchor=tk.W)
        ttk.Label(frame, text=f"Subject: {subject}").pack(anchor=tk.W)
        ttk.Label(frame, text=f"AI classified as: {importance} important").pack(anchor=tk.W, pady=(10, 0))
        ttk.Label(frame, text="Was this email actually important?").pack(anchor=tk.W, pady=(10, 0))
        
        # Feedback buttons
        buttons_frame = ttk.Frame(frame)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(
            buttons_frame, 
            text="Yes, Important", 
            command=lambda: self._submit_feedback(dialog, message_id, True)
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            buttons_frame, 
            text="No, Not Important", 
            command=lambda: self._submit_feedback(dialog, message_id, False)
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            buttons_frame, 
            text="Cancel", 
            command=dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)
    
    def _submit_feedback(self, dialog, message_id, is_important):
        """Submit user feedback for an email"""
        # Provide feedback to the email processor
        success = self.email_processor.provide_feedback(message_id, is_important)
        
        if success:
            messagebox.showinfo("Feedback Submitted", 
                               "Thank you for your feedback. This will help improve the AI model.")
        else:
            messagebox.showerror("Error", "Failed to submit feedback.")
        
        # Close the dialog
        dialog.destroy()
    
    def retrain_model(self):
        """Retrain the AI model with accumulated feedback"""
        self.status_var.set("Retraining model...")
        
        # Run in a separate thread
        threading.Thread(target=self._retrain_model_thread, daemon=True).start()
    
    def _retrain_model_thread(self):
        """Background thread for retraining the model"""
        try:
            success = self.email_processor.retrain_model()
            
            # Update the UI in the main thread
            if success:
                self.root.after(0, lambda: messagebox.showinfo("Model Retrained", 
                                                             "The AI model has been successfully retrained."))
            else:
                self.root.after(0, lambda: messagebox.showinfo("Not Enough Data", 
                                                             "Not enough training examples to retrain the model."))
            
        except Exception as e:
            # Show error message in the main thread
            self.root.after(0, lambda: messagebox.showerror("Error", f"An error occurred: {str(e)}"))
        finally:
            # Update status
            self.root.after(0, lambda: self.status_var.set("Ready"))
    
    def show_stats(self):
        """Show application statistics"""
        stats = self.email_processor.get_stats()
        
        # Create a dialog window
        dialog = tk.Toplevel(self.root)
        dialog.title("Application Statistics")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        
        # Create dialog content
        frame = ttk.Frame(dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Stats
        ttk.Label(frame, text="Email Statistics:", font=("", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        ttk.Label(frame, text=f"Processed Emails: {stats['processed_emails']}").pack(anchor=tk.W)
        ttk.Label(frame, text=f"Unique Senders: {stats['unique_senders']}").pack(anchor=tk.W)
        
        # Actions breakdown
        if 'actions' in stats and stats['actions']:
            ttk.Label(frame, text="\nActions Taken:", font=("", 10, "bold")).pack(anchor=tk.W, pady=(10, 5))
            for action, count in stats['actions'].items():
                ttk.Label(frame, text=f"{action.capitalize()}: {count}").pack(anchor=tk.W)
        
        # Model stats
        if 'model_stats' in stats and stats['model_stats']:
            ms = stats['model_stats']
            ttk.Label(frame, text="\nModel Training:", font=("", 10, "bold")).pack(anchor=tk.W, pady=(10, 5))
            ttk.Label(frame, text=f"Training Examples: {ms.get('total_examples', 0)}").pack(anchor=tk.W)
            
            if 'important_count' in ms and 'unimportant_count' in ms:
                ttk.Label(frame, text=f"Important Emails: {ms['important_count']}").pack(anchor=tk.W)
                ttk.Label(frame, text=f"Not Important Emails: {ms['unimportant_count']}").pack(anchor=tk.W)
            
            if 'important_ratio' in ms:
                ratio = ms['important_ratio'] * 100
                ttk.Label(frame, text=f"Important Email Ratio: {ratio:.1f}%").pack(anchor=tk.W)
        
        # Close button
        ttk.Button(frame, text="Close", command=dialog.destroy).pack(pady=(15, 0))
    
    def toggle_auto_refresh(self):
        """Toggle the auto-refresh feature"""
        if self.auto_refresh_var.get():
            # Start auto-refresh
            self.auto_refresh_enabled = True
            self.auto_refresh_thread = threading.Thread(target=self._auto_refresh_loop, daemon=True)
            self.auto_refresh_thread.start()
        else:
            # Stop auto-refresh
            self.auto_refresh_enabled = False
    
    def _auto_refresh_loop(self):
        """Background thread for auto-refreshing"""
        while self.auto_refresh_enabled:
            # Wait for 5 minutes
            for _ in range(300):  # 300 seconds = 5 minutes
                if not self.auto_refresh_enabled:
                    break
                time.sleep(1)
            
            # Process emails if auto-refresh is still enabled
            if self.auto_refresh_enabled and not self.is_processing:
                try:
                    # Get the number of emails to process from the spinbox
                    email_count = int(self.email_count_var.get())
                    if email_count < 1 or email_count > 500:
                        email_count = 20
                except ValueError:
                    email_count = 20
                
                # Process emails with the current count setting
                self.root.after(0, self.process_emails)