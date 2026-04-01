import time
import tkinter as tk
from tkinter import messagebox, ttk
import subprocess
import sys
import os
import configparser
import threading

import serial
import serial.tools.list_ports

# Vérifier si le fichier config.ini existe
if not os.path.exists("config.ini"):
    print("Erreur : Le fichier config.ini est introuvable.")
    sys.exit(1)

# Lire la configuration depuis le fichier ini
config = configparser.ConfigParser()
config.read("config.ini")

# Chemin d'accès à la commande socat
try:
    SOCAT = config["Paths"]["SOCAT"]
except KeyError:
    print("Erreur : Le chemin de SOCAT n'est pas défini dans config.ini.")
    sys.exit(1)

# Liste pour garder une trace des processus socat lancés
socat_processes = []

# # Obtenir le chemin du fichier icône
def resource_path(relative_path):
    """Obtenir le chemin absolu du fichier, compatible avec PyInstaller"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class TextRedirector:
    """Classe pour rediriger stdout/stderr vers un widget Text."""
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, message):
        self.text_widget.insert(tk.END, message)
        self.text_widget.see(tk.END)  # Faire défiler automatiquement vers le bas

    def flush(self):
        pass  # Nécessaire pour compatibilité avec sys.stdout/stderr

# Création de l'interface
tk_root = tk.Tk()
tk_root.title("Liste des ports COM disponibles")
tk_root.iconbitmap(resource_path("usb_icon.ico"))

tk.Label(tk_root, text="This Program must remain open in order to function").pack()

# Listbox contenant les Ports COM
port_listbox = tk.Listbox(
    tk_root, 
    selectmode=tk.MULTIPLE,
    width=40, height=10, bd=2, relief=tk.SUNKEN)
port_listbox.pack(padx=5, pady=5)

# Case à cocher pour le mode Silent
silent_mode = tk.BooleanVar(value=False)  # Par défaut, le mode silent est activé
tk.Checkbutton(
    tk_root,
    text="Mode Silent (désactiver pour afficher les logs)",
    variable=silent_mode
).pack(padx=5, pady=5)

# Créer un conteneur pour les boutons
button_frame = tk.Frame(tk_root)
button_frame.pack()

# Ajouter un Notebook pour les onglets de logs
notebook = ttk.Notebook(tk_root)
notebook.pack(fill=tk.BOTH, expand=True)
logs = tk.Frame(notebook)
notebook.add(logs, text="Logs")

# Zone de texte pour afficher les logs
log_text = tk.Text(logs, width=80, height=20, state=tk.NORMAL, wrap=tk.WORD)
log_text.pack(fill=tk.BOTH, padx=5, pady=5)

def reset_ports():
    terminate_socat_processes()
    # Clear the content of the logs frame
    log_text.delete(1.0, tk.END)
    # Destroy all frames in the notebook except the "Logs" tab
    for tab in notebook.tabs():
        if notebook.tab(tab, "text") != "Logs":
            notebook.forget(tab)
        # Clear the content of the port_listbox
    port_listbox.delete(0, tk.END)
    scan_ports()
    
def scan_ports():
    """
    Scans and lists all available COM ports.

    Side Effects:
        - Prints a message to the console indicating the start of the scan.
        - Modifies the contents of the `port_listbox` widget.

    Note:
        Ensure that the `serial` module and `port_listbox` are properly
        initialized before calling this function.
    """
    print ("Recherche des ports COM disponibles...")

    ports = serial.tools.list_ports.comports()
    port_listbox.delete(0, tk.END)
    for port in ports:
        port_listbox.insert(tk.END, port.device)

def run(port: int, silent:bool = False, protocol: str="UDP"):
    VERBOSE = "-v" if not silent else ""
    # MODE_OUTPUT_REDIR = "" if silent else "> NUL"

    ensure_socat()

    # Utilisation de pyserial pour configurer le port série si nécessaire
    try:
        with serial.Serial(f"COM{port}", baudrate=250000, parity='N', stopbits=1, bytesize=8, timeout=1) as ser:
            print(f"Port COM{port} ouvert et utilisé correctement.")
    except serial.SerialException as e:
        print(f"Erreur lors de la configuration du port COM{port}: {e}")
        return

    # En fonction du protocole, on lance socat
    if protocol == "UDP":
        socat_command = f"{SOCAT} {VERBOSE} UDP4-RECV:5010,ip-add-membership=239.255.50.10:0.0.0.0,reuseaddr!!udp-sendto:localhost:7778 /dev/ttyS{port - 1}"
    elif protocol == "TCP":
        socat_command = f"{SOCAT} {VERBOSE} TCP4-CONNECT:127.0.0.1:7778 /dev/ttyS{port - 1}"
    else:
        raise ValueError(f"Erreur, protocole {protocol} invalide.")

    # Zone de texte pour afficher les logs
    frame = tk.Frame(notebook)
    text = tk.Text(frame, state=tk.DISABLED, wrap=tk.WORD)
    text.pack(fill=tk.BOTH, padx=5, pady=5)
    notebook.add(frame, text=f"COM{port}")

    # Fonction pour rediriger les logs vers la zone de texte
    def redirect_logs(process):
        if process.stdout:  # Check if stdout is not None
            print ("## set log for process ##")
            for line in iter(process.stdout.readline, b""):
                print(line.decode("utf-8"), end="")
                text.config(state=tk.NORMAL)
                text.insert(tk.END, line.decode("utf-8"))
                text.see(tk.END)
                text.config(state=tk.DISABLED)
            process.stdout.close()
        # process.stdout = TextRedirector(text)
        # process.stderr = TextRedirector(text)
       
    # Lancer le processus socat avec Popen
    try:
        process = subprocess.Popen(
            socat_command,
            stdout=subprocess.PIPE if silent else None,
            stderr=subprocess.PIPE if silent else None,
            shell=False
        )
        socat_processes.append(process)  # Ajouter le processus à la liste
        print(f"Socat lancé pour le port COM{port}.")

        # Lancer un thread pour rediriger les logs
        thread = threading.Thread(target=redirect_logs, args=(process,))
        thread.start()

    except subprocess.SubprocessError as e:
        print(f"Erreur lors du lancement de socat : {e}")

def connect_ports():
    """
    Connects to the selected COM ports and runs a specified function for each port.
    """
    print("")
    selected_ports = [port_listbox.get(i).replace("COM", "") for i in port_listbox.curselection()]
    if not selected_ports:
        messagebox.showwarning("Avertissement", "Veuillez sélectionner au moins un port COM.")
        return

    for port in selected_ports:
        try:
            run(int(port), silent=silent_mode.get())
        except (ValueError, serial.SerialException) as e:
            messagebox.showerror("Erreur", f"Échec de connexion au port {port}: {e}")

        print (f"Le port {port} a été connecté.")

    print ("Tous les ports COM ont été connectés.")

# Fonction permettant de s'assurer que 'socat' est disponible
def ensure_socat():
    """
    Ensures that the 'socat' utility is installed and accessible.
    """
    try:
        subprocess.run([SOCAT, "-V"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError:
        print("Socat n'est pas installé ou n'est pas accessible. Veuillez installer Socat avant d'exécuter ce programme.")
        sys.exit(1)
    
def terminate_socat_processes():
    """
    Terminates all active socat processes and clears the process list.
    """
    print ("Terminer tous les processus socat en cours.")

    # Arrêter les processus socat
    for process in socat_processes:
        if process.poll() is None:  # Si le processus est toujours actif
            print(f"Arrêt du processus socat (PID: {process.pid})...")
            process.terminate()  # Envoyer un signal de terminaison
            try:
                process.wait(timeout=5)  # Attendre que le processus se termine
                print(f"Processus socat (PID: {process.pid}) arrêté.")
            except subprocess.TimeoutExpired:
                print(f"Le processus socat (PID: {process.pid}) ne répond pas, forçage de l'arrêt.")
                process.kill()  # Forcer l'arrêt du processus

    # Nettoyer la liste des processus
    socat_processes.clear()
    print("Tous les processus socat ont été terminés.")

# Associer la fermeture de la fenêtre à la fonction de terminaison des processus
def on_closing():
    """
    Handles the closing event of the Tkinter application.
    """
    terminate_socat_processes()  # Appeler la fonction pour fermer socat proprement
    tk_root.destroy()  # Fermer proprement l'application Tkinter

tk_root.protocol("WM_DELETE_WINDOW", on_closing)  # Lier l'événement de fermeture à on_closing

tk.Button(button_frame, text="Scanner", command=reset_ports).pack(side=tk.LEFT, padx=5, pady=5)
tk.Button(button_frame, text="Connecter", command=connect_ports).pack(side=tk.LEFT, padx=5, pady=5)

# Rediriger stdout et stderr vers la zone de texte
sys.stdout = TextRedirector(log_text)
sys.stderr = TextRedirector(log_text)

scan_ports()  # Scanner immédiatement au lancement
 
tk_root.mainloop()
