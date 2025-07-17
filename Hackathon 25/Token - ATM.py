import tkinter as tk
from tkinter import ttk, messagebox
import json
import os

# File paths
DB_FILE = "transactions.json"
NFC_FILE = "nfc_payload.txt"

# Load transaction database
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {"transactions": [], "shared": []}

# Save transaction database
def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

# GUI Application
class ATMApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulated ATM")

        ttk.Label(root, text="Enter Transaction ID (from NFC):").pack(pady=5)
        self.tx_entry = ttk.Entry(root, width=50)
        self.tx_entry.pack(pady=5)

        ttk.Button(root, text="Scan NFC", command=self.scan_nfc).pack(pady=5)
        ttk.Button(root, text="Process Transaction", command=self.process_transaction).pack(pady=10)

    def scan_nfc(self):
        if os.path.exists(NFC_FILE):
            with open(NFC_FILE, "r") as f:
                tx_id = f.read().strip()
                self.tx_entry.delete(0, tk.END)
                self.tx_entry.insert(0, tx_id)
                messagebox.showinfo("NFC Scan", "Transaction ID scanned from NFC.")
        else:
            messagebox.showwarning("NFC Error", "No NFC data found.")

    def process_transaction(self):
        tx_id = self.tx_entry.get().strip()
        if not tx_id:
            messagebox.showwarning("Input Error", "Please enter a transaction ID.")
            return

        db = load_db()
        for tx in db["transactions"]:
            if tx.get("id") == tx_id and tx.get("status") == "valid":
                tx["status"] = "used"
                save_db(db)
                messagebox.showinfo("Transaction Executed",
                                    f"Transaction for {tx['currency']} {tx['amount']} executed.\nStatus set to 'used'.")
                
                self.tx_entry.delete(0, tk.END)
                return

        messagebox.showerror("Transaction Not Found", "No valid transaction found for the provided ID.")

# Run the application
if __name__ == '__main__':
    root = tk.Tk()
    app = ATMApp(root)
    root.mainloop()
