import os
import threading
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox

BASE_DIR = r"\\192.168.1.240\BT Redactional"
ANI = [str(an) for an in range(2015, 2027)]


def cauta_fisiere(cuvinte_lower, callback_progres, callback_rezultat):
    files = []
    for i, an in enumerate(ANI):
        folder = os.path.join(BASE_DIR, an)
        callback_progres(i, an)
        if os.path.isdir(folder):
            for root, dirs, filenames in os.walk(folder):
                for fname in filenames:
                    if fname.lower().endswith(".pdf") and cuvinte_lower in fname.lower():
                        files.append(os.path.join(root, fname))
    callback_rezultat(files)


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Cautare PDF")
        self.root.resizable(False, False)
        self.root.configure(padx=20, pady=20)

        # Camp cautare
        tk.Label(root, text="Cuvinte cheie:", font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w")
        self.entry = tk.Entry(root, width=40, font=("Segoe UI", 11))
        self.entry.grid(row=1, column=0, pady=(4, 12), ipady=4)
        self.entry.bind("<Return>", lambda e: self.start_search())

        # Buton
        self.btn = tk.Button(root, text="Cauta", font=("Segoe UI", 10, "bold"),
                             bg="#2563eb", fg="white", relief="flat",
                             padx=16, pady=6, cursor="hand2",
                             command=self.start_search)
        self.btn.grid(row=1, column=1, padx=(10, 0), pady=(4, 12))

        # Status
        self.status_var = tk.StringVar(value="")
        tk.Label(root, textvariable=self.status_var, font=("Segoe UI", 9),
                 fg="#555").grid(row=2, column=0, columnspan=2, sticky="w")

        # Progress bar
        self.progress = ttk.Progressbar(root, length=380, maximum=len(ANI))
        self.progress.grid(row=3, column=0, columnspan=2, pady=(4, 12))

        # Rezultat
        tk.Label(root, text="Rezultat:", font=("Segoe UI", 10)).grid(row=4, column=0, sticky="w")
        self.result_box = tk.Text(root, width=52, height=8, font=("Segoe UI", 9),
                                  state="disabled", bg="#f8f8f8", relief="flat",
                                  wrap="word")
        self.result_box.grid(row=5, column=0, columnspan=2, pady=(4, 0))

    def start_search(self):
        cuvinte = self.entry.get().strip()
        if not cuvinte:
            messagebox.showwarning("Atentie", "Introdu cuvinte cheie pentru cautare.")
            return

        self.btn.config(state="disabled")
        self.progress["value"] = 0
        self.status_var.set("Se cauta...")
        self.set_result("")

        def progres(i, an):
            self.progress["value"] = i + 1
            self.status_var.set("Caut in: " + an + " (" + str(i + 1) + "/" + str(len(ANI)) + ")")
            self.root.update_idletasks()

        def rezultat(files):
            self.progress["value"] = len(ANI)
            self.btn.config(state="normal")

            if not files:
                self.status_var.set("Gata. Niciun fisier gasit.")
                self.set_result("Niciun PDF gasit cu \"" + cuvinte + "\".")
                return

            files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
            latest = files[0]
            date = datetime.fromtimestamp(os.path.getmtime(latest)).strftime("%Y-%m-%d %H:%M:%S")
            size = round(os.path.getsize(latest) / 1024, 1)

            text = "Gasite: " + str(len(files)) + " fisier(e)\n\n"
            text += "Cel mai recent:\n"
            text += latest + "\n"
            text += "Data: " + date + "  |  " + str(size) + " KB\n"

            if len(files) > 1:
                text += "\nToate fisierele:\n"
                for f in files:
                    d = datetime.fromtimestamp(os.path.getmtime(f)).strftime("%Y-%m-%d %H:%M:%S")
                    text += d + "  " + os.path.basename(f) + "\n"

            self.status_var.set("Gata. " + str(len(files)) + " fisier(e) gasit(e).")
            self.set_result(text)

        threading.Thread(
            target=cauta_fisiere,
            args=(cuvinte.lower(), progres, rezultat),
            daemon=True
        ).start()

    def set_result(self, text):
        self.result_box.config(state="normal")
        self.result_box.delete("1.0", "end")
        self.result_box.insert("end", text)
        self.result_box.config(state="disabled")


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()