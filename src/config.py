import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

DB_URI = os.getenv("DB_URI")

if not DB_URI:
    print("DB_URI not found. Make sure it is set in the .env file.")
else:
    print("DB_URI loaded from .env")
