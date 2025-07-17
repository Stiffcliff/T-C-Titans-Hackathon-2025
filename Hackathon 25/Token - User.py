import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime
import json
import uuid
from cryptography.fernet import Fernet
import os

# File paths
KEY_FILE = "secret.key"
DB_FILE = "transactions.json"
PAYEES_FILE = "payees.json"
NFC_FILE = "nfc_payload.txt"

# Load or generate encryption key
def load_key():
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
    else:
        with open(KEY_FILE, "rb") as f:
            key = f.read()
    return Fernet(key)

fernet = load_key()

# Load or initialize transaction database
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {"transactions": [], "shared": []}

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

# Load or initialize payees
def load_payees():
    if os.path.exists(PAYEES_FILE):
        with open(PAYEES_FILE, "r") as f:
            return json.load(f)
    return ["Alan", "Kevin", "John"]

def save_payees(payees):
    with open(PAYEES_FILE, "w") as f:
        json.dump(payees, f, indent=2)

payees = load_payees()

# GUI Application
class TapPassApp:
    def __init__(self, root):
        self.root = root
        self.root.title("NFC Token System - Sim")
        self.root.geometry("500x400+100+100")
        ttk.Button(root, text="Generate Transaction Token", command=self.generate_token_window).pack(pady=5)
        ttk.Button(root, text="My Transaction Tokens", command=self.view_tokens).pack(pady=5)
        ttk.Button(root, text="Send Transaction Token", command=self.send_token_window).pack(pady=5)
        ttk.Button(root, text="My Shared Tokens", command=self.view_shared_tokens).pack(pady=5)
        ttk.Button(root, text="Execute Transaction Token", command=self.execute_token_window).pack(pady=5)
        ttk.Button(root, text="Payees", command=self.manage_payees).pack(pady=5)

    def generate_token_window(self):
        win = tk.Toplevel(self.root)
        win.title("Generate Token")
        win.geometry("500x400+100+100")
        ttk.Label(win, text="Currency:").grid(row=0, column=0)
        currency_var = tk.StringVar()
        currency_menu = ttk.Combobox(win, textvariable=currency_var, values=["USD", "GBP", "EUR"], state="readonly")
        currency_menu.grid(row=0, column=1)
        currency_menu.current(0)
        ttk.Label(win, text="Amount:").grid(row=1, column=0)
        amount_entry = ttk.Entry(win)
        amount_entry.grid(row=1, column=1)
        ttk.Label(win, text="Expiry Date:").grid(row=2, column=0)
        date_entry = DateEntry(win, date_pattern='yyyy/mm/dd')
        date_entry.grid(row=2, column=1)
        ttk.Label(win, text="Expiry Time (HH:MM):").grid(row=3, column=0)
        time_entry = ttk.Entry(win)
        time_entry.insert(0, "12:00")
        time_entry.grid(row=3, column=1)

        def submit():
            try:
                db = load_db()
                currency = currency_var.get()
                amount = float(amount_entry.get())
                expiry_str = f"{date_entry.get()} {time_entry.get()}"
                expiry = datetime.strptime(expiry_str, "%Y/%m/%d %H:%M")
                tx_id = str(uuid.uuid4())
                encrypted = fernet.encrypt(tx_id.encode()).decode()
                db["transactions"].append({
                    "id": tx_id,
                    "encrypted": encrypted,
                    "currency": currency,
                    "amount": amount,
                    "expiry": expiry.strftime("%Y/%m/%d - %H:%M"),
                    "status": "valid"
                })
                save_db(db)
                with open(NFC_FILE, "w") as f:
                    f.write(tx_id)
                messagebox.showinfo("Success", f"Transaction created.\nEncrypted NFC Token:\n{encrypted}")
                win.destroy()
                self.show_payment_simulation()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ttk.Button(win, text="Create", command=submit).grid(row=4, column=0, columnspan=2, pady=10)

    def show_payment_simulation(self):
        pay_win = tk.Toplevel(self.root)
        pay_win.title("Simulate Payment")
        pay_win.geometry("500x400+100+100")
        ttk.Label(pay_win, text="Simulate payment for the generated token").pack(pady=10)

        def simulate_payment():
            messagebox.showinfo("Payment", "Payment simulated successfully.")
            pay_win.destroy()

        ttk.Button(pay_win, text="Pay from linked bank account", command=simulate_payment).pack(pady=10)

    def view_tokens(self):
        win = tk.Toplevel(self.root)
        win.title("My Transactions")
        win.geometry("500x400+100+100")
        db = load_db()
        for tx in db["transactions"]:
            label = f"{tx['currency']} {tx['amount']} - Exp: {tx['expiry']} - Status: {tx['status']}"
            ttk.Label(win, text=label).pack(anchor="w")

    def send_token_window(self):
        win = tk.Toplevel(self.root)
        win.title("Send Token")
        win.geometry("500x400+100+100")
        db = load_db()
        valid_tokens = [tx for tx in db["transactions"] if tx["status"] == "valid"]
        if not valid_tokens:
            ttk.Label(win, text="No valid tokens available.").pack()
            return
        ttk.Label(win, text="Select Token:").pack()
        token_var = tk.StringVar()
        token_menu = ttk.Combobox(win, textvariable=token_var, state="readonly")
        token_menu['values'] = [f"{tx['currency']} {tx['amount']} - Exp: {tx['expiry']}" for tx in valid_tokens]
        token_menu.pack()
        ttk.Label(win, text="Send To:").pack()
        recipient_var = tk.StringVar()
        recipient_menu = ttk.Combobox(win, textvariable=recipient_var, values=payees, state="readonly")
        recipient_menu.pack()

        def send():
            idx = token_menu.current()
            recipient = recipient_var.get()
            if idx >= 0 and recipient:
                db = load_db()
                valid_tokens = [tx for tx in db["transactions"] if tx["status"] == "valid"]
                tx = valid_tokens[idx]
                if tx["status"] != "valid":
                    messagebox.showerror("Error", "Only valid tokens can be sent.")
                    return
                db["shared"].append({
                    "to": recipient,
                    "token": tx["encrypted"],
                    "amount": tx["amount"],
                    "expiry": tx["expiry"],
                    "status": "sent"
                })
                db["transactions"].remove(tx)
                save_db(db)
                messagebox.showinfo("Success", f"Token sent to {recipient}.")
                win.destroy()

        ttk.Button(win, text="Send", command=send).pack(pady=10)

    def view_shared_tokens(self):
        win = tk.Toplevel(self.root)
        win.title("Shared Tokens")
        win.geometry("500x400+100+100")
        db = load_db()
        for tx in db["shared"]:
            label = f"To: {tx['to']} - Amount: {tx['amount']} - Exp: {tx['expiry']} - Status: {tx['status']}"
            ttk.Label(win, text=label).pack(anchor="w")

    def execute_token_window(self):
        win = tk.Toplevel(self.root)
        win.title("Execute Token")
        win.geometry("500x400+100+100")
        db = load_db()
        valid_tokens = [tx for tx in db["transactions"] if tx["status"] == "valid"]
        if not valid_tokens:
            ttk.Label(win, text="No valid tokens to execute.").pack()
            return
        ttk.Label(win, text="Select Token to Execute:").pack()
        token_var = tk.StringVar()
        token_menu = ttk.Combobox(win, textvariable=token_var, state="readonly")
        token_menu['values'] = [f"{tx['currency']} {tx['amount']} - Exp: {tx['expiry']}" for tx in valid_tokens]
        token_menu.pack()

        def execute():
            idx = token_menu.current()
            if idx >= 0:
                db = load_db()
                valid_tokens = [tx for tx in db["transactions"] if tx["status"] == "valid"]
                tx = valid_tokens[idx]
                win.destroy()
                self.show_nfc_simulation(tx)

        ttk.Button(win, text="Execute", command=execute).pack(pady=10)

    def show_nfc_simulation(self, tx):
        win = tk.Toplevel(self.root)
        win.title("NFC Simulation")
        win.geometry("500x400+100+100")
        ttk.Label(win, text="Simulated NFC Token Scanned").pack(pady=5)
        ttk.Label(win, text="Plain Token ID:").pack()
        text = tk.Text(win, height=4, width=60)
        text.insert("1.0", tx["id"])
        text.config(state="disabled")
        text.pack()

        def mark_used():
            db = load_db()
            for t in db["transactions"]:
                if t["id"] == tx["id"]:
                    t["status"] = "used"
                    break
            save_db(db)
            messagebox.showinfo("Transaction", "Transaction marked as used.")

        ttk.Button(win, text="Mark as Used", command=mark_used).pack(pady=10)

    def manage_payees(self):
        win = tk.Toplevel(self.root)
        win.title("Manage Payees")
        win.geometry("500x400+100+100")
        ttk.Label(win, text="Existing Payees:").pack()
        listbox = tk.Listbox(win)
        for p in payees:
            listbox.insert("end", p)
        listbox.pack()
        ttk.Label(win, text="Add New Payee:").pack()
        new_entry = ttk.Entry(win)
        new_entry.pack()

        def add_payee():
            name = new_entry.get().strip()
            if name and name not in payees:
                payees.append(name)
                save_payees(payees)
                listbox.insert("end", name)
                new_entry.delete(0, "end")

        ttk.Button(win, text="Add", command=add_payee).pack(pady=5)

if __name__ == '__main__':
    root = tk.Tk()
    root.geometry("500x400+100+100")
    app = TapPassApp(root)
    root.mainloop()
