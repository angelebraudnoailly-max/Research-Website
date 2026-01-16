import pandas as pd
from sqlalchemy import create_engine
import os

# --- CONFIGURATION ---
# Dictionnaire qui associe : "Nom du fichier" : "Nom de la table dans la base de données"
# L'ordre est important si vous avez des liens entre les tables (clés étrangères).
# Mettez les tables principales (ex: auteurs) en premier.

FILES_CONFIG = {
    # "nom_fichier_local" : "nom_table_render"
    "LeMonde_pour_db.csv": "colonnes_lemonde",
    "CAIRN_LDA_LIGHT_pour_db.csv": "colonnes_CAIRNLIGHT",
    "CAIRN_final_cleaned_pour_db.csv": "colonnes_CAIRNCLEAN",
    "topics_data.json": "colonnes_json"  # Votre fichier JSON
}

def upload_data():
    # 1. Demander l'URL (une seule fois pour tous les fichiers)
    db_url = input("Collez ici votre External Database URL de Render : ").strip()

    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    # 2. Connexion
    engine = create_engine(db_url)
    print("--> Connexion établie avec Render.")

    # 3. Boucle sur chaque fichier
    for filename, table_name in FILES_CONFIG.items():
        print(f"\n-----------------------------------")
        print(f"--> Traitement de : {filename} vers la table '{table_name}'")
        
        if not os.path.exists(filename):
            print(f"❌ ERREUR : Le fichier {filename} est introuvable dans le dossier !")
            continue

        try:
            # Détection automatique : CSV ou JSON
            if filename.endswith('.json'):
                # Lecture JSON (suppose une liste d'objets)
                df = pd.read_json(filename)
            else:
                # Lecture CSV
                df = pd.read_csv(filename)

            print(f"    Données chargées : {len(df)} lignes trouvées.")
            
            # Envoi vers PostgreSQL
            df.to_sql(table_name, engine, if_exists='replace', index=False)
            print(f"✅ Succès : Table '{table_name}' créée/mise à jour.")

        except ValueError as ve:
            print(f"❌ Erreur de format JSON/CSV sur {filename} : {ve}")
        except Exception as e:
            print(f"❌ Erreur critique sur {filename} : {e}")

    print("\n-----------------------------------")
    print("🏁 Terminé ! Vérifiez votre site web.")

if __name__ == "__main__":
    upload_data()
