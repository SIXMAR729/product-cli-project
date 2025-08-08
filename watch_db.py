import sqlite3
import os
import argparse

DATABASE_NAME = "orders.db"
# A list of keywords that can modify data
DESTRUCTIVE_KEYWORDS = ["DELETE", "UPDATE", "INSERT", "DROP", "ALTER", "CREATE"]

def run_interactive_sql_client(read_only=False):
    """Starts an interactive SQL client with safety features."""
    
    if not os.path.exists(DATABASE_NAME):
        print(f"❌ Error: Database file '{DATABASE_NAME}' not found.")
        return

    mode = "Read-Only" if read_only else "Full Access"
    print(f"🔎 Connected to database: {DATABASE_NAME} (Mode: {mode})")
    print("Enter any SQL command, or type '.quit' to exit.")

    try:
        conn = sqlite3.connect(DATABASE_NAME)
        conn.row_factory = sqlite3.Row
        
        while True:
            command = input("sql> ").strip()

            if command.lower() == '.quit':
                break
            if not command:
                continue

            command_upper = command.upper()
            is_destructive = any(keyword in command_upper for keyword in DESTRUCTIVE_KEYWORDS)

            # Safety Check 1: Read-Only Mode
            if read_only and is_destructive:
                print("❌ Error: Cannot execute modifying command in read-only mode.")
                continue

            # Safety Check 2: Confirmation Prompt
            if is_destructive:
                confirm = input("⚠️ This command can modify data. Are you sure? [y/N] ")
                if confirm.lower() != 'y':
                    print("Aborted.")
                    continue
            
            try:
                cursor = conn.cursor()
                cursor.execute(command)

                if command_upper.startswith("SELECT"):
                    rows = cursor.fetchall()
                    if not rows:
                        print("(No results)")
                        continue
                    
                    headers = rows[0].keys()
                    print(" | ".join(f"{h:<20}" for h in headers))
                    print("-" * (23 * len(headers)))
                    for row in rows:
                        print(" | ".join(f"{str(value):<20}" for value in row))
                else:
                    conn.commit()
                    print(f"✅ OK. Rows affected: {cursor.rowcount}")

            except sqlite3.Error as e:
                print(f"❌ SQL Error: {e}")

    finally:
        if conn:
            conn.close()
            print("\nDisconnected from database.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="A safe, interactive client for SQLite.")
    parser.add_argument("--read-only", action="store_true", help="Run in read-only mode.")
    args = parser.parse_args()
    
    run_interactive_sql_client(read_only=args.read_only)