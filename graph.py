import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io
import base64
import pandas as pd

def create_bar_graph(x, y, title, color="skyblue"):
    plt.figure(figsize=(18, 9), dpi=120)
    plt.bar(x, y, color=color)
    plt.title(title)
    plt.xticks(list(x)[::10], rotation=45, ha='right') # Step de 10 ans
    plt.tight_layout()
    
    img = io.BytesIO()
    plt.savefig(img, format="png")
    img.seek(0)
    b64 = base64.b64encode(img.getvalue()).decode()
    plt.close()
    return b64

def get_graphs(df_cairn_light, df_mon_light):
    """
    Génère les graphs temporels à partir des DataFrames légers (juste les dates).
    """
    g_cairn, g_mon = "", ""

    # ---- CAIRN ----
    if not df_cairn_light.empty:
        # Nettoyage
        df_c = df_cairn_light.copy()
        df_c["annee"] = pd.to_numeric(df_c["annee"], errors='coerce').fillna(0).astype(int)
        df_c = df_c[df_c["annee"] > 1000] # Filtre années invalides
        
        dist = df_c["annee"].value_counts().sort_index()
        g_cairn = create_bar_graph(dist.index, dist.values, "Articles par année (CAIRN)", "skyblue")

    # ---- LE MONDE ----
    if not df_mon_light.empty:
        df_m = df_mon_light.copy()
        # Conversion date
        df_m["date_published"] = pd.to_datetime(df_m["date_published"], errors="coerce", utc=True)
        df_m = df_m.dropna(subset=["date_published"])
        df_m["annee"] = df_m["date_published"].dt.year.astype(int)
        
        dist = df_m["annee"].value_counts().sort_index()
        g_mon = create_bar_graph(dist.index, dist.values, "Articles par année (Le Monde)", "coral")

    return g_mon, g_cairn
