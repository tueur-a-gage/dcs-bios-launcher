import configparser
import os
import subprocess
import sys

# Check if config.ini file exists
def ensure_socat():
    '''Function to ensure that 'socat' is available'''
    try:
        subprocess.run([SOCAT, "-V"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError:
        print("Socat is not installed or not accessible.")
        sys.exit(1)

# Check if config.ini file exists
print("Checking for config.ini file...")
if not os.path.exists("config.ini"):
    print("Error : The config.ini file is not found.")
    sys.exit(1)

# Read the configuration from the ini file
config = configparser.ConfigParser()
config.read("config.ini")

# Path to the socat command
try:
    print("Reading SOCAT path from config.ini...")
    SOCAT = config["Paths"]["SOCAT"]
    print(f"SOCAT path found: {SOCAT}")
    # ensure_socat ()  # Ensure that socat is available
except KeyError:
    print("Error : The path to SOCAT is not defined in config.ini.")
    sys.exit(1)
