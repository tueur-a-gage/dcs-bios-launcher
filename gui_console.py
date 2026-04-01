import tkinter as tk
from tkinter import messagebox
import subprocess
import sys
import os
import threading
import configparser
import signal

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

# Liste pour garder une trace des threads lancés
socat_threads = []
# Liste pour garder une trace des processus socat lancés
socat_processes = []

silent_mode=False

class TextRedirector:
    """Classe pour rediriger stdout/stderr vers un widget Text."""
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, message):
        self.text_widget.insert(tk.END, message)
        self.text_widget.see(tk.END)  # Faire défiler automatiquement vers le bas

    def flush(self):
        pass  # Nécessaire pour compatibilité avec sys.stdout/stderr

# Obtenir le chemin du fichier icône
def resource_path(relative_path):
    """Obtenir le chemin absolu du fichier, compatible avec PyInstaller"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# Fonction permettant de s'assurer que 'socat' est disponible
def ensure_socat():
    try:
        subprocess.run([SOCAT, "-V"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError:
        print("Socat n'est pas installé ou n'est pas accessible. Veuillez installer Socat avant d'exécuter ce programme.")
        sys.exit(1)

def run(port: int, silent: bool=True, protocol: str="UDP"):
    VERBOSE = "-v" if not silent else ""
    MODE_OUTPUT_REDIR = "" if silent else "> NUL"

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
        print(f"Socat lancé pour le port COM{port}.")
    except Exception as e:
        print(f"Erreur lors du lancement de socat : {e}")
    ############################################
            
def terminate_socat_processes():
    """Terminer tous les processus socat en cours."""

    ############################################
    # En mode MuliThreading
    # for thread in socat_threads:
    #     if thread.is_alive():
    #         print("Attente de la fin du thread...")
    #         thread.join(timeout=1)  # Attendre que le thread se termine (timeout pour éviter un blocage)
    #         print("Thread terminé.")

    # # Nettoyer les listes
    # socat_threads.clear()
    # print("Tous les processus et threads socat ont été terminés.")

    # # Si des processus enfants ont été lancés, terminez-les explicitement
    # try:
    #     os.killpg(0, signal.SIGTERM)  # Tuer tous les processus enfants du groupe
    #     print("Tous les processus enfants ont été terminés.")
    # except Exception as e:
    #     print(f"Erreur lors de la terminaison des processus enfants : {e}")
    ############################################

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

    # Terminer les threads
    for thread in socat_threads:
        if thread.is_alive():
            print("Attente de la fin du thread...")
            thread.join(timeout=1)
            print("Thread terminé.")

    socat_threads.clear()
    print("Tous les threads ont été terminés.")

def scan_ports():
    ports = serial.tools.list_ports.comports()
    port_listbox.delete(0, tk.END)
    for port in ports:
        port_listbox.insert(tk.END, port.device)


def connect_ports():
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

# Création de l'interface
tk_root = tk.Tk()
tk_root.title("Liste des ports COM disponibles")
tk_root.iconbitmap(resource_path("usb_icon.ico"))

tk.Label(tk_root, text="This Program must remain open in order to function").pack()

port_listbox = tk.Listbox(
    tk_root, 
    selectmode=tk.MULTIPLE,
    width=40, height=10, bd=2, relief=tk.SUNKEN)

port_listbox.pack(padx=5, pady=5)

# Créer un conteneur pour les boutons
button_frame = tk.Frame(tk_root)
button_frame.pack()

tk.Button(button_frame, text="Scanner", command=scan_ports).pack(side=tk.LEFT, padx=5, pady=5)
tk.Button(button_frame, text="Connecter", command=connect_ports).pack(side=tk.LEFT, padx=5, pady=5)

silent_mode = tk.BooleanVar(value=True)  # Par défaut, le mode silent est activé

tk.Checkbutton(
    tk_root,
    text="Mode Silent (désactiver pour afficher les logs)",
    variable=silent_mode
).pack(padx=5, pady=5)

# Zone de texte pour afficher les logs
log_text = tk.Text(tk_root, width=80, height=20, state=tk.NORMAL, wrap=tk.WORD)
log_text.pack(padx=5, pady=5)

# Rediriger stdout et stderr vers la zone de texte
sys.stdout = TextRedirector(log_text)
sys.stderr = TextRedirector(log_text)

scan_ports()  # Scanner immédiatement au lancement

# Associer la fermeture de la fenêtre à la fonction de terminaison des processus
def on_closing():
    terminate_socat_processes()  # Appeler la fonction pour fermer socat proprement
    tk_root.destroy()  # Fermer proprement l'application Tkinter
    
tk_root.protocol("WM_DELETE_WINDOW", on_closing)  # Lier l'événement de fermeture à on_closing
    
tk_root.mainloop()
