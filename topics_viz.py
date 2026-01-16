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
# CSV source
# ---------------------------------------------------------------------------
CSV_FILE = "https://storage.googleapis.com/russian_database/CAIRN_LDA_LIGHT.csv"  # <-- your local CSV file

# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------
def fig_to_base64(plt_fig):
    """Convert a Matplotlib figure to a Base64 string."""
    img = io.BytesIO()
    plt_fig.tight_layout()
    plt_fig.savefig(img, format="png", dpi=120)
    img.seek(0)
    base64_str = base64.b64encode(img.getvalue()).decode()
    plt.close()
    return base64_str

def safe_parse(x):
    """Convert a string representing a list/tuple to a Python object."""
    if isinstance(x, str):
        return ast.literal_eval(x)
    return x

# ---------------------------------------------------------------------------
# Main function to generate graphs and statistics
# ---------------------------------------------------------------------------
def get_lda_insights():
    """Generate 4 LDA graphs and author statistics from CSV."""
    # Read directly from the CSV file
    df = pd.read_csv(CSV_FILE)

    # Parsing columns of list type
    df["top_2_topics_with_prop"] = df["top_2_topics_with_prop"].apply(safe_parse)

    # --- Prepare data for topics ---
    all_top2 = [t for sub in df["top_2_topics_with_prop"] for t, _ in sub]
    topic_freq = Counter(all_top2)
    topic_props = defaultdict(list)
    for sub in df["top_2_topics_with_prop"]:
        for t, p in sub:
            topic_props[t].append(p)
    avg_props = {t: sum(ps)/len(ps) for t, ps in topic_props.items()}

    # --- Graph 1: Frequency ---
    top_f = topic_freq.most_common(15)
    ts, cs = zip(*top_f) if top_f else ([], [])
    plt.figure(figsize=(10, 7))
    plt.bar(range(len(ts)), cs, color="skyblue")
    plt.xticks(range(len(ts)), ts, rotation=45)
    plt.xlabel("Topic")
    plt.ylabel("Frequency")
    plt.title("Top 15 Topics by Frequency")
    g_freq = fig_to_base64(plt)

    # --- Graph 2: Proportion ---
    top_p = sorted(avg_props.items(), key=lambda x: x[1], reverse=True)[:15]
    ts, ps = zip(*top_p) if top_p else ([], [])
    plt.figure(figsize=(10, 7))
    plt.bar(range(len(ts)), ps, color="salmon")
    plt.xticks(range(len(ts)), ts, rotation=45)
    plt.xlabel("Topic")
    plt.ylabel("Average Proportion")
    plt.title("Top 15 Topics by Average Proportion")
    g_prop = fig_to_base64(plt)

    # --- Graph 3: Combined ---
    combined = {t: topic_freq[t] * avg_props[t] for t in topic_freq}
    top_c = sorted(combined.items(), key=lambda x: x[1], reverse=True)[:15]
    ts, ss = zip(*top_c) if top_c else ([], [])
    plt.figure(figsize=(10, 7))
    plt.bar(range(len(ts)), ss, color="plum")
    plt.xticks(range(len(ts)), ts, rotation=45)
    plt.xlabel("Topic")
    plt.ylabel("Combined Score")
    plt.title("Top 15 Topics (Combined Score)")
    g_comb = fig_to_base64(plt)

    # --- Graph 4: Dispersion ---
    disp = df.groupby("url")["top_2_topics_with_prop"].apply(lambda x: len({t for s in x for t, _ in s}))
    plt.figure(figsize=(10, 7))
    plt.hist(disp, bins=range(int(disp.min()), int(disp.max()) + 2), align="left", rwidth=0.8, color="teal")
    plt.xlabel("Number of Unique Topics per Article")
    plt.ylabel("Number of Articles")
    plt.title("Thematic Dispersion per Article")
    g_disp = fig_to_base64(plt)

    # --- Author statistics ---
    author_topics = defaultdict(set)
    for _, row in df.iterrows():
        if pd.notna(row['name']):
            authors = [a.strip() for a in str(row['name']).split('|')]
            for author in authors:
                for topic_id, _ in row['top_2_topics_with_prop']:
                    author_topics[author].add(topic_id)
    
    author_counts = [len(t) for t in author_topics.values()]
    author_counts_array = np.array(author_counts)

    author_stats = {
        "mean"            : np.mean(author_counts_array) if author_counts else 0,
        "median"          : int(np.median(author_counts_array)) if author_counts else 0,
        "min"             : int(np.min(author_counts_array)) if author_counts else 0,
        "max"             : int(np.max(author_counts_array)) if author_counts else 0,
        "percentile_25"   : np.percentile(author_counts_array, 25) if author_counts else 0,
        "percentile_75"   : np.percentile(author_counts_array, 75) if author_counts else 0,
        "num_gt15"        : int(np.sum(author_counts_array > 15)) if author_counts else 0,
        "unique_authors"  : len(author_counts_array)
    }

    return g_freq, g_prop, g_comb, g_disp, author_stats