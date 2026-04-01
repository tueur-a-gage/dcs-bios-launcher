import tkinter as tk
import serial.tools.list_ports

def scan_ports(log_text, port_listbox, nb_ports_text):
    log_text.delete(1.0, tk.END)  # Clear the log text area before scanning
    print("Scanning for available COM ports...")
    ports = serial.tools.list_ports.comports()
    port_listbox.delete(0, tk.END)
    i: int=1
    for port in ports:
        value = str(i) + " - " + port.device
        port_listbox.insert(tk.END, value)
        i += 1
    nb_ports_text.config(text=f"Nb of available ports: {i-1}")

def connect_ports(log_text, port_listbox, silent_mode):
    print("Connecting to selected COM ports...")
    # selected_ports = [port_listbox.get(i).replace("COM", "") for i in port_listbox.curselection()]
    # if not selected_ports:
    #     messagebox.showwarning("Avertissement", "Veuillez sélectionner au moins un port COM.")
    #     return

    # for port in selected_ports:
    #     try:
    #         run(int(port), silent=silent_mode.get())
    #     except (ValueError, serial.SerialException) as e:
    #         messagebox.showerror("Erreur", f"Échec de connexion au port {port}: {e}")

    #     print (f"Le port {port} a été connecté.")

    print ("All selected COM ports have been connected.")
