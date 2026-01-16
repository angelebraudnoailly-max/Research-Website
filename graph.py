import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io
import base64

def create_bar_graph(x, y, title, xlabel="Year", ylabel="Number of articles", color="skyblue", tick_step=10):
    # Création du canvas
    plt.figure(figsize=(18, 9), dpi=120)
    plt.bar(x, y, color=color)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    
    tick_years = list(x)[::tick_step]
    plt.xticks(tick_years, rotation=45, ha='right')
    plt.tight_layout()
    
    # Export en Base64
    img = io.BytesIO()
    plt.savefig(img, format="png")
    img.seek(0)
    graph_base64 = base64.b64encode(img.getvalue()).decode()
    plt.close()
    return graph_base64

def get_graphs(df_cairn, df_mon):
    """
    Génère les graphiques temporels.
    Args:
        df_cairn (pd.DataFrame): Doit contenir une colonne 'annee'.
        df_mon (pd.DataFrame): Doit contenir 'date_published'.
    """
    
    # ---- CAIRN ----
    if not df_cairn.empty:
        # On s'assure que c'est propre
        if df_cairn["annee"].dtype == object:
             # Nettoyage basique si besoin
             pass
        df_cairn["annee"] = pd.to_numeric(df_cairn["annee"], errors='coerce').fillna(0).astype(int)
        df_cairn = df_cairn[df_cairn["annee"] > 0]
        
        dist_cairn = df_cairn["annee"].value_counts().sort_index()
        graph_cairn = create_bar_graph(
            dist_cairn.index, dist_cairn.values,
            "Distribution of articles by year in CAIRN dataset",
            color="skyblue", tick_step=10
        )
    else:
        graph_cairn = ""

    # ---- Le Monde ----
    if not df_mon.empty:
        # Conversion date
        df_mon["date_published"] = pd.to_datetime(df_mon["date_published"], errors="coerce", utc=True)
        df_mon = df_mon.dropna(subset=["date_published"])
        df_mon["annee"] = df_mon["date_published"].dt.year.astype(int)
        
        dist_mon = df_mon["annee"].value_counts().sort_index()
        graph_mon = create_bar_graph(
            dist_mon.index, dist_mon.values,
            "Distribution of articles by year in Le Monde dataset",
            color="coral", tick_step=10
        )
    else:
        graph_mon = ""

    return graph_mon, graph_cairn
