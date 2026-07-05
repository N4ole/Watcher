import psutil
import subprocess
import time
import os
import sys
from datetime import datetime

# ─── Configuration ──────────────────────────────────────────────
SCRIPT_A_SURVEILLER = "main.py"      # Nom du script à surveiller
INTERVALLE = 10                       # Intervalle de vérification (secondes)
PYTHON_EXE = sys.executable           # Utilise le même interpréteur Python
# ────────────────────────────────────────────────────────────────


def log(message):
    """Affiche un message horodaté."""
    horodatage = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{horodatage}] {message}")


def est_en_cours(nom_script):
    """
    Vérifie si un script Python donné est en cours d'exécution.
    Retourne le PID si trouvé, sinon None.
    """
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            cmdline = proc.info["cmdline"]
            if not cmdline:
                continue
            # On vérifie que c'est bien un processus python exécutant notre script
            if any("python" in part.lower() for part in cmdline) and \
               any(nom_script in part for part in cmdline):
                # On évite de se détecter soi-même (le moniteur)
                if os.path.basename(__file__) not in " ".join(cmdline):
                    return proc.info["pid"]
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return None


def lancer_script(nom_script):
    """Lance le script cible en arrière-plan."""
    chemin = os.path.abspath(nom_script)
    if not os.path.exists(chemin):
        log(f"❌ ERREUR : le fichier '{chemin}' est introuvable.")
        return None

    log(f"🚀 Lancement de {nom_script}...")
    processus = subprocess.Popen(
        [PYTHON_EXE, chemin],
        stdout=subprocess.DEVNULL,   # Remplace par un fichier log si besoin
        stderr=subprocess.DEVNULL,
    )
    log(f"✅ {nom_script} lancé (PID {processus.pid}).")
    return processus.pid


def main():
    log(f"🔍 Démarrage du moniteur pour '{SCRIPT_A_SURVEILLER}'.")
    log(f"   Vérification toutes les {INTERVALLE} secondes.")

    try:
        while True:
            pid = est_en_cours(SCRIPT_A_SURVEILLER)
            if pid:
                log(f"✔️  {SCRIPT_A_SURVEILLER} tourne correctement (PID {pid}).")
            else:
                log(f"⚠️  {SCRIPT_A_SURVEILLER} n'est PAS en cours d'exécution.")
                lancer_script(SCRIPT_A_SURVEILLER)

            time.sleep(INTERVALLE)

    except KeyboardInterrupt:
        log("🛑 Moniteur arrêté par l'utilisateur.")


if __name__ == "__main__":
    main()
