import tkinter as tk
from tkinter import messagebox, filedialog
import sqlite3
import csv
import os

class BusinessApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Business Data Tracker")
        self.root.geometry("500x500")
        
        # Database setup
        self.db_path = "business_data.db"
        self.init_db()

        # UI Layout
        tk.Label(root, text="Business Manager", font=("Arial", 20, "bold")).pack(pady=20)
        
        # Input Fields
        tk.Label(root, text="Item/Service Name:").pack()
        self.entry_item = tk.Entry(root, width=40)
        self.entry_item.pack(pady=5)

        tk.Label(root, text="Amount:").pack()
        self.entry_amount = tk.Entry(root, width=40)
        self.entry_amount.pack(pady=5)

        # Buttons
        tk.Button(root, text="Save Entry", command=self.save_data, bg="#2ecc71", width=20).pack(pady=10)
        tk.Button(root, text="View All Records", command=self.show_data, width=20).pack(pady=5)
        tk.Button(root, text="Export to CSV (Excel)", command=self.export_csv, width=20).pack(pady=5)
        
        tk.Label(root, text="Data is stored locally in 'business_data.db'", fg="gray").pack(side="bottom", pady=10)

    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.connect().cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS records (id INTEGER PRIMARY KEY, item TEXT, amount REAL)")
        conn.commit()
        conn.close()

    def save_data(self):
        item = self.entry_item.get()
        amount = self.entry_amount.get()
        if item and amount:
            try:
                conn = sqlite3.connect(self.db_path)
                conn.execute("INSERT INTO records (item, amount) VALUES (?, ?)", (item, float(amount)))
                conn.commit()
                conn.close()
                messagebox.showinfo("Success", "Data Saved!")
                self.entry_item.delete(0, tk.END)
                self.entry_amount.delete(0, tk.END)
            except ValueError:
                messagebox.showerror("Error", "Amount must be a number!")
        else:
            messagebox.showwarning("Error", "Fill all fields!")

    def show_data(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("SELECT item, amount FROM records")
        rows = cursor.fetchall()
        conn.close()
        summary = "\n".join([f"{r[0]}: ${r[1]}" for r in rows])
        messagebox.showinfo("Current Records", summary if summary else "No data found.")

    def export_csv(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if file_path:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute("SELECT * FROM records")
            rows = cursor.fetchall()
            with open(file_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "Item", "Amount"])
                writer.writerows(rows)
            conn.close()
            messagebox.showinfo("Exported", f"Data saved to {file_path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = BusinessApp(root)
    root.mainloop()