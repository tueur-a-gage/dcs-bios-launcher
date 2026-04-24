import os
import sys
import configparser
import tkinter as tk
import communication as com
from error_mgt import ConfigError

def resource_path(relative_path):
    """Get the absolute path of the file"""
    return os.path.join(os.path.dirname(__file__), relative_path)

class TextRedirector:
    """Class for redirecting stdout/stderr to a Text widget."""
    def __init__(self, text_widget):
        """Initialize the TextRedirector with the given Text widget."""
        self.text_widget = text_widget

    def write(self, message):
        """Write a message to the Text widget and scroll to the end."""
        self.text_widget.insert(tk.END, message)
        self.text_widget.see(tk.END)  # Scroll automatically to the bottom

    def flush(self):
        """Called when closed"""

def open_interface() -> None:
    '''Function to open the graphical interface'''
    tk_root = tk.Tk()
    tk_root.title("Available COM ports list")

    bridges = []  # List to keep track of launched sockets/bridges for proper cleanup on exit

    try:
        # Load and set the window icon
        tk_root.iconbitmap(resource_path("usb_icon.ico"))
    except tk.TclError as e:
        print(f"Warning: Failed to load usb_icon.ico: {e}")

    try:
        top_frame = tk.Frame(tk_root)
        top_frame.pack(padx=10, pady=10)
        left_frame = tk.Frame(top_frame)
        left_frame.pack(side=tk.LEFT, padx=10, pady=10)
        right_frame = tk.Frame(top_frame)
        right_frame.pack(side=tk.RIGHT, anchor='n', padx=10, pady=10)

        tk.Label(left_frame, text="Select com ports and click Connect").pack()

        # Create a Listbox to display available COM ports
        port_listbox = tk.Listbox(
            left_frame,
            selectmode=tk.MULTIPLE,
            width=40, height=10, bd=2, relief=tk.GROOVE)
        port_listbox.pack(padx=5, pady=5)

        nb_ports_text = tk.Label(left_frame, text="Nb of available ports: 0")
        nb_ports_text.pack()

        # Create a container for the buttons Scan & Connect
        button_frame = tk.Frame(right_frame)
        button_frame.pack(fill=tk.X, expand=True)

        scan_button = tk.Button(button_frame,
                                text="Scan",
                                command=lambda: com.scan_ports(log_text,
                                                               port_listbox,
                                                               nb_ports_text))
        scan_button.grid(row=0, column=0, sticky='ew', padx=5, pady=5)

        connect_button = tk.Button(button_frame,
                                   text="Connect",
                                   command=lambda: com.connect_ports(socat_path,
                                                                     log_text,
                                                                     port_listbox,
                                                                     silent_mode,
                                                                     bridges))
        connect_button.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

        # Silent mode checkbox
        silent_mode = tk.BooleanVar(value=True)
        tk.Checkbutton(
            right_frame,
            text="Mode Silent (deactivate to display logs)",
            variable=silent_mode
        ).pack(padx=5, pady=5)

        # Load and display the logo
        logo_image = tk.PhotoImage(file=resource_path("vfa103.png"))
        logo_label = tk.Label(right_frame, image=logo_image)
        logo_label.pack(pady=10)
        # Keep reference to prevent garbage collection
        right_frame.logo_image = logo_image

        # Log text area
        log_text = tk.Text(tk_root, width=80, height=20, state=tk.NORMAL, wrap=tk.WORD)
        log_text.pack(padx=5, pady=5)

        # Redirect stdout and stderr to the log text area
        # sys.stdout = TextRedirector(log_text)
        # sys.stderr = TextRedirector(log_text)

        # Check if config.ini file exists
        print("Checking for config.ini file...")
        if not os.path.exists("config.ini"):
            raise ConfigError("The config.ini file is not found.")

        # Read the configuration from the ini file
        config = configparser.ConfigParser()
        config.read("config.ini")

        # Path to the socat command
        try:
            print("Reading SOCAT path from config.ini...")
            socat_path = config["Paths"]["SOCAT"]
            print(f"SOCAT path found: {socat_path}")

        except KeyError as e:
            raise ConfigError("The path to SOCAT is not defined in config.ini.") from e

        com.scan_ports(log_text, port_listbox, nb_ports_text)

    except tk.TclError as e:
        print(f"Warning: {e}")
    except ConfigError as e:
        print(f"Error : {e}")
        scan_button.config(state=tk.DISABLED)
        connect_button.config(state=tk.DISABLED)

    def on_closing():
        try:
            com.stop_all_bridges(bridges)  # Function to stop all running bridges/sockets
            tk_root.destroy()
        except tk.TclError as e:
            print(f"Error destroying window: {e}")
            sys.exit(1)

    tk_root.protocol("WM_DELETE_WINDOW", on_closing)
    tk_root.mainloop()
