import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io
import base64

CAIRN_CSV = "CAIRN_final_cleaned.csv"
LEMONDE_CSV = "LeMonde_auteur_filtré50.csv"

def create_bar_graph(x, y, title, xlabel="Year", ylabel="Number of articles", color="skyblue", tick_step=10):
    plt.figure(figsize=(18, 9), dpi=120)
    plt.bar(x, y, color=color)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    tick_years = list(x)[::tick_step]
    plt.xticks(tick_years, rotation=45, ha='right')
    plt.tight_layout()
    img = io.BytesIO()
    plt.savefig(img, format="png")
    img.seek(0)
    graph_base64 = base64.b64encode(img.getvalue()).decode()
    plt.close()
    return graph_base64

def get_graphs():
    # ---- CAIRN ----
    df_cairn = pd.read_csv(CAIRN_CSV)
    df_cairn["annee"] = df_cairn["annee"].astype(int)
    dist_cairn = df_cairn["annee"].value_counts().sort_index()
    graph_cairn = create_bar_graph(dist_cairn.index, dist_cairn.values,
                                   "Distribution of articles by year in CAIRN dataset",
                                   color="skyblue", tick_step=10)

    # ---- Le Monde ----
    df_mon = pd.read_csv(LEMONDE_CSV)
    df_mon["date_published"] = pd.to_datetime(df_mon["date_published"], errors="coerce", utc=True)
    df_mon = df_mon.dropna(subset=["date_published"])
    df_mon["annee"] = df_mon["date_published"].dt.year.astype(int)
    dist_mon = df_mon["annee"].value_counts().sort_index()
    graph_mon = create_bar_graph(dist_mon.index, dist_mon.values,
                                 "Distribution of articles by year in Le Monde dataset",
                                 color="coral", tick_step=10)
    return graph_mon, graph_cairn
