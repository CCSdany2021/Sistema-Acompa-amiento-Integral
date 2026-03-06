import psycopg2
from urllib.parse import urlparse
import sys

# Default URL from config
DATABASE_URL = "postgresql://postgres:admin8128@localhost/acompanamiento_db"

def test_connection():
    print(f"Testing connection to: {DATABASE_URL}")
    
    try:
        # Try connecting
        conn = psycopg2.connect(DATABASE_URL)
        print("Successfully connected!")
        conn.close()
    except Exception as e:
        print("\n--- Connection Failed ---")
        # Try to print the error object directly
        try:
            print(f"Error type: {type(e)}")
            print(f"Error: {e}")
        except:
            print("Could not print error using default encoding.")
        
        # If it's a UnicodeDecodeError or similar during printing, we missed it above?
        # Actually the user's error happened INSIDE connect(), so we might catch it here.
        # But if the error message itself is the problem, we need to inspect the exception object cautiously.
        
        if hasattr(e, 'pgerror') and e.pgerror:
             print(f"PG Code: {e.pgcode}")
             try:
                 print(f"PG Error (raw): {e.pgerror.encode('latin1')}") # try to show raw bytes if possible
             except:
                 pass

if __name__ == "__main__":
    # Force console encoding to utf-8
    sys.stdout.reconfigure(encoding='utf-8')
    test_connection()
