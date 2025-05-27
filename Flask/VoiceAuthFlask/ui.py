import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledText
from ttkbootstrap.tooltip import ToolTip
from tkinter import messagebox, StringVar, Toplevel
import threading
import time

class VoiceAuthUI:
    def __init__(self, root, auth_handler=None, theme="darkly"):
        self.root = root
        self.auth_handler = auth_handler
        self.style = ttk.Style(theme=theme)
        self.root.title("Voice Authentication System")
        self.root.geometry("450x350")
        self.root.resizable(False, False)
        self.running = False

        # Configure custom radio button style
        self.style.configure("Custom.TRadiobutton", font=("Arial", 12), foreground="#ffffff", background="#212529")

        # Main Window GUI
        self.main_frame = ttk.Frame(self.root, padding=20, bootstyle="dark")
        self.main_frame.pack(fill="both", expand=True)

        # Header
        ttk.Label(self.main_frame, text="Voice Authentication System", font=("Arial", 18, "bold"), bootstyle="light").pack(pady=(0, 20))

        # Action Selection Frame
        action_frame = ttk.LabelFrame(self.main_frame, text="Select Action", padding=10, bootstyle="primary")
        action_frame.pack(fill="x", pady=10)

        self.action_var = StringVar(value="signup")
        self.signup_radio = ttk.Radiobutton(action_frame, text="Signup (New User)", variable=self.action_var, value="signup", 
                                           style="Custom.TRadiobutton")
        self.signup_radio.pack(anchor="w", pady=5)
        ToolTip(self.signup_radio, text="Register a new user with voice samples and a secret phrase.")

        self.login_radio = ttk.Radiobutton(action_frame, text="Login (Existing User)", variable=self.action_var, value="login", 
                                          style="Custom.TRadiobutton")
        self.login_radio.pack(anchor="w", pady=5)
        ToolTip(self.login_radio, text="Authenticate using your voice and secret phrase.")

        self.forgot_radio = ttk.Radiobutton(action_frame, text="Forgot Password (Reset Setup)", variable=self.action_var, value="forgot", 
                                           style="Custom.TRadiobutton")
        self.forgot_radio.pack(anchor="w", pady=5)
        ToolTip(self.forgot_radio, text="Reset your voice and phrase setup using OTP verification.")

        # Proceed Button
        self.proceed_button = ttk.Button(self.main_frame, text="Proceed", command=self.open_action_window, bootstyle="primary-outline", width=15)
        self.proceed_button.pack(pady=20)
        ToolTip(self.proceed_button, text="Open the selected action window.")

        # Status Label
        self.status_label = ttk.Label(self.main_frame, text="Select an action to proceed.", font=("Arial", 10), bootstyle="light")
        self.status_label.pack(pady=10)

    def open_action_window(self):
        """Open a new window based on selected action and hide the main window."""
        if self.running:
            messagebox.showwarning("Warning", "Another process is running. Please wait.", parent=self.root)
            return

        action = self.action_var.get()
        self.root.withdraw()

        action_window = Toplevel()
        action_window.resizable(True, True)
        action_window.geometry("900x750")
        action_window.configure(bg="#212529")  # Match dark theme
        action_window.protocol("WM_DELETE_WINDOW", lambda: self.close_action_window(action_window))

        if action == "signup":
            action_window.title("Signup - Voice Authentication")
            self.setup_signup_window(action_window)
        elif action == "forgot":
            action_window.title("Forgot Password - Reset Voice Setup")
            self.setup_forgot_window(action_window)
        else:
            action_window.title("Login - Voice Authentication")
            self.setup_login_window(action_window)

    def close_action_window(self, window):
        """Close the action window and show the main window."""
        self.running = False
        if window.winfo_exists():
            window.destroy()
        self.root.deiconify()

    def setup_signup_window(self, window):
        """Setup the Signup window."""
        frame = ttk.Frame(window, padding=20, bootstyle="dark")
        frame.pack(fill="both", expand=True)

        # Header
        ttk.Label(frame, text="Signup - Voice Authentication", font=("Arial", 20, "bold"), bootstyle="light").pack(pady=(0, 20))

        # Email Input Frame
        email_frame = ttk.LabelFrame(frame, text="User Information", padding=10, bootstyle="primary")
        email_frame.pack(fill="x", pady=10)

        email_var = StringVar()
        ttk.Label(email_frame, text="Email:", font=("Arial", 12), bootstyle="light").pack(anchor="w", pady=5)
        email_entry = ttk.Entry(email_frame, textvariable=email_var, width=50, bootstyle="primary")
        email_entry.pack(anchor="w", pady=5)
        ToolTip(email_entry, text="Enter your email address for identification.")

        # Status Area
        status_frame = ttk.LabelFrame(frame, text="Status", padding=10, bootstyle="primary")
        status_frame.pack(fill="both", expand=True, pady=10)

        status_text = ScrolledText(status_frame, height=15, width=80, font=("Arial", 10), wrap="word", bootstyle="dark", padding=5)
        status_text.pack(fill="both", expand=True)
        status_text.text.insert("end", "Enter your email and click Start Signup to record two voice samples and a secret phrase.\n")
        status_text.text.bind("<Key>", lambda e: "break")

        # Progress Bar
        progress_bar = ttk.Progressbar(frame, bootstyle="success-striped", mode="determinate", length=400)
        progress_bar.pack(pady=10)
        progress_bar.pack_forget()

        # Buttons Frame
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill="x", pady=10)

        start_button = ttk.Button(button_frame, text="Start Signup", 
                                 command=lambda: self.start_signup(email_var.get().strip(), status_text, progress_bar, window, start_button),
                                 bootstyle="success-outline", width=15)
        start_button.pack(side="left", padx=10)
        ToolTip(start_button, text="Begin the signup process.")

        cancel_button = ttk.Button(button_frame, text="Cancel", command=lambda: self.close_action_window(window), 
                                  bootstyle="danger-outline", width=15)
        cancel_button.pack(side="left", padx=10)
        ToolTip(cancel_button, text="Return to the main window.")

        # Image Label
        image_label = ttk.Label(frame, text="Intruder Photo (if captured)", font=("Arial", 10), bootstyle="light")
        image_label.pack(pady=15)
        self.image_label = image_label

    def setup_login_window(self, window):
        """Setup the Login window."""
        frame = ttk.Frame(window, padding=20, bootstyle="dark")
        frame.pack(fill="both", expand=True)

        # Header
        ttk.Label(frame, text="Login - Voice Authentication", font=("Arial", 20, "bold"), bootstyle="light").pack(pady=(0, 20))

        # Email Input Frame
        email_frame = ttk.LabelFrame(frame, text="User Information", padding=10, bootstyle="primary")
        email_frame.pack(fill="x", pady=10)

        email_var = StringVar()
        ttk.Label(email_frame, text="Email:", font=("Arial", 12), bootstyle="light").pack(anchor="w", pady=5)
        email_entry = ttk.Entry(email_frame, textvariable=email_var, width=50, bootstyle="primary")
        email_entry.pack(anchor="w", pady=5)
        ToolTip(email_entry, text="Enter your registered email address.")

        # Status Area
        status_frame = ttk.LabelFrame(frame, text="Status", padding=10, bootstyle="primary")
        status_frame.pack(fill="both", expand=True, pady=10)

        status_text = ScrolledText(status_frame, height=15, width=80, font=("Arial", 10), wrap="word", bootstyle="dark", padding=5)
        status_text.pack(fill="both", expand=True)
        status_text.text.insert("end", "Enter your email and click Start Login to record one voice sample and your secret phrase.\n")
        status_text.text.bind("<Key>", lambda e: "break")

        # Progress Bar
        progress_bar = ttk.Progressbar(frame, bootstyle="success-striped", mode="determinate", length=400)
        progress_bar.pack(pady=10)
        progress_bar.pack_forget()

        # Buttons Frame
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill="x", pady=10)

        start_button = ttk.Button(button_frame, text="Start Login", 
                                 command=lambda: self.start_login(email_var.get().strip(), status_text, progress_bar, window, start_button),
                                 bootstyle="primary-outline", width=15)
        start_button.pack(side="left", padx=10)
        ToolTip(start_button, text="Begin the login process.")

        cancel_button = ttk.Button(button_frame, text="Cancel", command=lambda: self.close_action_window(window), 
                                  bootstyle="danger-outline", width=15)
        cancel_button.pack(side="left", padx=10)
        ToolTip(cancel_button, text="Return to the main window.")

        # Image Label
        image_label = ttk.Label(frame, text="Intruder Photo (if captured)", font=("Arial", 10), bootstyle="light")
        image_label.pack(pady=15)
        self.image_label = image_label

    def setup_forgot_window(self, window):
        """Setup the Forgot Password window."""
        frame = ttk.Frame(window, padding=20, bootstyle="dark")
        frame.pack(fill="both", expand=True)

        # Header
        ttk.Label(frame, text="Reset Voice Setup", font=("Arial", 20, "bold"), bootstyle="light").pack(pady=(0, 20))

        # Email Input Frame
        email_frame = ttk.LabelFrame(frame, text="Account Recovery", padding=10, bootstyle="primary")
        email_frame.pack(fill="x", pady=10)

        email_var = StringVar()
        ttk.Label(email_frame, text="Email:", font=("Arial", 12), bootstyle="light").pack(anchor="w", pady=5)
        email_entry = ttk.Entry(email_frame, textvariable=email_var, width=50, bootstyle="primary")
        email_entry.pack(anchor="w", pady=5)
        ToolTip(email_entry, text="Enter your registered email address.")

        # Status Area
        status_frame = ttk.LabelFrame(frame, text="Status", padding=10, bootstyle="primary")
        status_frame.pack(fill="both", expand=True, pady=10)

        status_text = ScrolledText(status_frame, height=15, width=80, font=("Arial", 10), wrap="word", bootstyle="dark", padding=5)
        status_text.pack(fill="both", expand=True)
        status_text.text.insert("end", "Enter your registered email and click Reset to begin recovery.\n")
        status_text.text.bind("<Key>", lambda e: "break")

        # Progress Bar
        progress_bar = ttk.Progressbar(frame, bootstyle="info-striped", mode="determinate", length=400)
        progress_bar.pack(pady=10)
        progress_bar.pack_forget()

        # Buttons Frame
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill="x", pady=10)

        reset_button = ttk.Button(button_frame, text="Reset", 
                                 command=lambda: self.start_reset(email_var.get().strip(), status_text, progress_bar, window, reset_button),
                                 bootstyle="info-outline", width=15)
        reset_button.pack(side="left", padx=10)
        ToolTip(reset_button, text="Begin the reset process.")

        cancel_button = ttk.Button(button_frame, text="Cancel", command=lambda: self.close_action_window(window), 
                                  bootstyle="danger-outline", width=15)
        cancel_button.pack(side="left", padx=10)
        ToolTip(cancel_button, text="Return to the main window.")

        # Image Label
        image_label = ttk.Label(frame, text="Intruder Photo (if captured)", font=("Arial", 10), bootstyle="light")
        image_label.pack(pady=15)
        self.image_label = image_label

    def start_signup(self, email, status_text, progress_bar, window, start_button):
        """Initiate signup process."""
        if self.running:
            messagebox.showwarning("Warning", "Another process is running. Please wait.", parent=window)
            return
        if not email:
            messagebox.showerror("Error", "Please enter an email address.", parent=window)
            return
        if not self.auth_handler:
            messagebox.showerror("Error", "Authentication handler not initialized.", parent=window)
            return
        self.running = True
        start_button.config(state='disabled')
        threading.Thread(target=self.auth_handler.run_signup, args=(email, status_text, progress_bar, window, self.image_label), daemon=True).start()
        threading.Thread(target=self._enable_button_after, args=(start_button,), daemon=True).start()

    def start_login(self, email, status_text, progress_bar, window, start_button):
        """Initiate login process."""
        if self.running:
            messagebox.showwarning("Warning", "Another process is running. Please wait.", parent=window)
            return
        if not email:
            messagebox.showerror("Error", "Please enter an email address.", parent=window)
            return
        if not self.auth_handler:
            messagebox.showerror("Error", "Authentication handler not initialized.", parent=window)
            return
        self.running = True
        start_button.config(state='disabled')
        threading.Thread(target=self.auth_handler.run_login, args=(email, status_text, progress_bar, window, self.image_label), daemon=True).start()
        threading.Thread(target=self._enable_button_after, args=(start_button,), daemon=True).start()

    def start_reset(self, email, status_text, progress_bar, window, reset_button):
        """Initiate reset process."""
        if self.running:
            messagebox.showwarning("Warning", "Another process is running. Please wait.", parent=window)
            return
        if not email:
            messagebox.showerror("Error", "Please enter an email address.", parent=window)
            return
        if not self.auth_handler:
            messagebox.showerror("Error", "Authentication handler not initialized.", parent=window)
            return
        self.running = True
        reset_button.config(state='disabled')
        threading.Thread(target=self.auth_handler.run_password_reset, args=(email, status_text, progress_bar, window, self.image_label), daemon=True).start()
        threading.Thread(target=self._enable_button_after, args=(reset_button,), daemon=True).start()

    def _enable_button_after(self, button):
        """Re-enable the start button after the process completes."""
        while self.running:
            time.sleep(0.1)
        try:
            if button.winfo_exists():
                button.config(state='normal')
        except Exception:
            pass
        self.running = False