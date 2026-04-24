import tkinter as tk
from tkinter import messagebox

logged_in = False

users = {
    "manager": "manager123",
    "employee": "employee123",
}

def login():
    username = entry_user.get()
    password = entry_pass.get()

    # Validating users
    if username in users and users[username] == password:
        role = username.capitalize()
        window.destroy()
        global logged_in
        logged_in = True
        return role
    else:
        messagebox.showerror("Error", "Invalid login details")

window = tk.Tk()
window.title("Secure Login")
window.geometry("400x450")
window.configure(bg="#1e1e2f")
window.lift()  # ← Add this
window.focus_force()

frame = tk.Frame(window, bg="#2c2c3c", padx=30, pady=30)
frame.place(relx=0.5, rely=0.5, anchor="center")

tk.Label(
    frame,
    text="Login Portal",
    font=("Segoe UI", 18, "bold"),
    fg="white",
    bg="#2c2c3c"
).pack(pady=(0, 20))

tk.Label(frame, text="Username", fg="white", bg="#2c2c3c").pack(anchor="w")
entry_user = tk.Entry(frame, width=25, font=("Segoe UI", 10))
entry_user.pack(pady=8)

tk.Label(frame, text="Password", fg="white", bg="#2c2c3c").pack(anchor="w")
entry_pass = tk.Entry(frame, width=25, font=("Segoe UI", 10), show="*")
entry_pass.pack(pady=8)

# Login Buttons
tk.Button(
    frame,
    text="Login",
    width=20,
    bg="#4a90e2",
    fg="Black",
    font=("Segoe UI", 10, "bold",),
    relief="flat",
    command=login).pack(pady=20)

window.mainloop()

import landing_page as lp
if logged_in:
    print("Logged in")
    lp.start()