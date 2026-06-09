import tkinter as tk
from tkinter import ttk, messagebox
import threading
import socket
import json
import os
import time
import struct
from PIL import Image, ImageTk
import numpy as np

# ─────────────────────────────────────────────
#  CLIENT RASPBERRY PI
# ─────────────────────────────────────────────

class ClientRasberry:
    def __init__(self):
        self.s = None
        self.connecte = False
        self.lock = threading.Lock()

    def connecter(self, ip, port=5000):
        try:
            self.s = socket.socket()
            self.s.settimeout(10)
            self.s.connect((ip, int(port)))
            self.connecte = True
            return True
        except:
            self.connecte = False
            return False

    def deconnecter(self):
        if self.s:
            try:
                self._envoyer({"action": "stop"})
            except:
                pass
            self.s.close()
        self.connecte = False

    def _envoyer(self, ordre):
        msg = json.dumps(ordre) + "\n"
        self.s.sendall(msg.encode())

    def _recevoir_reponse(self):
        data = b""
        while True:
            chunk = self.s.recv(1)
            if not chunk or chunk == b"\n":
                break
            data += chunk
        return data.decode()

    def _recevoir_fichier(self):
        taille_bytes = b""
        while len(taille_bytes) < 4:
            taille_bytes += self.s.recv(4 - len(taille_bytes))
        taille = struct.unpack(">I", taille_bytes)[0]
        donnees = b""
        while len(donnees) < taille:
            donnees += self.s.recv(min(4096, taille - len(donnees)))
        return donnees

    def allume_led(self, x, y, r=255, g=255, b=255):
        with self.lock:
            self._envoyer({"action": "allume_led",
                           "x": x, "y": y, "r": r, "g": g, "b": b})
            self._recevoir_reponse()

    def eteint_led(self, x, y):
        with self.lock:
            self._envoyer({"action": "eteint_led", "x": x, "y": y})
            self._recevoir_reponse()

    def eteint_tout(self):
        with self.lock:
            self._envoyer({"action": "eteint_tout"})
            self._recevoir_reponse()

    def prendre_photo(self, nom, expo="50000"):
        with self.lock:
            self._envoyer({"action": "photo", "nom": nom, "expo": expo})
            donnees = self._recevoir_fichier()
        return donnees


# ─────────────────────────────────────────────
#  MODE SIMULATION
# ─────────────────────────────────────────────

class ClientSimule:
    def __init__(self):
        self.connecte = True

    def connecter(self, ip, port=5000):
        self.connecte = True
        return True

    def deconnecter(self):
        self.connecte = False

    def allume_led(self, x, y, r=255, g=255, b=255):
        time.sleep(0.01)

    def eteint_led(self, x, y):
        pass

    def eteint_tout(self):
        pass

    def prendre_photo(self, nom, expo="50000"):
        img = Image.fromarray(
            np.random.randint(100, 200, (480, 640), dtype=np.uint8))
        buf = __import__('io').BytesIO()
        img.save(buf, format="JPEG")
        time.sleep(0.05)
        return buf.getvalue()


# ─────────────────────────────────────────────
#  FICHIER CONFIG
# ─────────────────────────────────────────────

CONFIG_FILE = "fpm_config.json"

CONFIG_DEFAUT = {
    "expo":       "50000",
    "espacement": "1",
    "NA":         "0.10",
    "Mag":        "4",
    "lambda_um":  "0.532",
    "h_mm":       "87.5",
    "D_LED_mm":   "2.5",
    "pixel_um":   "6.5",
    "dossier":    "Images",
}


# ─────────────────────────────────────────────
#  APPLICATION
# ─────────────────────────────────────────────

class AppFPM(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FPM Controller")
        self.geometry("1100x740")
        self.configure(bg="#f5f5f5")

        self.client = ClientSimule()
        self.mode_simule = True
        self.acquisition_active = False
        self.images_capturees = []
        self.ordre_leds = self._calculer_ordre_serpentin()

        self._construire_ui()
        self._charger_config()

    def _calculer_ordre_serpentin(self):
        ordre = []
        for i in range(16):
            start = i * 16 + 1
            end = (i + 1) * 16
            if i % 2 == 0:
                ordre += [(i, j, n) for j, n in
                          enumerate(range(start, end+1))]
            else:
                ordre += [(i, j, n) for j, n in
                          enumerate(range(end, start-1, -1))]
        return ordre

    # ── Config ────────────────────────────────

    def _charger_config(self):
        """Charge la config depuis le fichier JSON"""
        config = CONFIG_DEFAUT.copy()
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE) as f:
                    config.update(json.load(f))
            except:
                pass

        # Remplir les champs
        self.entry_expo.delete(0, tk.END)
        self.entry_expo.insert(0, config["expo"])
        self.entry_espacement.delete(0, tk.END)
        self.entry_espacement.insert(0, config["espacement"])
        self.entry_na.delete(0, tk.END)
        self.entry_na.insert(0, config["NA"])
        self.entry_mag.delete(0, tk.END)
        self.entry_mag.insert(0, config["Mag"])
        self.entry_lambda.delete(0, tk.END)
        self.entry_lambda.insert(0, config["lambda_um"])
        self.entry_h.delete(0, tk.END)
        self.entry_h.insert(0, config["h_mm"])
        self.entry_dled.delete(0, tk.END)
        self.entry_dled.insert(0, config["D_LED_mm"])
        self.entry_pixel.delete(0, tk.END)
        self.entry_pixel.insert(0, config["pixel_um"])
        self.entry_dossier.delete(0, tk.END)
        self.entry_dossier.insert(0, config["dossier"])

    def _sauvegarder_config(self):
        """Sauvegarde la config dans le fichier JSON"""
        config = {
            "expo":       self.entry_expo.get(),
            "espacement": self.entry_espacement.get(),
            "NA":         self.entry_na.get(),
            "Mag":        self.entry_mag.get(),
            "lambda_um":  self.entry_lambda.get(),
            "h_mm":       self.entry_h.get(),
            "D_LED_mm":   self.entry_dled.get(),
            "pixel_um":   self.entry_pixel.get(),
            "dossier":    self.entry_dossier.get(),
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)

        self.lbl_config_status.config(
            text="✓ Config sauvegardée", fg="#2a9d2a")
        self.after(2000, lambda: self.lbl_config_status.config(text=""))

    # ── UI ────────────────────────────────────

    def _construire_ui(self):
        # Barre haute
        barre = tk.Frame(self, bg="#ffffff", height=50)
        barre.pack(fill="x", side="top")
        barre.pack_propagate(False)

        tk.Label(barre, text="FPM Controller", bg="#ffffff",
                 font=("Helvetica", 14, "bold"),
                 fg="#222222").pack(side="left", padx=20, pady=12)

        self.lbl_connexion = tk.Label(
            barre, text="● Mode simulation",
            bg="#ffffff", font=("Helvetica", 10), fg="#f0a500")
        self.lbl_connexion.pack(side="right", padx=20)

        tk.Button(barre, text="⚙ Setup Raspberry",
                  bg="#ffffff", fg="#333333",
                  font=("Helvetica", 10), relief="flat",
                  cursor="hand2",
                  command=self._ouvrir_setup).pack(side="right", padx=5)

        # Corps
        corps = tk.Frame(self, bg="#f5f5f5")
        corps.pack(fill="both", expand=True, padx=16, pady=12)

        col_gauche = tk.Frame(corps, bg="#f5f5f5")
        col_gauche.pack(side="left", fill="both", expand=True)

        col_droite = tk.Frame(corps, bg="#f5f5f5", width=310)
        col_droite.pack(side="right", fill="y", padx=(12, 0))
        col_droite.pack_propagate(False)

        self._construire_apercu(col_gauche)
        self._construire_grille(col_gauche)
        self._construire_panneau_droite(col_droite)

    def _construire_apercu(self, parent):
        card = tk.Frame(parent, bg="#ffffff",
                        highlightbackground="#dddddd",
                        highlightthickness=1)
        card.pack(fill="both", expand=True, pady=(0, 10))

        en_tete = tk.Frame(card, bg="#ffffff")
        en_tete.pack(fill="x", padx=12, pady=8)

        tk.Label(en_tete, text="Dernière image capturée",
                 bg="#ffffff", font=("Helvetica", 11, "bold"),
                 fg="#222222").pack(side="left")

        self.lbl_nom_image = tk.Label(
            en_tete, text="", bg="#ffffff",
            font=("Helvetica", 9), fg="#888888")
        self.lbl_nom_image.pack(side="right")

        self.canvas_img = tk.Canvas(card, bg="#1a1a1a",
                                     width=500, height=280)
        self.canvas_img.pack(padx=12, pady=(0, 12))
        self.canvas_img.create_text(
            250, 140, text="Aucune image capturée",
            fill="#555555", font=("Helvetica", 12))

    def _construire_grille(self, parent):
        card = tk.Frame(parent, bg="#ffffff",
                        highlightbackground="#dddddd",
                        highlightthickness=1)
        card.pack(fill="x", pady=(0, 10))

        tk.Label(card, text="Tableau LED 16×16",
                 bg="#ffffff", font=("Helvetica", 11, "bold"),
                 fg="#222222").pack(anchor="w", padx=12, pady=8)

        grille_frame = tk.Frame(card, bg="#ffffff")
        grille_frame.pack(padx=12, pady=(0, 12))

        self.cellules = {}
        for i in range(16):
            for j in range(16):
                c = tk.Canvas(grille_frame, width=18, height=18,
                               bg="#222222", highlightthickness=1,
                               highlightbackground="#333333",
                               cursor="hand2")
                c.grid(row=i, column=j, padx=1, pady=1)
                c.bind("<Button-1>",
                        lambda e, x=j, y=i: self._clic_led(x, y))
                self.cellules[(j, i)] = c

        self._colorier_led(7, 7, "#00cc44")

    def _construire_panneau_droite(self, parent):
        # ── Paramètres ────────────────────────
        card = tk.Frame(parent, bg="#ffffff",
                         highlightbackground="#dddddd",
                         highlightthickness=1)
        card.pack(fill="x", pady=(0, 8))

        en_tete = tk.Frame(card, bg="#ffffff")
        en_tete.pack(fill="x", padx=12, pady=(10, 6))

        tk.Label(en_tete, text="Paramètres",
                 bg="#ffffff", font=("Helvetica", 11, "bold"),
                 fg="#222222").pack(side="left")

        # Bouton sauvegarder config
        tk.Button(en_tete, text="💾 Sauvegarder",
                  command=self._sauvegarder_config,
                  bg="#f0f0f0", fg="#333333",
                  font=("Helvetica", 8), relief="flat",
                  cursor="hand2", padx=6, pady=2).pack(side="right")

        def champ(label, valeur=""):
            f = tk.Frame(card, bg="#ffffff")
            f.pack(fill="x", padx=12, pady=2)
            tk.Label(f, text=label, bg="#ffffff",
                     font=("Helvetica", 9), fg="#555555",
                     width=18, anchor="w").pack(side="left")
            e = tk.Entry(f, font=("Helvetica", 9),
                         width=10, relief="solid", bd=1)
            e.pack(side="right")
            return e

        self.entry_expo       = champ("Exposition (µs)")
        self.entry_espacement = champ("Pas LEDs")
        self.entry_na         = champ("NA objectif")
        self.entry_mag        = champ("Grossissement")
        self.entry_lambda     = champ("λ (µm)")
        self.entry_h          = champ("Distance LED (mm)")
        self.entry_dled       = champ("Espacement LED (mm)")
        self.entry_pixel      = champ("Taille pixel (µm)")
        self.entry_dossier    = champ("Dossier images")

        self.lbl_config_status = tk.Label(
            card, text="", bg="#ffffff",
            font=("Helvetica", 8), fg="#2a9d2a")
        self.lbl_config_status.pack(pady=(0, 8))

        # ── Contrôles ─────────────────────────
        card2 = tk.Frame(parent, bg="#ffffff",
                          highlightbackground="#dddddd",
                          highlightthickness=1)
        card2.pack(fill="x", pady=(0, 8))

        tk.Label(card2, text="Contrôle",
                 bg="#ffffff", font=("Helvetica", 11, "bold"),
                 fg="#222222").pack(anchor="w", padx=12, pady=(10, 6))

        def bouton(texte, cmd, fg="#333333", bg="#f0f0f0"):
            tk.Button(card2, text=texte, command=cmd,
                      bg=bg, fg=fg, font=("Helvetica", 10),
                      relief="flat", cursor="hand2",
                      padx=10, pady=5).pack(
                fill="x", padx=12, pady=2)

        bouton("TEST (LED centrale)", self._test_led)
        bouton("AUTO — lancer acquisition",
               self._lancer_acquisition,
               fg="#ffffff", bg="#1a6bb5")
        bouton("STOP", self._stop_acquisition,
               fg="#ffffff", bg="#cc3333")
        bouton("SAVE images + paramètres",
               self._sauvegarder_tout)

        tk.Frame(card2, bg="#ffffff", height=8).pack()

        # ── Progression ───────────────────────
        card3 = tk.Frame(parent, bg="#ffffff",
                          highlightbackground="#dddddd",
                          highlightthickness=1)
        card3.pack(fill="x")

        tk.Label(card3, text="Progression",
                 bg="#ffffff", font=("Helvetica", 11, "bold"),
                 fg="#222222").pack(anchor="w", padx=12, pady=(10, 4))

        self.progress = ttk.Progressbar(
            card3, length=280, mode="determinate")
        self.progress.pack(padx=12, pady=4)

        self.lbl_prog = tk.Label(
            card3, text="0 / 0 images",
            bg="#ffffff", font=("Helvetica", 9), fg="#777777")
        self.lbl_prog.pack(padx=12, pady=(0, 10))

    # ── Actions ───────────────────────────────

    def _ouvrir_setup(self):
        win = tk.Toplevel(self)
        win.title("Setup Raspberry Pi")
        win.geometry("380x260")
        win.configure(bg="#f5f5f5")
        win.resizable(False, False)

        tk.Label(win, text="Connexion Raspberry Pi",
                 bg="#f5f5f5",
                 font=("Helvetica", 12, "bold"),
                 fg="#222222").pack(pady=(20, 16))

        frame = tk.Frame(win, bg="#f5f5f5")
        frame.pack(padx=30, fill="x")

        tk.Label(frame, text="Adresse IP :", bg="#f5f5f5",
                 font=("Helvetica", 10),
                 fg="#444444").pack(anchor="w")
        entry_ip = tk.Entry(frame, font=("Helvetica", 10),
                             relief="solid", bd=1)
        entry_ip.insert(0, "192.168.10.2")
        entry_ip.pack(fill="x", pady=4)

        tk.Label(frame, text="Port :", bg="#f5f5f5",
                 font=("Helvetica", 10),
                 fg="#444444").pack(anchor="w")
        entry_port = tk.Entry(frame, font=("Helvetica", 10),
                               relief="solid", bd=1)
        entry_port.insert(0, "5000")
        entry_port.pack(fill="x", pady=4)

        lbl_status = tk.Label(win, text="", bg="#f5f5f5",
                               font=("Helvetica", 9))
        lbl_status.pack(pady=8)

        def tenter():
            ip = entry_ip.get().strip()
            port = entry_port.get().strip()
            lbl_status.config(text="Connexion...", fg="#f0a500")
            win.update()
            c = ClientRasberry()
            if c.connecter(ip, port):
                self.client = c
                self.mode_simule = False
                self.lbl_connexion.config(
                    text=f"● Connecté ({ip})", fg="#2a9d2a")
                lbl_status.config(text="Connecté !", fg="#2a9d2a")
                win.after(1000, win.destroy)
            else:
                lbl_status.config(
                    text="Échec. Vérifiez IP/port.", fg="#cc3333")

        def sim():
            self.client = ClientSimule()
            self.mode_simule = True
            self.lbl_connexion.config(
                text="● Mode simulation", fg="#f0a500")
            win.destroy()

        tk.Button(win, text="Se connecter", command=tenter,
                  bg="#1a6bb5", fg="#ffffff",
                  font=("Helvetica", 10), relief="flat",
                  cursor="hand2", padx=10, pady=6).pack(pady=4)

        tk.Button(win, text="Continuer en simulation",
                  command=sim, bg="#f0f0f0", fg="#333333",
                  font=("Helvetica", 9), relief="flat",
                  cursor="hand2").pack()

    def _colorier_led(self, x, y, couleur):
        c = self.cellules.get((x, y))
        if c:
            c.configure(bg=couleur)

    def _clic_led(self, x, y):
        if not self.client.connecte:
            return
        self._colorier_led(x, y, "#ffdd00")
        def tache():
            self.client.allume_led(x, y)
            time.sleep(1)
            self.client.eteint_led(x, y)
            self.after(0, lambda: self._colorier_led(x, y, "#222222"))
        threading.Thread(target=tache, daemon=True).start()

    def _test_led(self):
        if not self.client.connecte:
            messagebox.showwarning("Non connecté",
                                    "Connectez-vous d'abord.")
            return
        def tache():
            self.client.allume_led(7, 7)
            self._colorier_led(7, 7, "#ffdd00")
            time.sleep(1)
            self.client.eteint_led(7, 7)
            self.after(0, lambda: self._colorier_led(7, 7, "#00cc44"))
        threading.Thread(target=tache, daemon=True).start()

    def _lancer_acquisition(self):
        if self.acquisition_active:
            return
        if not self.client.connecte:
            messagebox.showwarning("Non connecté",
                                    "Connectez-vous d'abord.")
            return
        self.acquisition_active = True
        self.images_capturees = []
        self.progress["value"] = 0
        pas = int(self.entry_espacement.get() or 1)
        dossier = self.entry_dossier.get() or "Images"
        os.makedirs(dossier, exist_ok=True)
        threading.Thread(
            target=self._acquisition_thread,
            args=(pas, dossier), daemon=True).start()

    def _acquisition_thread(self, pas, dossier):
        leds = self.ordre_leds[::pas]
        total = len(leds)

        for idx, (i, j, num) in enumerate(leds):
            if not self.acquisition_active:
                break

            x, y = j, i
            expo = self.entry_expo.get()

            # Allume LED
            self.client.allume_led(x, y)
            self.after(0, lambda cx=x, cy=y:
                        self._colorier_led(cx, cy, "#ffdd00"))

            # Nom du fichier avec position LED
            # Format : Image_num{N}_x{X}_y{Y}.jpeg
            nom_fichier = f"Image_num{num}_x{x}_y{y}"
            nom_serveur = nom_fichier  # nom envoyé à la Raspberry

            # Prendre la photo et récupérer les données
            donnees = self.client.prendre_photo(nom_serveur, expo)

            # Sauvegarder sur le PC avec position dans le nom
            chemin_pc = os.path.join(dossier, f"{nom_fichier}.jpeg")
            with open(chemin_pc, "wb") as f:
                f.write(donnees)

            self.images_capturees.append({
                "num":    num,
                "x":      x,
                "y":      y,
                "fichier": f"{nom_fichier}.jpeg",
                "chemin": chemin_pc,
            })

            # Afficher l'image
            self.after(0, lambda d=donnees, n=nom_fichier:
                        self._afficher_image_bytes(d, n))

            # Éteint LED
            self.client.eteint_led(x, y)
            self.after(0, lambda cx=x, cy=y:
                        self._colorier_led(cx, cy, "#222222"))

            # Progression
            pct = int((idx + 1) / total * 100)
            self.after(0, lambda p=pct, n=idx+1, t=total:
                        self._maj_progression(p, n, t))

        self.acquisition_active = False
        self.after(0, self._acquisition_terminee)

    def _afficher_image_bytes(self, donnees, nom):
        try:
            import io
            img = Image.open(io.BytesIO(donnees))
            img = img.resize((500, 280))
            photo = ImageTk.PhotoImage(img)
            self.canvas_img.image = photo
            self.canvas_img.create_image(0, 0, anchor="nw", image=photo)
            self.lbl_nom_image.config(text=nom)
        except:
            pass

    def _maj_progression(self, pct, n, total):
        self.progress["value"] = pct
        self.lbl_prog.config(text=f"{n} / {total} images")

    def _acquisition_terminee(self):
        messagebox.showinfo(
            "Terminé",
            f"{len(self.images_capturees)} images capturées !\n"
            f"Dossier : {self.entry_dossier.get()}")

    def _stop_acquisition(self):
        self.acquisition_active = False

    def _sauvegarder_tout(self):
        """Sauvegarde config + métadonnées images"""
        if not self.images_capturees:
            messagebox.showwarning(
                "Rien à sauvegarder",
                "Lancez d'abord une acquisition.")
            return

        # 1. Sauvegarder la config
        self._sauvegarder_config()

        # 2. Sauvegarder les métadonnées
        dossier = self.entry_dossier.get() or "Images"
        os.makedirs(dossier, exist_ok=True)

        metadonnees = {
            "parametres": {
                "NA":        self.entry_na.get(),
                "Mag":       self.entry_mag.get(),
                "lambda_um": self.entry_lambda.get(),
                "h_mm":      self.entry_h.get(),
                "D_LED_mm":  self.entry_dled.get(),
                "pixel_um":  self.entry_pixel.get(),
                "expo_us":   self.entry_expo.get(),
            },
            "images": self.images_capturees
            # Chaque image contient :
            # num, x, y, fichier (ex: Image_num1_x0_y0.jpeg)
        }

        chemin_meta = os.path.join(dossier, "metadata.json")
        with open(chemin_meta, "w") as f:
            json.dump(metadonnees, f, indent=2)

        messagebox.showinfo(
            "Sauvegardé",
            f"✓ Config sauvegardée dans fpm_config.json\n"
            f"✓ {len(self.images_capturees)} images dans {dossier}/\n"
            f"✓ Métadonnées dans {dossier}/metadata.json\n\n"
            f"Nom des images :\n"
            f"Image_num{{N}}_x{{X}}_y{{Y}}.jpeg")


if __name__ == "__main__":
    app = AppFPM()
    app.mainloop()