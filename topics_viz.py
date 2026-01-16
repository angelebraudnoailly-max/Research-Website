import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io
import base64
import numpy as np
from collections import Counter, defaultdict
import ast

# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------
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
        try:
            return ast.literal_eval(x)
        except:
            return [] # Retourne liste vide si erreur parsing
    return x

# ---------------------------------------------------------------------------
# Main function
# ---------------------------------------------------------------------------
def get_lda_insights(df):
    """
    Génère les graphiques et stats LDA à partir d'un DataFrame fourni.
    Args:
        df (pd.DataFrame): Le DataFrame 'CAIRN_LDA_LIGHT' chargé par app.py
    """
    
    if df.empty:
        return "", "", "", "", {}

    # Parsing columns of list type
    # On travaille sur une copie pour ne pas impacter le DF original
    df_work = df.copy()
    if "top_2_topics_with_prop" in df_work.columns:
        df_work["top_2_topics_with_prop"] = df_work["top_2_topics_with_prop"].apply(safe_parse)
    else:
        # Sécurité si colonne absente
        return "", "", "", "", {}

    # --- Prepare data for topics ---
    all_top2 = [t for sub in df_work["top_2_topics_with_prop"] if sub for t, _ in sub]
    topic_freq = Counter(all_top2)
    
    topic_props = defaultdict(list)
    for sub in df_work["top_2_topics_with_prop"]:
        if sub: # Check if list not empty
            for t, p in sub:
                topic_props[t].append(p)
    
    avg_props = {t: sum(ps)/len(ps) for t, ps in topic_props.items()}

    # --- Graph 1: Frequency ---
    top_f = topic_freq.most_common(15)
    if top_f:
        ts, cs = zip(*top_f)
        plt.figure(figsize=(10, 7))
        plt.bar(range(len(ts)), cs, color="skyblue")
        plt.xticks(range(len(ts)), ts, rotation=45)
        plt.xlabel("Topic")
        plt.ylabel("Frequency")
        plt.title("Top 15 Topics by Frequency")
        g_freq = fig_to_base64(plt)
    else:
        g_freq = ""

    # --- Graph 2: Proportion ---
    top_p = sorted(avg_props.items(), key=lambda x: x[1], reverse=True)[:15]
    if top_p:
        ts, ps = zip(*top_p)
        plt.figure(figsize=(10, 7))
        plt.bar(range(len(ts)), ps, color="salmon")
        plt.xticks(range(len(ts)), ts, rotation=45)
        plt.xlabel("Topic")
        plt.ylabel("Average Proportion")
        plt.title("Top 15 Topics by Average Proportion")
        g_prop = fig_to_base64(plt)
    else:
        g_prop = ""

    # --- Graph 3: Combined ---
    combined = {t: topic_freq[t] * avg_props[t] for t in topic_freq}
    top_c = sorted(combined.items(), key=lambda x: x[1], reverse=True)[:15]
    if top_c:
        ts, ss = zip(*top_c)
        plt.figure(figsize=(10, 7))
        plt.bar(range(len(ts)), ss, color="plum")
        plt.xticks(range(len(ts)), ts, rotation=45)
        plt.xlabel("Topic")
        plt.ylabel("Combined Score")
        plt.title("Top 15 Topics (Combined Score)")
        g_comb = fig_to_base64(plt)
    else:
        g_comb = ""

    # --- Graph 4: Dispersion ---
    disp = df_work.groupby("url")["top_2_topics_with_prop"].apply(lambda x: len({t for s in x for t, _ in s}))
    if not disp.empty:
        plt.figure(figsize=(10, 7))
        bins = range(int(disp.min()), int(disp.max()) + 2)
        plt.hist(disp, bins=bins, align="left", rwidth=0.8, color="teal")
        plt.xlabel("Number of Unique Topics per Article")
        plt.ylabel("Number of Articles")
        plt.title("Thematic Dispersion per Article")
        g_disp = fig_to_base64(plt)
    else:
        g_disp = ""

    # --- Author statistics ---
    author_topics = defaultdict(set)
    for _, row in df_work.iterrows():
        if pd.notna(row.get('name')):
            authors = [a.strip() for a in str(row['name']).split('|')]
            for author in authors:
                for topic_id, _ in row['top_2_topics_with_prop']:
                    author_topics[author].add(topic_id)
    
    author_counts = [len(t) for t in author_topics.values()]
    author_counts_array = np.array(author_counts)

    if len(author_counts) > 0:
        author_stats = {
            "mean"            : np.mean(author_counts_array),
            "median"          : int(np.median(author_counts_array)),
            "min"             : int(np.min(author_counts_array)),
            "max"             : int(np.max(author_counts_array)),
            "percentile_25"   : np.percentile(author_counts_array, 25),
            "percentile_75"   : np.percentile(author_counts_array, 75),
            "num_gt15"        : int(np.sum(author_counts_array > 15)),
            "unique_authors"  : len(author_counts_array)
        }
    else:
        author_stats = {}

    return g_freq, g_prop, g_comb, g_disp, author_stats
