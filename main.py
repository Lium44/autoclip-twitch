import customtkinter as ctk
import requests
import threading
import json
import os
import time
import sys
import winsound
import random
from tkinter import colorchooser
from pynput import keyboard
import traceback

# --- PARAMÈTRES DE STYLE ---
COLOR_BG = "#0F0F0F"        # Noir profond
COLOR_CARD = "#1A1A1A"      # Gris/Noir carte
COLOR_PINK = "#FF2E63"      # Rose vif
COLOR_PURPLE = "#8A2BE2"    # Violet électrique
COLOR_WHITE = "#FFFFFF"     # Blanc

class ConsoleRedirector:
    """Redirige les flux stdout/stderr vers le widget Textbox de l'app."""
    def __init__(self, textbox, app):
        self.textbox = textbox
        self.app = app

    def write(self, text):
        def _append():
            self.textbox.configure(state="normal")
            self.textbox.insert("end", text)
            self.textbox.configure(state="disabled")
            self.textbox.see("end")
        self.app.after(0, _append)

    def flush(self):
        pass

class TwitchAutoClipper(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Variables
        self.config_file = "config.json"
        self.clips_file = "clips_sauvegardes.txt"
        self.is_running = False
        self.listener = None
        self.auto_thread = None
        self.input_entries = []
        self.load_config() # Charger la config en premier
        self.current_pink = self.saved_config.get("color_pink", COLOR_PINK)
        self.current_purple = self.saved_config.get("color_purple", COLOR_PURPLE)

        self.title("Twitch Clip made by Lium")
        self.geometry("600x900")
        self.configure(fg_color=COLOR_BG)
        
        # Canvas pour l'animation de fond
        self.canvas = ctk.CTkCanvas(self, bg=COLOR_BG, highlightthickness=0)
        self.canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.particles = []
        self.init_background_animation()

        try:
            self.iconbitmap("ton_icone.ico")
        except Exception:
            pass # L'icône est optionnelle si le fichier est manquant

        self.setup_ui()
        self.animate()

    def init_background_animation(self):
        """Initialise des particules pour le fond."""
        p_color = self.saved_config.get("color_pink", COLOR_PINK)
        v_color = self.saved_config.get("color_purple", COLOR_PURPLE)
        for _ in range(25):
            x = random.randint(0, 600)
            y = random.randint(0, 900)
            size = random.randint(2, 5)
            color = random.choice([p_color, v_color])
            speed = random.uniform(0.5, 1.5)
            p = self.canvas.create_oval(x, y, x+size, y+size, fill=color, outline="")
            self.particles.append({'id': p, 'x': x, 'y': y, 'speed': speed, 'size': size})

    def animate(self):
        """Boucle d'animation du fond."""
        for p in self.particles:
            p['y'] -= p['speed']
            if p['y'] < -10:
                p['y'] = 910
                p['x'] = random.randint(0, 600)
            self.canvas.coords(p['id'], p['x'], p['y'], p['x']+p['size'], p['y']+p['size'])
        self.after(30, self.animate)

    def setup_ui(self):
        # Récupération des couleurs depuis la config
        p_color = self.saved_config.get("color_pink", COLOR_PINK)
        v_color = self.saved_config.get("color_purple", COLOR_PURPLE)

        # Titre
        self.label_title = ctk.CTkLabel(self, text="TWITCH CLIPPER PRO", font=("Orbitron", 32, "bold"), text_color=p_color)
        self.label_title.pack(pady=20)
        
        self.label_subtitle = ctk.CTkLabel(self, text="made by Lium", font=("Arial", 14, "italic"), text_color=COLOR_WHITE)
        self.label_subtitle.pack(pady=(0, 10))

        # Système d'onglets moderne
        self.tabview = ctk.CTkTabview(self, fg_color=COLOR_CARD, 
                                      segmented_button_selected_color=v_color, 
                                      segmented_button_selected_hover_color=p_color, 
                                      border_width=2, border_color=v_color)
        self.tabview.pack(padx=30, pady=10, fill="both", expand=True)
        self.tabview.add("Connexion")
        self.tabview.add("Configuration")
        self.tabview.add("Couleurs")

        # --- ONGLET CONNEXION ---
        self.create_input("Twitch Client ID", "entry_client_id", self.saved_config.get("client_id", ""), tab="Connexion")
        self.create_input("OAuth Access Token", "entry_token", self.saved_config.get("token", ""), show="*", tab="Connexion")
        self.create_input("Nom de la Chaîne", "entry_username", self.saved_config.get("username", ""), tab="Connexion")
        
        self.btn_fetch = ctk.CTkButton(self.tabview.tab("Connexion"), text="VÉRIFIER & RÉCUPÉRER L'ID", 
                                        fg_color="transparent", border_width=1, border_color=p_color,
                                        hover_color=p_color, text_color=COLOR_WHITE,
                                        font=("Arial", 13, "bold"),
                                        command=self.fetch_broadcaster_id)
        self.btn_fetch.pack(pady=15, padx=20, fill="x")
        self.create_input("ID Broadcaster (Auto)", "entry_bid", self.saved_config.get("broadcaster_id", ""), tab="Connexion")

        # --- ONGLET CONFIGURATION ---
        self.create_input("Raccourci Clavier (Hotkey)", "entry_hotkey", self.saved_config.get("hotkey", "e"), tab="Configuration")
        
        self.btn_capture = ctk.CTkButton(self.tabview.tab("Configuration"), text="ENREGISTRER UNE TOUCHE", 
                                        fg_color="transparent", border_width=1, border_color=p_color,
                                        hover_color=p_color, text_color=COLOR_WHITE,
                                        font=("Arial", 12, "bold"), command=self.start_hotkey_capture)
        self.btn_capture.pack(pady=(0, 10), padx=20, fill="x")

        self.create_input("Durée du Clip (sec)", "entry_duration", self.saved_config.get("duration", "30"), tab="Configuration")
        
        self.auto_mode_var = ctk.BooleanVar(value=self.saved_config.get("auto_mode", False))
        self.check_auto = ctk.CTkCheckBox(self.tabview.tab("Configuration"), text="Activer l'Auto-Clipping", 
                                         variable=self.auto_mode_var, text_color=COLOR_WHITE, 
                                         fg_color=v_color, hover_color=p_color, font=("Arial", 13, "bold"))
        self.check_auto.pack(pady=15, padx=20, anchor="w")
        
        self.create_input("Intervalle Timer (sec)", "entry_interval", self.saved_config.get("interval", "300"), tab="Configuration")

        # --- ONGLET COULEURS ---
        ctk.CTkLabel(self.tabview.tab("Couleurs"), text="Personnalisation visuelle", font=("Arial", 16, "bold"), text_color=p_color).pack(pady=10)
        
        self.btn_pick_pink = ctk.CTkButton(self.tabview.tab("Couleurs"), text="Choisir Couleur Rose (Accent 1)", 
                                            fg_color=self.current_pink, hover_color=self.current_pink,
                                            text_color=COLOR_WHITE, command=lambda: self.pick_color("pink"))
        self.btn_pick_pink.pack(pady=15, padx=20, fill="x")

        self.btn_pick_purple = ctk.CTkButton(self.tabview.tab("Couleurs"), text="Choisir Couleur Violet (Accent 2)", 
                                              fg_color=self.current_purple, hover_color=self.current_purple,
                                              text_color=COLOR_WHITE, command=lambda: self.pick_color("purple"))
        self.btn_pick_purple.pack(pady=15, padx=20, fill="x")

        ctk.CTkLabel(self.tabview.tab("Couleurs"), text="Les changements s'appliquent en temps réel.", font=("Arial", 11, "italic"), text_color="gray").pack(pady=10)

        self.btn_toggle = ctk.CTkButton(self.tabview.tab("Configuration"), text="DÉMARRER L'AUTOCLIPPER", 
                                        fg_color=v_color, hover_color=p_color,
                                        font=("Arial", 18, "bold"), height=50,
                                        command=self.toggle_service)
        self.btn_toggle.pack(pady=20, padx=40, fill="x")

        # Bouton pour ouvrir le fichier de clips
        self.btn_open_file = ctk.CTkButton(self.tabview.tab("Configuration"), text="OUVRIR L'HISTORIQUE (TXT)", 
                                            fg_color="transparent", border_width=1, border_color=COLOR_WHITE,
                                            hover_color="#333333", text_color=COLOR_WHITE,
                                            command=self.open_clips_file)
        self.btn_open_file.pack(pady=10, padx=40, fill="x")

        # Zone de Log/Console (Fixe en bas, hors du scroll pour être toujours visible)
        self.log_box = ctk.CTkTextbox(self, height=180, fg_color="#000000", text_color=COLOR_WHITE, corner_radius=10)
        self.log_box.pack(pady=(10, 20), padx=30, fill="x")
        self.log_box.configure(state="disabled")

        # Redirection de la console vers l'interface
        sys.stdout = ConsoleRedirector(self.log_box, self)
        sys.stderr = ConsoleRedirector(self.log_box, self)

        self.log("Système prêt.")

    def pick_color(self, color_type):
        """Ouvre un sélecteur de couleur et met à jour l'interface."""
        initial = self.current_pink if color_type == "pink" else self.current_purple
        color = colorchooser.askcolor(title="Choisir une couleur", initialcolor=initial)[1]
        
        if color:
            if color_type == "pink":
                self.current_pink = color
                self.btn_pick_pink.configure(fg_color=color, hover_color=color)
            else:
                self.current_purple = color
                self.btn_pick_purple.configure(fg_color=color, hover_color=color)
            
            self.apply_colors()
            self.save_config()

    def apply_colors(self):
        """Met à jour les couleurs de l'interface en temps réel."""
        p_color = self.current_pink
        v_color = self.current_purple

        self.label_title.configure(text_color=p_color)
        self.tabview.configure(segmented_button_selected_color=v_color, 
                             segmented_button_selected_hover_color=p_color, 
                             border_color=v_color)
        self.btn_fetch.configure(border_color=p_color, hover_color=p_color)
        self.btn_capture.configure(border_color=p_color, hover_color=p_color)
        self.check_auto.configure(fg_color=v_color, hover_color=p_color)
        
        toggle_color = p_color if self.is_running else v_color
        self.btn_toggle.configure(fg_color=toggle_color, hover_color=p_color)
        
        for entry in self.input_entries:
            entry.configure(border_color=v_color)

    def _get_clean_token(self):
        """Récupère et nettoie le token d'accès."""
        tok = self.entry_token.get().strip()
        if tok.lower().startswith("oauth:"):
            tok = tok[6:].strip()
        return tok

    def open_clips_file(self):
        """Ouvre le fichier texte contenant les liens des clips."""
        if os.path.exists(self.clips_file):
            os.startfile(self.clips_file)
        else:
            self.log("Le fichier d'historique n'existe pas encore.")

    def create_input(self, label_text, var_name, default_val, show=None, tab="Connexion"):
        v_color = self.saved_config.get("color_purple", COLOR_PURPLE)
        parent = self.tabview.tab(tab)
        label = ctk.CTkLabel(parent, text=label_text, text_color=COLOR_WHITE, font=("Arial", 12))
        label.pack(pady=(10, 0), padx=20, anchor="w")
        entry = ctk.CTkEntry(parent, fg_color="#2B2B2B", border_color=v_color, text_color=COLOR_WHITE, show=show)
        entry.insert(0, default_val)
        entry.pack(pady=(2, 10), padx=20, fill="x")
        setattr(self, var_name, entry)
        self.input_entries.append(entry)
        return entry

    def log(self, message):
        """Affiche un message dans la console de l'interface de façon sécurisée (Thread-safe)."""
        def _append():
            self.log_box.configure(state="normal")
            self.log_box.insert("end", f"> {message}\n")
            self.log_box.configure(state="disabled")
            self.log_box.see("end")
        self.after(0, _append)

    def save_config(self):
        """Sauvegarde les paramètres actuels dans le fichier JSON."""
        config = {
            "client_id": self.entry_client_id.get(),
            "token": self.entry_token.get(),
            "username": self.entry_username.get(),
            "broadcaster_id": self.entry_bid.get(),
            "hotkey": self.entry_hotkey.get(),
            "auto_mode": self.auto_mode_var.get(),
            "interval": self.entry_interval.get(),
            "duration": self.entry_duration.get(),
            "color_pink": self.current_pink,
            "color_purple": self.current_purple
        }
        with open(self.config_file, "w") as f:
            json.dump(config, f)

    def fetch_broadcaster_id(self):
        """Récupère l'ID numérique à partir du nom d'utilisateur via l'API Twitch"""
        username = self.entry_username.get().strip()
        client_id = self.entry_client_id.get().strip()
        token = self._get_clean_token()

        if not username or not client_id or not token:
            self.log("Erreur: Client ID, Token et Nom requis !")
            return

        url = f"https://api.twitch.tv/helix/users?login={username}"
        headers = {"Client-Id": client_id, "Authorization": f"Bearer {token}"}

        try:
            res = requests.get(url, headers=headers, timeout=5)
            if res.status_code == 200:
                data = res.json()
                if data['data']:
                    user_id = data['data'][0]['id']
                    self.entry_bid.delete(0, "end")
                    self.entry_bid.insert(0, user_id)
                    self.log(f"ID trouvé pour {username}: {user_id}")
                else:
                    self.log(f"Utilisateur '{username}' non trouvé.")
            else:
                try:
                    error_msg = res.json().get('message', 'Détails indisponibles')
                    self.log(f"Erreur API {res.status_code}: {error_msg}")
                except:
                    self.log(f"Erreur API {res.status_code}")
        except Exception:
            self.log(f"CRASH FETCH ID:\n{traceback.format_exc()}")

    def start_hotkey_capture(self):
        """Lance l'écoute pour capturer une combinaison de touches (ex: Ctrl+Alt+C)."""
        p_color = self.entry_color_pink.get().strip()
        self.btn_capture.configure(text="Maintenez votre combinaison...", state="disabled", fg_color=p_color)
        self.entry_hotkey.delete(0, "end")
        
        captured_keys = []
        currently_pressed = set()

        def on_press(key):
            if hasattr(key, 'char') and key.char:
                k = key.char
            else:
                clean_name = str(key).replace('Key.', '')
                mapping = {
                    "ctrl_l": "ctrl", "ctrl_r": "ctrl",
                    "alt_l": "alt", "alt_r": "alt", "alt_gr": "alt",
                    "shift_l": "shift", "shift_r": "shift"
                }
                clean_name = mapping.get(clean_name, clean_name)
                k = f"<{clean_name}>"

            if k not in captured_keys:
                captured_keys.append(k)
            
            currently_pressed.add(str(key))

            def update_ui():
                self.entry_hotkey.delete(0, "end")
                self.entry_hotkey.insert(0, "+".join(captured_keys))
            self.after(0, update_ui)

        def on_release(key):
            k_str = str(key)
            if k_str in currently_pressed:
                currently_pressed.remove(k_str)
            
            # On arrête l'écoute quand TOUTES les touches sont relâchées
            if len(currently_pressed) == 0 and captured_keys:
                def finalize_ui():
                    self.btn_capture.configure(text="ENREGISTRER UNE TOUCHE", state="normal", fg_color="transparent")
                    self.log(f"Raccourci capturé : {'+'.join(captured_keys)}")
                self.after(0, finalize_ui)
                return False

        threading.Thread(target=lambda: keyboard.Listener(on_press=on_press, on_release=on_release).start(), daemon=True).start()

    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, "r") as f:
                self.saved_config = json.load(f)
        else:
            # Configuration par défaut si le fichier n'existe pas
            self.saved_config = {
                "client_id": "",
                "token": "",
                "username": "",
                "broadcaster_id": "",
                "hotkey": "f9",
                "auto_mode": False,
                "interval": "300",
                "duration": "30",
                "color_pink": "#FF2E63",
                "color_purple": "#8A2BE2"
            }

    def create_clip(self):
        """Action de création du clip sur Twitch"""
        bid = self.entry_bid.get().strip()
        cid = self.entry_client_id.get().strip()
        tok = self._get_clean_token()

        if not bid or not cid or not tok:
            self.log("Erreur : Client ID, Token ou Broadcaster ID manquant !")
            return

        url = f"https://api.twitch.tv/helix/clips?broadcaster_id={bid}"
        headers = {"Client-Id": cid, "Authorization": f"Bearer {tok}"}
        
        try:
            res = requests.post(url, headers=headers, timeout=5)
            if res.status_code == 202:
                data = res.json()
                if data.get('data'):
                    slug = data['data'][0]['id']
                    clip_url = f"https://clips.twitch.tv/{slug}"
                    self.log(f"Clip créé ! Lien : {clip_url}")
                    winsound.MessageBeep(winsound.MB_OK) # Produit un son de confirmation
                    
                    # Sauvegarde dans le fichier texte
                    with open(self.clips_file, "a", encoding="utf-8") as f:
                        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {clip_url}\n")
            elif res.status_code == 404:
                self.log("Erreur 404 : Le streamer est hors-ligne.")
            else:
                try:
                    error_msg = res.json().get('message', 'Détails indisponibles')
                    self.log(f"Erreur API {res.status_code} : {error_msg}")
                except:
                    self.log(f"Erreur API {res.status_code}")
        except Exception:
            self.log(f"CRASH CLIP:\n{traceback.format_exc()}")

    def toggle_service(self):
        p_color = self.saved_config.get("color_pink", COLOR_PINK)
        v_color = self.saved_config.get("color_purple", COLOR_PURPLE)

        if not self.is_running:
            self.save_config()
            self.is_running = True
            self.btn_toggle.configure(text="ARRÊTER", fg_color=p_color)
            self.log("Écouteur activé...")
            
            # Lancement du listener dans un thread séparé
            self.hotkey_thread = threading.Thread(target=self.run_hotkey_listener, daemon=True)
            self.hotkey_thread.start()

            # Lancement du mode auto si coché
            if self.auto_mode_var.get():
                self.auto_thread = threading.Thread(target=self.run_auto_loop, daemon=True)
                self.auto_thread.start()
        else:
            self.is_running = False
            self.btn_toggle.configure(text="DÉMARRER", fg_color=v_color)
            if self.listener:
                self.listener.stop()
            self.log("Écouteur arrêté.")

    def run_auto_loop(self):
        """Boucle pour créer des clips automatiquement à intervalle régulier."""
        try:
            interval = int(self.entry_interval.get())
            if interval < 10:
                self.log("Attention : Intervalle trop court. Minimum 10s recommandé.")
                interval = 10
            
            self.log(f"Mode Auto activé : un clip toutes les {interval}s")
            while self.is_running:
                time.sleep(interval)
                if self.is_running:
                    self.log("Auto-Clip en cours...")
                    self.create_clip()
        except ValueError:
            self.log("Erreur : L'intervalle doit être un nombre.")
        except Exception:
            self.log(f"CRASH AUTO-MODE:\n{traceback.format_exc()}")

    def run_hotkey_listener(self):
        # Récupération et nettoyage de la touche
        hotkey = self.entry_hotkey.get().strip()
        if not hotkey:
            self.log("Erreur : Aucun raccourci clavier défini (ex: f9).")
            self.after(0, self.toggle_service) # Réinitialise l'interface (Stop)
            return

        try:
            with keyboard.GlobalHotKeys({hotkey: self.create_clip}) as self.listener:
                self.listener.join()
        except ValueError:
            self.log(f"Erreur : Le format de touche '{hotkey}' est incorrect (utilisez f8 ou <ctrl>+e).")
            self.after(0, self.toggle_service)
        except Exception:
            self.log(f"CRASH HOTKEY:\n{traceback.format_exc()}")

if __name__ == "__main__":
    app = TwitchAutoClipper()
    app.mainloop()
