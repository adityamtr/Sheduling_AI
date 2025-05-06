from pathlib import Path
import os
root_path = Path(os.getcwd().split('application_source')[0] + 'application_source')
import configparser
# Create a ConfigParser instance
config = configparser.ConfigParser()
# Read the config.ini file
config.read(Path.joinpath(root_path,"config/config.ini"))

