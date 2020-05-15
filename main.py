import requests
import os
from dotenv import load_dotenv

load_dotenv()
MINECRAFT_DIR, MINECRAFT_SNAPSHOT_DIR = os.getenv("MINECRAFT_DIR"), os.getenv("MINECRAFT_SNAPSHOT_DIR")