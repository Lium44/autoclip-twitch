# 🚀 Twitch Helix Clipper Pro (by Lium)

Une application moderne et stylée exploitant l'**API Twitch Helix** pour créer des clips instantanément, soit par un raccourci clavier personnalisé, soit automatiquement via un timer.

## ✨ Fonctionnalités
- **Interface Cyberpunk** : Design sombre avec accents rose/violet et fond animé.
- **Hotkey Intelligent** : Enregistrez vos propres combinaisons de touches (ex: Ctrl+Alt+C).
- **Helix API Core** : Utilisation des derniers endpoints Twitch pour une rapidité maximale.
- **Historique** : Sauvegarde automatique de tous les liens dans un fichier texte.
- **Beep de confirmation** : Un signal sonore retentit à chaque clip réussi.

## 📥 Installation (Développeur)

Si vous souhaitez lancer le script via Python :

1. Installez les dépendances :
   ```bash
   pip install -r requirements.txt
   ```
2. Lancez l'application :
   ```bash
   python main.py
   ```

## 🔑 Configuration Twitch

Pour utiliser l'outil avec l'API Helix, vous devez obtenir vos identifiants sur le [Twitch Token generator](https://twitchtokengenerator.com) :
1. Créez une "Application".
2. Récupérez votre **Client ID**.
3. Générez un **OAuth Token** (Access Token) avec la permission `clips:edit`.

## 📦 Créer une version .exe (Sans Python)

L'avantage de cette méthode est que l'utilisateur final n'a **pas besoin d'installer Python ni les dépendances**. Tout est inclus dans le fichier.

1. Installez PyInstaller : `pip install pyinstaller`
2. Lancez cette commande dans le dossier :
   ```bash
   pyinstaller --noconsole --onefile --name "Twitch Clipper Pro" --icon "ton_icone.ico" --collect-all customtkinter main.py
   ```
3. Récupérez le fichier `Twitch Clipper Pro.exe` dans le dossier `dist/` et envoyez-le à vos amis !

## 📂 Structure du projet
- `main.py` : Le code source principal.
- `config.json` : Stocke vos réglages (Client ID, Touche, etc.).
- `clips_sauvegardes.txt` : Journal de tous vos clips créés.
- `ton_icone.ico` : (Optionnel) L'icône de l'application.

---
*Développé avec ❤️ par Lium.*