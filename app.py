import os
import io
import base64
import json
import pandas as pd
import psycopg2
import matplotlib.pyplot as plt
from flask import Flask, render_template, request, redirect, flash, jsonify

# --- IMPORTS CORRIGÉS ---
# On importe les fonctions "passives" des autres fichiers
from graph import get_graphs 
from contact import send_email
from topics_viz import get_lda_insights
import topic_author_viz 

app = Flask(__name__)
app.secret_key = "secret"

# Fonction utilitaire pour se connecter à Render PostgreSQL
def get_db_connection():
    # Cette variable est créée automatiquement par Render quand vous liez la DB
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    return conn

# ---------------------------------------------------------------------------
# MAIN ROUTE (Page d'accueil)
# ---------------------------------------------------------------------------
@app.route("/", methods=['GET'])
def index():
    """
    Charge les données globales depuis PostgreSQL pour l'accueil.
    """
    conn = get_db_connection()
    
    # 1. LISTE DES AUTEURS (Dropdown)
    # On récupère juste les noms uniques via SQL (très rapide)
    # Note: Assurez-vous que la table 'catalogue_auteurs' existe (via import_csv.py)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT nom_auteur FROM catalogue_auteurs ORDER BY nom_auteur ASC")
    unique_names = [row[0] for row in cur.fetchall()]
    cur.close()

    # 2. GRAPHIQUES TEMPORELS (Le Monde / Cairn)
    # On utilise pandas read_sql pour récupérer les colonnes 'annee' et 'date_published'
    # depuis vos tables SQL (remplacez 'table_cairn' et 'table_lemonde' par vos vrais noms de tables)
    try:
        # On ne charge que les colonnes nécessaires (pas tout le texte !) pour économiser la RAM
        df_cairn_light = pd.read_sql("SELECT annee FROM table_oeuvres", conn) 
        df_mon_light = pd.read_sql("SELECT date_published FROM table_articles_lemonde", conn)
        
        # On génère les graphs via graph.py
        graph_mon, graph_cairn = get_graphs(df_cairn_light, df_mon_light)
    except Exception as e:
        print(f"Erreur graphs temporels : {e}")
        graph_mon, graph_cairn = "", ""

    # 3. STATISTIQUES LDA (Graphs colorés)
    # On récupère les données LDA depuis la table SQL
    try:
        # Remplacez 'table_lda_light' par le nom de la table contenant CAIRN_LDA_LIGHT.csv
        df_lda = pd.read_sql("SELECT * FROM table_lda_light", conn)
        
        # On génère les 4 graphs et les stats via topics_viz.py
        g_freq, g_prop, g_comb, g_disp, author_stats = get_lda_insights(df_lda)
        
        # Pour la liste des topics (texte), on peut la déduire ou la charger
        # Ici on prend un dict vide pour l'exemple, ou le résultat de get_lda_topics si vous avez une table
        topics = {} 
    except Exception as e:
        print(f"Erreur LDA stats : {e}")
        g_freq, g_prop, g_comb, g_disp, author_stats = "", "", "", "", {}
        topics = {}

    conn.close()

    return render_template(
        "index.html",
        graph_mon=graph_mon,
        graph_cairn=graph_cairn,
        topics=topics,
        g_freq=g_freq,
        g_prop=g_prop,
        g_comb=g_comb,
        g_disp=g_disp,
        author_stats=author_stats,
        unique_names=unique_names
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
# AUTHOR GRAPHS ROUTE (Lazy Loading Cloud)
# ---------------------------------------------------------------------------
@app.route("/author_graphs", methods=["POST"])
def author_graphs():
    data = request.json
    author_name = data.get("author")
    graph_type = data.get("graph_type", "full")

    # 1. Trouver l'URL Google Cloud dans la DB
    conn = get_db_connection()
    cur = conn.cursor()
    # ATTENTION: Vérifiez que votre table 'catalogue_auteurs' a bien une colonne 'url_cloud'
    # Sinon changez le nom de la colonne dans la requête ci-dessous
    cur.execute("SELECT url_cloud FROM catalogue_auteurs WHERE nom_auteur = %s", (author_name,))
    result = cur.fetchone()
    conn.close()

    if not result:
        return jsonify({"error": "Auteur introuvable"}), 404

    cloud_url = result[0] 

    # 2. Charger les données depuis le Cloud (Lazy Loading)
    try:
        # Pandas lit directement l'URL Google Cloud (si le fichier est public)
        # Si vos fichiers Cloud sont des JSON :
        df_author = pd.read_json(cloud_url)
        
        # Si vos fichiers Cloud sont des CSV, décommentez la ligne ci-dessous :
        # df_author = pd.read_csv(cloud_url)
    except Exception as e:
        return jsonify({"error": f"Erreur lecture Cloud: {e}"}), 500

    # 3. Générer le graph
    try:
        # On passe le DataFrame téléchargé à la fonction de dessin
        fig = topic_author_viz.plot_author_topics(df_author, graph_type=graph_type)

        img_bytes = io.BytesIO()
        fig.savefig(img_bytes, format="png", bbox_inches="tight")
        plt.close(fig)
        img_bytes.seek(0)
        img_base64 = base64.b64encode(img_bytes.read()).decode("utf-8")
        
        return jsonify({"img": img_base64})
    except Exception as e:
        return jsonify({"error": f"Erreur génération graph: {e}"}), 500

# ---------------------------------------------------------------------------
# SERVER LAUNCH
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
