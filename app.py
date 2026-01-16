import os
import io
import base64
import json
import pandas as pd
import psycopg2
import matplotlib.pyplot as plt
from flask import Flask, render_template, request, redirect, flash, jsonify

# On importe vos modules de visualisation
# IMPORTANT : Assurez-vous que ces fichiers ne font PAS de pd.read_csv() au démarrage !
# Ils doivent contenir seulement des fonctions qui acceptent un DataFrame en entrée.
from graph import get_graphs_from_data           # (Nom supposé fonction adaptée)
from contact import send_email
# from topics import get_lda_topics              # On va le remplacer par une requête SQL
# from topic_author_viz import unique_names      # On va le remplacer par une requête SQL
import topic_author_viz 

app = Flask(_name_)
app.secret_key = "secret"

# Fonction utilitaire pour se connecter à Render PostgreSQL
def get_db_connection():
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    return conn

# ---------------------------------------------------------------------------
# MAIN ROUTE (Le haut de l'Iceberg : Rapide & Léger)
# ---------------------------------------------------------------------------
@app.route("/", methods=['GET'])
def index():
    """
    Cette route ne charge plus de fichiers. Elle interroge PostgreSQL.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    # 1. Récupérer la liste des auteurs (Léger)
    # Au lieu de lire tout le CSV pour trouver les noms uniques, on demande à la DB
    # Assurez-vous d'avoir une table 'catalogue_auteurs' créée via import_csv.py
    cur.execute("SELECT DISTINCT nom_auteur FROM catalogue_auteurs ORDER BY nom_auteur ASC")
    unique_names = [row[0] for row in cur.fetchall()]

    # 2. Récupérer les stats globales pour les graphs (Léger)
    # Idéalement, vous avez stocké les données de 'get_graphs' et 'get_lda_topics'
    # dans des tables SQL dédiées (ex: 'table_stats_globales')
    
    # EXEMPLE : Si vous avez mis vos stats LDA dans la DB
    cur.execute("SELECT topic_id, keywords FROM table_topics_lda")
    lda_topics = cur.fetchall() # Adapter selon votre structure

    # Si vos graphs globaux (séries temporelles) sont légers, vous pouvez 
    # soit les avoir en SQL, soit garder un PETIT csv 'stats.csv' dans le dossier du projet
    # Pour l'exemple, imaginons que vous ayez adapté get_graphs pour lire une table SQL :
    # graph_mon, graph_cairn = get_graphs_from_db(conn) 
    
    # Pour ne pas casser votre code sans voir vos autres fichiers, je mets des placeholders
    graph_mon = "" 
    graph_cairn = ""
    g_freq, g_prop, g_comb, g_disp, author_stats = "", "", "", "", ""

    conn.close()

    return render_template(
        "index.html",
        graph_mon=graph_mon,
        graph_cairn=graph_cairn,
        topics=lda_topics,
        unique_names=unique_names, # La liste dropdown vient maintenant de la DB
        # ... autres variables ...
    )

# ---------------------------------------------------------------------------
# CONTACT ROUTE
# ---------------------------------------------------------------------------
@app.route("/contact", methods=['POST'])
def contact_route():
    name = request.form.get('name')
    email = request.form.get('email')
    message = request.form.get('message')
    try:
        send_email(name, email, message)
        flash("Message sent successfully!")
    except Exception as e:
        flash(f"Error: {e}")
    return redirect('/')

# ---------------------------------------------------------------------------
# AUTHOR GRAPHS ROUTE (La partie immergée : Lazy Loading depuis Google Cloud)
# ---------------------------------------------------------------------------
@app.route("/author_graphs", methods=["POST"])
def author_graphs():
    """
    C'est ici que la magie opère. On ne charge les données QUE quand on clique.
    """
    data = request.json
    author_name = data.get("author")
    graph_type = data.get("graph_type", "full")

    # 1. On cherche l'URL Google Cloud de cet auteur dans la Base de Données
    conn = get_db_connection()
    cur = conn.cursor()
    
    # On suppose que votre table a une colonne 'url_cloud' qui pointe vers le fichier JSON/CSV spécifique de l'auteur
    query = "SELECT url_cloud FROM catalogue_auteurs WHERE nom_auteur = %s"
    cur.execute(query, (author_name,))
    result = cur.fetchone()
    conn.close()

    if not result:
        return jsonify({"error": "Auteur introuvable ou pas de données cloud"}), 404

    cloud_url = result[0] 
    # Ex: https://storage.googleapis.com/mon-bucket/data_tolstoi.json

    # 2. LAZY LOADING : On télécharge les données brutes depuis Google Cloud
    # Pandas sait lire directement une URL
    try:
        # Si c'est du JSON sur le cloud
        df_author = pd.read_json(cloud_url)
        # Si c'est du CSV
        # df_author = pd.read_csv(cloud_url)
    except Exception as e:
        return jsonify({"error": f"Erreur chargement Cloud: {e}"}), 500

    # 3. Génération du Graphique
    # Il faut modifier votre fonction plot_author_topics pour qu'elle prenne 
    # le DataFrame (df_author) en argument au lieu de lire un fichier global.
    
    # Avant : fig = topic_author_viz.plot_author_topics(author)
    # Après :
    fig = topic_author_viz.plot_author_topics(df_author, graph_type=graph_type)

    # 4. Encodage et envoi
    img_bytes = io.BytesIO()
    fig.savefig(img_bytes, format="png", bbox_inches="tight")
    plt.close(fig)
    img_bytes.seek(0)
    img_base64 = base64.b64encode(img_bytes.read()).decode("utf-8")

    return jsonify({"img": img_base64})

# ---------------------------------------------------------------------------
# SERVER LAUNCH
# ---------------------------------------------------------------------------
if _name_ == "_main_":
    # Sur Render, le port est défini par l'environnement, sinon 5000 par défaut
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True) # Debug=False en production !
