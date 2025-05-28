import tkinter as tk
from tkinter import ttk, font
import speedtest
import threading
import platform # For OS-specific font adjustments

# --- Configuration ---
APP_TITLE = "FluxNet Speed Tester"
WINDOW_SIZE = "450x550"

# Theme Colors (Dark Theme Example)
BG_COLOR = "#2E2E2E"
FG_COLOR = "#E0E0E0"
ACCENT_COLOR = "#007ACC"
BUTTON_BG_COLOR = "#4A4A4A"
BUTTON_FG_COLOR = "#FFFFFF"
BUTTON_ACTIVE_BG = "#5A5A5A"
RESULT_FG_COLOR = "#4CAF50"
ERROR_FG_COLOR = "#F44336"
FONT_FAMILY_MAIN = "Segoe UI" if platform.system() == "Windows" else "Helvetica"
FONT_FAMILY_DIGITS = "Consolas" if platform.system() == "Windows" else "Menlo"

# --- Global Variables for UI Elements ---
root = None
download_label_var = None
upload_label_var = None
ping_label_var = None
status_label_var = None
start_button = None
progress_bar = None

# --- Helper functions for thread-safe GUI updates ---
def safe_gui_update(element_var, value):
    """Safely updates a Tkinter StringVar from any thread."""
    if root and root.winfo_exists() and element_var:
        root.after(0, lambda v=value: element_var.set(v))

def safe_button_config(state, text):
    """Safely configures the start button from any thread."""
    if root and root.winfo_exists() and start_button:
        root.after(0, lambda s=state, t=text: start_button.config(state=s, text=t))

def safe_progressbar_control(action):
    """Safely controls the progress bar from any thread."""
    if root and root.winfo_exists() and progress_bar:
        if action == 'start':
            root.after(0, lambda: progress_bar.start(10))
        elif action == 'stop':
            root.after(0, lambda: progress_bar.stop())
            root.after(0, lambda: progress_bar.config(value=0))

# --- Real-time Speed Update Callbacks ---
def download_progress_updater(bytes_transferred, time_elapsed, **kwargs): # <--- Added **kwargs
    """Callback for speedtest download progress."""
    if not root or not root.winfo_exists(): return # Window closed
    if time_elapsed > 0:
        # Speed in Mbps
        current_speed_mbps = (bytes_transferred * 8 / 1_000_000) / time_elapsed
        safe_gui_update(download_label_var, f"{current_speed_mbps:.2f}")
    elif download_label_var.get() == "---" or download_label_var.get() == "Error": # Initial update
        safe_gui_update(download_label_var, "0.00")

def upload_progress_updater(bytes_transferred, time_elapsed, **kwargs): # <--- Added **kwargs
    """Callback for speedtest upload progress."""
    if not root or not root.winfo_exists(): return # Window closed
    if time_elapsed > 0:
        # Speed in Mbps
        current_speed_mbps = (bytes_transferred * 8 / 1_000_000) / time_elapsed
        safe_gui_update(upload_label_var, f"{current_speed_mbps:.2f}")
    elif upload_label_var.get() == "---" or upload_label_var.get() == "Error": # Initial update
        safe_gui_update(upload_label_var, "0.00")


# --- Core Speed Test Logic ---
def perform_speed_test():
    global download_label_var, upload_label_var, ping_label_var, status_label_var

    safe_gui_update(status_label_var, "Initializing speed test...")
    safe_button_config(tk.DISABLED, "Testing...")
    safe_progressbar_control('start')

    # Reset labels to "---" or "0.00" before test
    safe_gui_update(download_label_var, "0.00")
    safe_gui_update(upload_label_var, "0.00")
    safe_gui_update(ping_label_var, "---")

    try:
        st = speedtest.Speedtest()
        # st.closest = {} # Force re-fetch, useful for debugging if servers are cached too aggressively

        safe_gui_update(status_label_var, "Finding best server...")
        st.get_best_server() # This can take a moment
        safe_gui_update(ping_label_var, f"{st.results.ping:.2f}") # Ping is available after get_best_server

        safe_gui_update(status_label_var, "Testing download speed...")
        # The st.download() method itself returns the final average speed in bits/sec
        # The callback will update the label in real-time
        st.download(callback=download_progress_updater)
        final_download_speed_mbps = st.results.download / 1_000_000
        safe_gui_update(download_label_var, f"{final_download_speed_mbps:.2f}")

        safe_gui_update(status_label_var, "Testing upload speed...")
        # The st.upload() method itself returns the final average speed in bits/sec
        st.upload(callback=upload_progress_updater)
        final_upload_speed_mbps = st.results.upload / 1_000_000
        safe_gui_update(upload_label_var, f"{final_upload_speed_mbps:.2f}")

        # Ping might be refined after full test, re-fetch
        final_ping = st.results.ping
        safe_gui_update(ping_label_var, f"{final_ping:.2f}")

        safe_gui_update(status_label_var, "Test Complete!")

    except speedtest.ConfigRetrievalError:
        safe_gui_update(status_label_var, "Error: Cannot connect to Speedtest.net.")
        set_error_labels_thread_safe()
    except speedtest.NoMatchedServers:
        safe_gui_update(status_label_var, "Error: No suitable test servers found.")
        set_error_labels_thread_safe()
    except Exception as e:
        error_msg = f"Error: {str(e)[:50]}"
        if "HTTP Error 403: Forbidden" in str(e): # More specific error for common issue
            error_msg = "Error: Access denied by Speedtest.net (403). Try later."
        safe_gui_update(status_label_var, error_msg + "...")
        set_error_labels_thread_safe()
    finally:
        safe_button_config(tk.NORMAL, "Start Speed Test")
        safe_progressbar_control('stop')

def set_error_labels_thread_safe():
    safe_gui_update(download_label_var, "Error")
    safe_gui_update(upload_label_var, "Error")
    safe_gui_update(ping_label_var, "Error")
    # Potentially change status label color here too if desired, using a similar safe_gui_update approach

def start_test_thread():
    # Reset labels to initial state before starting a new test
    if download_label_var: download_label_var.set("---")
    if upload_label_var: upload_label_var.set("---")
    if ping_label_var: ping_label_var.set("---")
    if status_label_var: status_label_var.set("Click 'Start Speed Test' to begin.")

    test_thread = threading.Thread(target=perform_speed_test)
    test_thread.daemon = True
    test_thread.start()

# --- GUI Setup ---
def create_gui():
    global root, download_label_var, upload_label_var, ping_label_var, status_label_var, start_button, progress_bar

    root = tk.Tk()
    root.title(APP_TITLE)
    root.geometry(WINDOW_SIZE)
    root.configure(bg=BG_COLOR)
    root.resizable(False, False)

    # --- Fonts ---
    title_font = font.Font(family=FONT_FAMILY_MAIN, size=20, weight="bold")
    label_font = font.Font(family=FONT_FAMILY_MAIN, size=12)
    result_font = font.Font(family=FONT_FAMILY_DIGITS, size=18, weight="bold")
    status_font = font.Font(family=FONT_FAMILY_MAIN, size=10, slant="italic")
    button_font = font.Font(family=FONT_FAMILY_MAIN, size=12, weight="bold")

    # --- Main Frame ---
    main_frame = tk.Frame(root, bg=BG_COLOR, padx=20, pady=20)
    main_frame.pack(expand=True, fill=tk.BOTH)

    # --- Title ---
    title_label = tk.Label(main_frame, text=APP_TITLE, font=title_font, bg=BG_COLOR, fg=ACCENT_COLOR)
    title_label.pack(pady=(0, 30))

    # --- Icon ---
    icon_placeholder = tk.Label(main_frame, text="🚀", font=(FONT_FAMILY_MAIN, 48), bg=BG_COLOR, fg=ACCENT_COLOR)
    icon_placeholder.pack(pady=(0, 20))

    # --- Results Frame ---
    results_frame = tk.Frame(main_frame, bg=BG_COLOR)
    results_frame.pack(pady=20)

    def create_result_row(parent, text, var_for_value, unit_text):
        row_frame = tk.Frame(parent, bg=BG_COLOR)
        tk.Label(row_frame, text=text, font=label_font, bg=BG_COLOR, fg=FG_COLOR, width=15, anchor="w").pack(side=tk.LEFT, padx=5)
        value_label = tk.Label(row_frame, textvariable=var_for_value, font=result_font, bg=BG_COLOR, fg=RESULT_FG_COLOR, width=7, anchor="e") # Adjusted width
        value_label.pack(side=tk.LEFT, padx=(5,0))
        tk.Label(row_frame, text=unit_text, font=label_font, bg=BG_COLOR, fg=FG_COLOR, anchor="w", width=5).pack(side=tk.LEFT, padx=(0,5)) # Adjusted width
        row_frame.pack(fill=tk.X, pady=5)
        return value_label # Return for potential color changes on error

    download_label_var = tk.StringVar(value="---")
    upload_label_var = tk.StringVar(value="---")
    ping_label_var = tk.StringVar(value="---")

    create_result_row(results_frame, "Download:", download_label_var, "Mbps")
    create_result_row(results_frame, "Upload:", upload_label_var, "Mbps")
    create_result_row(results_frame, "Ping:", ping_label_var, "ms")


    # --- Progress Bar ---
    style = ttk.Style()
    style.theme_use('clam')
    style.configure("Accent.Horizontal.TProgressbar", troughcolor=BG_COLOR, bordercolor=ACCENT_COLOR, background=ACCENT_COLOR, lightcolor=ACCENT_COLOR, darkcolor=ACCENT_COLOR)
    progress_bar = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, length=300, mode='indeterminate', style="Accent.Horizontal.TProgressbar")
    progress_bar.pack(pady=(10, 10))

    # --- Status Label ---
    status_label_var = tk.StringVar(value="Click 'Start Speed Test' to begin.")
    status_label_widget = tk.Label(main_frame, textvariable=status_label_var, font=status_font, bg=BG_COLOR, fg=FG_COLOR, wraplength=380)
    status_label_widget.pack(pady=(10, 20))

    # --- Start Button ---
    start_button = tk.Button(
        main_frame,
        text="Start Speed Test",
        font=button_font,
        bg=BUTTON_BG_COLOR,
        fg=BUTTON_FG_COLOR,
        activebackground=BUTTON_ACTIVE_BG,
        activeforeground=BUTTON_FG_COLOR,
        command=start_test_thread,
        relief=tk.FLAT,
        padx=20,
        pady=10,
        borderwidth=0, # No borderwidth, rely on bg for visual
        highlightthickness=0
    )
    start_button.pack(pady=(10, 20))

    def on_enter(e):
        if start_button['state'] == tk.NORMAL:
            start_button['bg'] = ACCENT_COLOR
    def on_leave(e):
        if start_button['state'] == tk.NORMAL:
            start_button['bg'] = BUTTON_BG_COLOR

    start_button.bind("<Enter>", on_enter)
    start_button.bind("<Leave>", on_leave)

    root.mainloop()

# --- Main Execution ---
if __name__ == "__main__":
    create_gui()