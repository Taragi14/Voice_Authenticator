import os
from flask import Flask, render_template
import tkinter as tk
import threading
from ui import VoiceAuthUI
from auth import AuthHandler
from database import init_db

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key')  # Use environment variable for security

# Initialize database
init_db()

# Initialize Tkinter, AuthHandler, and VoiceAuthUI
root = tk.Tk()
auth_handler = AuthHandler()
voice_app = VoiceAuthUI(root, auth_handler, theme="darkly")

@app.route('/success')
def success():
    return render_template('success.html')

if __name__ == '__main__':
    # Start Flask server in a separate thread
    flask_thread = threading.Thread(target=lambda: app.run(debug=False, use_reloader=False), daemon=True)
    flask_thread.start()
    # Start Tkinter GUI
    root.mainloop()