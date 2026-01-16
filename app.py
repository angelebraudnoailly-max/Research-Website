import os
import io
import base64
import json
import pandas as pd
import psycopg2
import matplotlib.pyplot as plt
from flask import Flask, render_template, request, redirect, flash, jsonify

# --- IMPORTS ---
from graph import get_graphs 
from contact import send_email
from topics_viz import get_lda_insights
import topic_author_viz 

app = Flask(__name__)
app.secret_key = "secret"

# Fonction utilitaire pour se connecter à Render PostgreSQL
def get_db_connection():
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
    # MAJ INTEGRÉE : On utilise SQL pour découper les auteurs multiples (séparés par '|')
    cur = conn.cursor()
    try:
        # Note : J'utilise la colonne 'name' comme vu dans votre script précédent.
        # Si votre colonne s'appelle toujours 'nom_auteur', remplacez 'name' par 'nom_auteur' ci-dessous.
        sql_authors = """
            SELECT DISTINCT TRIM(unnest(string_to_array(name, '|'))) 
            FROM colonnes_CAIRNLIGHT 
            ORDER BY 1 ASC
        """
        cur.execute(sql_authors)
        # On filtre les résultats vides ou nuls
        unique_names = [row[0] for row in cur.fetchall() if row[0] and row[0].strip() != '']
    except Exception as e:
        print(f"Erreur récupération auteurs : {e}")
        unique_names = []
    cur.close()

    # 2. GRAPHIQUES TEMPORELS (Le Monde / Cairn)
    try:
        # On ne charge que les colonnes nécessaires pour économiser la RAM
        df_cairn_light = pd.read_sql("SELECT annee FROM colonnes_CAIRNLIGHT", conn) 
        df_mon_light = pd.read_sql("SELECT date_published FROM colonnes_lemonde", conn)
        
        graph_mon, graph_cairn = get_graphs(df_cairn_light, df_mon_light)
    except Exception as e:
        print(f"Erreur graphs temporels : {e}")
        graph_mon, graph_cairn = "", ""

    # 3. STATISTIQUES LDA (Graphs colorés)
    try:
        # On récupère tout le contenu de la table Cairn pour les stats globales
        df_lda = pd.read_sql("SELECT * FROM colonnes_CAIRNLIGHT", conn)
        
        g_freq, g_prop, g_comb, g_disp, author_stats = get_lda_insights(df_lda)
        
        # Pour les topics, on peut utiliser un dictionnaire vide ou une autre table si dispo
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
# AUTHOR GRAPHS ROUTE (Optimisé : Requête SQL Directe)
# ---------------------------------------------------------------------------
@app.route("/author_graphs", methods=["POST"])
def author_graphs():
    data = request.json
    author_name = data.get("author")
    graph_type = data.get("graph_type", "full")

    conn = get_db_connection()
    
    # MAJ INTEGRÉE : On cherche les données directement dans la table principale (colonnes_CAIRNLIGHT)
    # Plus besoin de fichier catalogue ni d'URL Cloud.
    # On utilise LIKE avec %...% pour trouver l'auteur même s'il est dans une chaîne "Auteur1 | Auteur2"
    query = "SELECT * FROM colonnes_CAIRNLIGHT WHERE name LIKE %s"
    
    try:
        # pd.read_sql exécute la requête et met le résultat directement dans un DataFrame
        df_author = pd.read_sql(query, conn, params=(f"%{author_name}%",))
        conn.close()
        
        if df_author.empty:
             return jsonify({"error": "Auteur introuvable dans la base"}), 404

        # Génération du graphique avec les données récupérées
        fig = topic_author_viz.plot_author_topics(df_author, graph_type=graph_type)

        img_bytes = io.BytesIO()
        fig.savefig(img_bytes, format="png", bbox_inches="tight")
        plt.close(fig)
        img_bytes.seek(0)
        img_base64 = base64.b64encode(img_bytes.read()).decode("utf-8")
        
        return jsonify({"img": img_base64})

    except Exception as e:
        return jsonify({"error": f"Erreur lors de la génération du graphique : {e}"}), 500

# ---------------------------------------------------------------------------
# SERVER LAUNCH
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
