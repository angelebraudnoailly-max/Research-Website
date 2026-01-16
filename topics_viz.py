import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io
import base64
import numpy as np
import pandas as pd
from collections import Counter, defaultdict
import ast

def fig_to_base64(plt_fig):
    img = io.BytesIO()
    plt_fig.tight_layout()
    plt_fig.savefig(img, format="png", dpi=120)
    img.seek(0)
    base64_str = base64.b64encode(img.getvalue()).decode()
    plt.close()
    return base64_str

def safe_parse(x):
    if isinstance(x, str):
        try: return ast.literal_eval(x)
        except: return []
    return x

def get_lda_insights(df):
    """
    Génère les stats globales à partir du DataFrame SQL complet.
    """
    if df.empty:
        return "", "", "", "", {}

    # Travail sur une copie
    df_work = df.copy()
    
    # Parsing si nécessaire
    if "top_2_topics_with_prop" in df_work.columns:
        df_work["top_2_topics_with_prop"] = df_work["top_2_topics_with_prop"].apply(safe_parse)

    # --- Calculs Stats (Identiques à avant) ---
    all_top2 = [t for sub in df_work["top_2_topics_with_prop"] if sub for t, _ in sub]
    topic_freq = Counter(all_top2)
    
    topic_props = defaultdict(list)
    for sub in df_work["top_2_topics_with_prop"]:
        if sub:
            for t, p in sub: topic_props[t].append(p)
    
    avg_props = {t: sum(ps)/len(ps) for t, ps in topic_props.items()}

    # --- Graph 1: Frequency ---
    top_f = topic_freq.most_common(15)
    if top_f:
        ts, cs = zip(*top_f)
        plt.figure(figsize=(10, 7))
        plt.bar(range(len(ts)), cs, color="skyblue")
        plt.xticks(range(len(ts)), ts, rotation=45)
        plt.title("Top 15 Topics (Fréquence)")
        g_freq = fig_to_base64(plt)
    else: g_freq = ""

    # --- Graph 2: Proportion ---
    top_p = sorted(avg_props.items(), key=lambda x: x[1], reverse=True)[:15]
    if top_p:
        ts, ps = zip(*top_p)
        plt.figure(figsize=(10, 7))
        plt.bar(range(len(ts)), ps, color="salmon")
        plt.xticks(range(len(ts)), ts, rotation=45)
        plt.title("Top 15 Topics (Proportion)")
        g_prop = fig_to_base64(plt)
    else: g_prop = ""

    # --- Graph 3: Combined ---
    combined = {t: topic_freq[t] * avg_props[t] for t in topic_freq}
    top_c = sorted(combined.items(), key=lambda x: x[1], reverse=True)[:15]
    if top_c:
        ts, ss = zip(*top_c)
        plt.figure(figsize=(10, 7))
        plt.bar(range(len(ts)), ss, color="plum")
        plt.xticks(range(len(ts)), ts, rotation=45)
        plt.title("Top 15 Topics (Score Combiné)")
        g_comb = fig_to_base64(plt)
    else: g_comb = ""

    # --- Graph 4: Dispersion ---
    # Adaptez "url" si votre colonne ID s'appelle autrement (ex: 'article_id')
    col_id = "url" if "url" in df_work.columns else df_work.columns[0]
    disp = df_work.groupby(col_id)["top_2_topics_with_prop"].apply(lambda x: len({t for s in x for t, _ in s}))
    
    if not disp.empty:
        plt.figure(figsize=(10, 7))
        plt.hist(disp, bins=range(int(disp.min()), int(disp.max()) + 2), align="left", rwidth=0.8, color="teal")
        plt.title("Dispersion Thématique")
        g_disp = fig_to_base64(plt)
    else: g_disp = ""

    # --- Author Stats ---
    author_topics = defaultdict(set)
    for _, row in df_work.iterrows():
        # Adaptez 'name' si votre colonne auteur s'appelle 'nom_auteur'
        col_nom = 'name' if 'name' in df_work.columns else 'nom_auteur'
        if pd.notna(row.get(col_nom)):
            authors = [a.strip() for a in str(row[col_nom]).split('|')]
            for author in authors:
                for topic_id, _ in row['top_2_topics_with_prop']:
                    author_topics[author].add(topic_id)
    
    counts = np.array([len(t) for t in author_topics.values()])
    
    if len(counts) > 0:
        author_stats = {
            "mean": np.mean(counts), "median": int(np.median(counts)),
            "min": int(np.min(counts)), "max": int(np.max(counts)),
            "unique_authors": len(counts)
        }
    else: author_stats = {}

    return g_freq, g_prop, g_comb, g_disp, author_stats
