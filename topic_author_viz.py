import pandas as pd
import matplotlib
matplotlib.use("Agg") # Important pour Render (pas d'écran)
import matplotlib.pyplot as plt
import numpy as np
import ast
from collections import Counter

# ---------------------------------------------------------------------------
# NOTE : La liste 'unique_names' n'est plus calculée ici.
# Elle est gérée par app.py via la base de données SQL.
# ---------------------------------------------------------------------------

def plot_author_topics(df_author, graph_type="full"):
    """
    Génère le graphique pour un auteur à partir d'un DataFrame déjà chargé.
    
    Args:
        df_author (pd.DataFrame): Les données de l'auteur (chargées depuis le Cloud via app.py).
        graph_type (str): "full" ou "top5".
    """
    
    # Sécurité : Si le fichier Cloud contient plusieurs auteurs (cas rare), on re-filtre
    # Mais si le fichier est déjà spécifique à l'auteur, cette ligne ne change rien.
    # On suppose que df_author est déjà propre.
    if df_author.empty:
        raise ValueError("Le DataFrame fourni pour cet auteur est vide.")

    # Parsing des colonnes string -> list (si nécessaire)
    if "top_2_topics_with_prop" in df_author.columns:
        first_cell = df_author["top_2_topics_with_prop"].iloc[0]
        if isinstance(first_cell, str):
            df_author["top_2_topics_with_prop"] = df_author["top_2_topics_with_prop"].apply(ast.literal_eval)

    # -----------------------------------------------------------------------
    # Full graph
    # -----------------------------------------------------------------------
    if graph_type == "full":
        # Copie locale pour éviter les warning SettingWithCopy
        df_work = df_author.copy()
        
        df_work["topic_prop"] = df_work["top_2_topics_with_prop"].apply(lambda x: [(t[0], t[1]) for t in x])
        df_long = df_work.explode("topic_prop")
        # Sécurité anti-NaN après explode
        df_long = df_long.dropna(subset=["topic_prop"])
        
        df_long["topics"] = df_long["topic_prop"].apply(lambda x: x[0])
        df_long["props"]  = df_long["topic_prop"].apply(lambda x: x[1])

        df_agg = df_long.groupby(["annee","topics"], as_index=False).agg(mean_prop=("props","mean"))
        topics_sorted = sorted(df_agg["topics"].unique())
        num_topics = len(topics_sorted)
        
        height = max(0.5 * num_topics, 6)
        width = 14
        if num_topics > 20: width = 16
        if num_topics > 30: width = 18

        fig, ax = plt.subplots(figsize=(width, height))

        # Colors logic
        if num_topics <= 10:
            cmap = plt.cm.tab10
            colors = [cmap(i % 10) for i in range(num_topics)]
        elif num_topics <= 20:
            cmap = plt.cm.tab20
            colors = [cmap(i) for i in range(num_topics)]
        else:
            cmap = plt.cm.gist_ncar
            colors = [cmap(i/num_topics) for i in range(num_topics)]

        for i, topic in enumerate(topics_sorted):
            subset = df_agg[df_agg["topics"] == topic]
            # Jitter léger pour éviter la superposition
            y_positions = [i + np.random.uniform(-0.1, 0.1) for _ in range(len(subset))]
            ax.scatter(
                subset["annee"].to_numpy(),
                y_positions,
                s=(subset["mean_prop"].to_numpy() * 500),
                alpha=0.7,
                color=colors[i],
                edgecolors='black',
                linewidth=0.5
            )

        ax.set_yticks(range(num_topics))
        ax.set_yticklabels(topics_sorted)
        ax.set_xlabel("Year")
        ax.set_ylabel("Topics")
        ax.set_title("Discrete Time Bands") # Le titre de l'auteur est géré par le HTML

        years_min, years_max = int(df_agg["annee"].min()), int(df_agg["annee"].max())
        step = 5 if (years_max - years_min) > 30 else 1
        years_ticks = np.arange(years_min, years_max + 1, step)
        
        ax.set_xticks(years_ticks)
        ax.tick_params(axis='x', rotation=45, labelsize=8)
        ax.grid(axis="x", linestyle=":", alpha=0.3)
        plt.subplots_adjust(left=0.15, right=0.85, top=0.95, bottom=0.1)

        return fig

    # -----------------------------------------------------------------------
    # Top 5 topics
    # -----------------------------------------------------------------------
    elif graph_type == "top5":
        df_work = df_author.copy()
        all_topics = [t[0] for sublist in df_work["top_2_topics_with_prop"] for t in sublist]
        
        if not all_topics:
            # Cas rare : auteur sans topics
            fig, ax = plt.subplots()
            ax.text(0.5, 0.5, "Pas de données topics", ha='center')
            return fig

        top5_topics = [t for t, _ in Counter(all_topics).most_common(5)]

        df_work["topic_prop"] = df_work["top_2_topics_with_prop"].apply(
            lambda x: [(t[0], t[1]) for t in x if t[0] in top5_topics]
        )

        df_long = df_work.explode("topic_prop")
        df_long = df_long[df_long["topic_prop"].notna()]
        
        if df_long.empty:
             fig, ax = plt.subplots()
             ax.text(0.5, 0.5, "Pas de données top 5", ha='center')
             return fig

        df_long["topics"] = df_long["topic_prop"].apply(lambda x: x[0])
        df_long["props"]  = df_long["topic_prop"].apply(lambda x: x[1])

        df_agg = df_long.groupby(["annee","topics"], as_index=False).agg(mean_prop=("props","mean"))
        topics_sorted = sorted(df_agg["topics"].unique())
        height = max(0.5 * len(topics_sorted), 6)

        fig, ax = plt.subplots(figsize=(12, height))
        colors = plt.cm.tab10.colors

        for i, topic in enumerate(topics_sorted):
            subset = df_agg[df_agg["topics"] == topic]
            y_positions = [i + np.random.uniform(-0.1, 0.1) for _ in range(len(subset))]
            ax.scatter(
                subset["annee"].to_numpy(),
                y_positions,
                s=(subset["mean_prop"].to_numpy() * 500),
                alpha=0.7,
                color=colors[i % len(colors)],
                label=topic,
                edgecolors='black',
                linewidth=0.5
            )

        ax.set_yticks(range(len(topics_sorted)))
        ax.set_yticklabels(topics_sorted)
        ax.set_xlabel("Year")
        ax.set_title("Top 5 Topics")
        
        years_min, years_max = int(df_agg["annee"].min()), int(df_agg["annee"].max())
        step = 5 if (years_max - years_min) > 30 else 1
        ax.set_xticks(np.arange(years_min, years_max + 1, step))
        ax.tick_params(axis='x', rotation=45, labelsize=8)
        ax.grid(axis="x", linestyle=":", alpha=0.3)
        plt.subplots_adjust(left=0.15, right=0.85, top=0.95, bottom=0.1)

        return fig

    else:
        raise ValueError("graph_type must be 'full' or 'top5'")
