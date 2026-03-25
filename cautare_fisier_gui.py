import os
import json
import threading
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox

BASE_DIR = r"\\192.168.1.240\BT Redactional"
AN_CURENT = datetime.now().year
ANI_TRECUTI = [str(an) for an in range(2015, AN_CURENT)]
INDEX_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index_pdf.json")


def construieste_index(callback_status=None):
    index = {}
    total = len(ANI_TRECUTI)
    for i, an in enumerate(ANI_TRECUTI):
        folder = os.path.join(BASE_DIR, an)
        if callback_status:
            callback_status(i, total, "Indexez: " + an)
        fisiere_an = []
        if os.path.isdir(folder):
            for root, dirs, filenames in os.walk(folder):
                for fname in filenames:
                    if fname.lower().endswith(".pdf"):
                        fpath = os.path.join(root, fname)
                        try:
                            fisiere_an.append({
                                "cale": fpath,
                                "nume": fname.lower(),
                                "data": os.path.getmtime(fpath),
                                "size": os.path.getsize(fpath)
                            })
                        except:
                            pass
        index[an] = fisiere_an
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False)
    return index


def incarca_index():
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def cauta_in_index(index, cuvinte_lower):
    files = []
    for an, fisiere in index.items():
        for fi in fisiere:
            if cuvinte_lower in fi["nume"]:
                files.append(fi)
    return files


def cauta_an_curent(cuvinte_lower):
    files = []
    folder = os.path.join(BASE_DIR, str(AN_CURENT))
    if os.path.isdir(folder):
        for root, dirs, filenames in os.walk(folder):
            for fname in filenames:
                if fname.lower().endswith(".pdf") and cuvinte_lower in fname.lower():
                    fpath = os.path.join(root, fname)
                    try:
                        files.append({
                            "cale": fpath,
                            "nume": fname.lower(),
                            "data": os.path.getmtime(fpath),
                            "size": os.path.getsize(fpath)
                        })
                    except:
                        pass
    return files


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Cautare PDF")
        self.root.resizable(False, False)
        self.root.configure(padx=20, pady=20)
        self.index = None

        tk.Label(root, text="Cuvinte cheie:", font=("Segoe UI", 10)).grid(
            row=0, column=0, sticky="w")

        self.entry = tk.Entry(root, width=38, font=("Segoe UI", 11))
        self.entry.grid(row=1, column=0, pady=(4, 12), ipady=4)
        self.entry.bind("<Return>", lambda e: self.start_search())

        self.btn_cauta = tk.Button(root, text="Cauta", font=("Segoe UI", 10, "bold"),
                                   bg="#2563eb", fg="white", relief="flat",
                                   padx=16, pady=6, cursor="hand2",
                                   command=self.start_search)
        self.btn_cauta.grid(row=1, column=1, padx=(10, 0), pady=(4, 12))

        self.btn_index = tk.Button(root, text="Rebuild index", font=("Segoe UI", 9),
                                   bg="#e5e7eb", fg="#333", relief="flat",
                                   padx=10, pady=4, cursor="hand2",
                                   command=self.start_rebuild)
        self.btn_index.grid(row=1, column=2, padx=(6, 0), pady=(4, 12))

        self.index_var = tk.StringVar(value="")
        tk.Label(root, textvariable=self.index_var, font=("Segoe UI", 8),
                 fg="#888").grid(row=2, column=0, columnspan=3, sticky="w")

        self.status_var = tk.StringVar(value="")
        tk.Label(root, textvariable=self.status_var, font=("Segoe UI", 9),
                 fg="#555").grid(row=3, column=0, columnspan=3, sticky="w")

        self.progress = ttk.Progressbar(root, length=460, maximum=100)
        self.progress.grid(row=4, column=0, columnspan=3, pady=(4, 12))

        tk.Label(root, text="Rezultat:", font=("Segoe UI", 10)).grid(
            row=5, column=0, sticky="w")

        self.result_box = tk.Text(root, width=62, height=10, font=("Segoe UI", 9),
                                  state="disabled", bg="#f8f8f8", relief="flat",
                                  wrap="word")
        self.result_box.grid(row=6, column=0, columnspan=3, pady=(4, 0))

        self.root.after(100, self.load_index_la_start)

    def load_index_la_start(self):
        index = incarca_index()
        if index:
            self.index = index
            total = sum(len(v) for v in index.values())
            self.index_var.set("Index incarcat: " + str(total) + " PDF-uri din anii 2015-" + str(AN_CURENT - 1))
        else:
            self.index_var.set("Niciun index gasit. Apasa 'Rebuild index' pentru prima scanare.")

    def start_rebuild(self):
        self.btn_cauta.config(state="disabled")
        self.btn_index.config(state="disabled")
        self.progress["value"] = 0
        self.set_result("")

        def progres(i, total, mesaj):
            self.status_var.set(mesaj)
            self.progress["value"] = int((i + 1) / total * 100)
            self.root.update_idletasks()

        def run():
            index = construieste_index(progres)
            self.index = index
            total = sum(len(v) for v in index.values())
            self.progress["value"] = 100
            self.status_var.set("Index construit cu succes.")
            self.index_var.set("Index: " + str(total) + " PDF-uri din anii 2015-" + str(AN_CURENT - 1))
            self.btn_cauta.config(state="normal")
            self.btn_index.config(state="normal")

        threading.Thread(target=run, daemon=True).start()

    def start_search(self):
        cuvinte = self.entry.get().strip()
        if not cuvinte:
            messagebox.showwarning("Atentie", "Introdu cuvinte cheie pentru cautare.")
            return
        if not self.index:
            messagebox.showinfo("Index lipsa",
                "Indexul nu este construit inca.\nApasa 'Rebuild index' pentru prima scanare.")
            return

        self.btn_cauta.config(state="disabled")
        self.progress["value"] = 0
        self.status_var.set("Caut in index...")
        self.set_result("")

        def run():
            cuvinte_lower = cuvinte.lower()
            files = cauta_in_index(self.index, cuvinte_lower)
            self.progress["value"] = 80
            self.status_var.set("Index cautat. Scanez anul curent " + str(AN_CURENT) + "...")
            self.root.update_idletasks()

            files += cauta_an_curent(cuvinte_lower)
            self.progress["value"] = 100
            self.btn_cauta.config(state="normal")

            if not files:
                self.status_var.set("Gata. Niciun fisier gasit.")
                self.set_result("Niciun PDF gasit cu \"" + cuvinte + "\".")
                return

            files.sort(key=lambda f: f["data"], reverse=True)
            latest = files[0]
            date = datetime.fromtimestamp(latest["data"]).strftime("%Y-%m-%d %H:%M:%S")
            size = round(latest["size"] / 1024, 1)

            text = "Gasite: " + str(len(files)) + " fisier(e)\n\n"
            text += "Cel mai recent:\n"
            text += latest["cale"] + "\n"
            text += "Data: " + date + "  |  " + str(size) + " KB\n"

            if len(files) > 1:
                text += "\nToate fisierele:\n"
                for f in files:
                    d = datetime.fromtimestamp(f["data"]).strftime("%Y-%m-%d %H:%M:%S")
                    text += d + "  " + os.path.basename(f["cale"]) + "\n"

            self.status_var.set("Gata. " + str(len(files)) + " fisier(e) gasit(e).")
            self.set_result(text)

        threading.Thread(target=run, daemon=True).start()

    def set_result(self, text):
        self.result_box.config(state="normal")
        self.result_box.delete("1.0", "end")
        self.result_box.insert("end", text)
        self.result_box.config(state="disabled")


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()