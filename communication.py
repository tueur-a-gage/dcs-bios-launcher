import os
import tkinter as tk
from tkinter import messagebox
import serial.tools.list_ports
import subprocess, sys
from error_mgt import ConfigError, CommunicationError

def scan_ports(log_text: tk.Text, port_listbox: tk.Listbox, nb_ports_text: tk.Label):

    """Scan for available COM ports and update the Listbox and port count label."""
    log_text.delete(1.0, tk.END)  # Clear the log text area before scanning
    print("Scanning for available COM ports...")
    ports = serial.tools.list_ports.comports()

    port_listbox.delete(0, tk.END)  # Clear the Listbox before adding new ports
    i=0
    for port in ports:
        i += 1
        value = str(i) + " - " + port.device
        port_listbox.insert(tk.END, value)

    try:
        nb_ports_text.config(text=f"Nb of available ports: {i}")
    except tk.TclError as e:
        print(f"Warning: Failed to update nb_ports_text: {e}")

    ### DEBUG
    if i == 0:
        port_listbox.insert(tk.END, "<!> - COM3")
        port_listbox.insert(tk.END, "<!> - COM15")
        port_listbox.insert(tk.END, "<!> - COM24")

def ensure_socat(socat_path: str):
    """Function to ensure that 'socat' is available."""
    try:
        subprocess.run([socat_path, "-V"],
                       check=True,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        raise ConfigError(f"SOCAT is not installed or not accessible at path: {socat_path}") from e

def run(socat_path: str, port: int, silent: bool, socat_processes: list, protocol: str="UDP"):
    """Function to run socat with the specified parameters."""

    verbose = "-v" if not silent else ""

    ensure_socat(socat_path)

    # Use pyserial to configure the serial port
    try:
        with serial.Serial(f"COM{port}", baudrate=250000, parity='N',
                           stopbits=1, bytesize=8, timeout=1) as ser:
            print(f"COM{port} port is open and works fine")
    except serial.SerialException as e:
        raise CommunicationError(f"Error configuring COM{port}: {e}") from e

    # Run SOCAT depending on the protocol
    if protocol == "UDP":
        socat_command = f"{socat_path} {verbose} UDP4-RECV:5010,ip-add-membership=239.255.50.10:0.0.0.0,reuseaddr!!udp-sendto:localhost:7778 /dev/ttyS{port - 1}"
    elif protocol == "TCP":
        socat_command = f"{socat_path} {verbose} TCP4-CONNECT:127.0.0.1:7778 /dev/ttyS{port - 1}"
    else:
        raise ConfigError(f"Invalid protocol {protocol}.") from e

    ############################################
    # En mode mulithreading    
    # def execute_socat():
    #     try:
    #         subprocess.run(
    #             socat_command, 
    #             check=True, 
    #             shell=True, 
    #             stdout=subprocess.PIPE, 
    #             stderr=subprocess.PIPE)
    #     except subprocess.SubprocessError as e:
    #         print(f"Erreur lors de l'exécution de socat : {e}")

    # thread = threading.Thread(target=execute_socat)
    # thread.start()
    # socat_threads.append(thread)  # Ajouter le thread à la liste
    ############################################

    ############################################
    # En mode subprocess
    # Lancer le processus socat avec Popen
    try:
        process = subprocess.Popen(
            socat_command,
            stdout=subprocess.PIPE if silent else None,
            stderr=subprocess.PIPE if silent else None,
            shell=False
        )
        socat_processes.append(process)  # Ajouter le processus à la liste
        print(f"Run SOCAT on port {port}")
    except subprocess.SubprocessError as e:
        raise CommunicationError(f"Error on SOCAT usage: {e}") from e
    ############################################

def connect_ports(socat_path: str,
                  log_text: tk.Text,
                  port_listbox: tk.Listbox,
                  silent_mode: tk.BooleanVar,
                  socat_processes: list):
    """Connect to the selected COM ports."""
    log_text.delete(1.0, tk.END)  # Clear the log text area before scanning

    print("Connecting to selected COM ports...")

    selected_ports = []
    print("")
    print("Selected COM ports:")
    for i in port_listbox.curselection():
        selected_port = port_listbox.get(i).split("COM")[1]
        print(f" - COM{selected_port}")
        selected_ports.append(selected_port)

    if not selected_ports:
        print("No COM ports selected.")
        messagebox.showwarning("Warning", "Please select at least one COM port.", icon='warning')
        return

    print("")
    print("Attempting to connect to port:")
    for port in selected_ports:
        try:
            print(f" - COM{port}")
            run(socat_path, int(port), silent_mode.get(), socat_processes)
        except (ValueError, serial.SerialException) as e:
            messagebox.showerror("Error", f"Failed to connect to port {port}: {e}")

        print (f" - Port COM{port} has been connected.")

    print("")
    print ("### All selected COM ports have been connected. ###")
