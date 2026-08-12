import sqlite3
from contextlib import contextmanager

DB_PATH = 'canteen_erp.db'

@contextmanager
def get_db_connection():
    # Phase 1: Initialize
    # Open the vault door
    conn = sqlite3.connect(DB_PATH)
    
     
    # We must turn them ON every time we connect so your schema constraints work.
    conn.execute("PRAGMA foreign_keys = ON;")
    
    try:
        # Phase 2: Yield
        # Hand the active connection to the CRUD function that asked for it
        yield conn
        
        # Phase 3: Terminate (Success)
        # If the CRUD function finishes without crashing, save (commit) the data
        conn.commit()
        
    except Exception as e:
        # Phase 3: Terminate (Failure)
        # If the CRUD function crashes, undo (rollback) any partial data writes
        conn.rollback()
        print(f"[-] Database Error: {e}")
        raise e  
        
    finally:
        # The vault door automatically closes no matter what happened
        conn.close()