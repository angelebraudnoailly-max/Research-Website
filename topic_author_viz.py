import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import ast
from collections import Counter

# ---------------------------------------------------------------------------
# Load data from CSV
# ---------------------------------------------------------------------------
CSV_FILE = "https://storage.googleapis.com/russian_database/CAIRN_LDA_LIGHT.csv"  # <-- your CSV file
df_filtered = pd.read_csv(CSV_FILE)

# Ensure the 'annee' column is integer type
df_filtered["annee"] = df_filtered["annee"].astype(int)

# ---------------------------------------------------------------------------
# Create unique author list
# ---------------------------------------------------------------------------
all_names = set()
for cell in df_filtered['name']:
    if pd.notna(cell):
        names_in_cell = [name.strip() for name in cell.split('|')]
        all_names.update(names_in_cell)

unique_names = sorted(all_names)
print(f"Number of unique authors: {len(unique_names)}")

# ---------------------------------------------------------------------------
# Function to generate author graphs
# ---------------------------------------------------------------------------
def plot_author_topics(author, graph_type="full"):
    """
    author: str, author name
    graph_type: str, "full" for all topics, "top5" for top 5 topics
    Returns a matplotlib figure.
    """
    # Filter articles by author
    df_author = df_filtered[df_filtered["name"].str.contains(author, na=False)].copy()
    
    if df_author.empty:
        raise ValueError(f"No articles found for author: {author}")

    # Convert top_2_topics_with_prop column to list of tuples if needed
    if isinstance(df_author["top_2_topics_with_prop"].iloc[0], str):
        df_author["top_2_topics_with_prop"] = df_author["top_2_topics_with_prop"].apply(ast.literal_eval)

    # -----------------------------------------------------------------------
    # Full graph
    # -----------------------------------------------------------------------
    if graph_type == "full":
        df_author["topic_prop"] = df_author["top_2_topics_with_prop"].apply(lambda x: [(t[0], t[1]) for t in x])
        df_long = df_author.explode("topic_prop")
        df_long["topics"] = df_long["topic_prop"].apply(lambda x: x[0])
        df_long["props"]  = df_long["topic_prop"].apply(lambda x: x[1])

        df_agg = df_long.groupby(["annee","topics"], as_index=False).agg(mean_prop=("props","mean"))
        topics_sorted = sorted(df_agg["topics"].unique())
        num_topics = len(topics_sorted)
        
        # Adjust dimensions
        height = max(0.5 * num_topics, 6)
        width = 14
        if num_topics > 20: width = 16
        if num_topics > 30: width = 18

        fig, ax = plt.subplots(figsize=(width, height))

        # Colors
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
        ax.set_title(f"Discrete Time Bands – {author}")

        years_min, years_max = int(df_agg["annee"].min()), int(df_agg["annee"].max())
        if (years_max - years_min) > 30:
            years_ticks = np.arange(years_min, years_max + 1, 5)
        else:
            years_ticks = np.arange(years_min, years_max + 1, 1)
        ax.set_xticks(years_ticks)
        ax.tick_params(axis='x', rotation=45, labelsize=8)
        ax.grid(axis="x", linestyle=":", alpha=0.3)
        plt.subplots_adjust(left=0.15, right=0.85, top=0.95, bottom=0.1)

        # Legend
        total_articles = df_author.shape[0]
        total_topics = num_topics
        legend_elements = []
        for size in [0.05, 0.2, 0.4]:
            legend_elements.append(
                plt.Line2D([0], [0], marker='o', color='w',
                          markerfacecolor='gray', markersize=np.sqrt(size*500)/2,
                          label=f"Size = {size} mean proportion",
                          alpha=0.7)
            )
        legend_elements.append(
            plt.Line2D([0], [0], marker='', color='w', 
                      label=f"Total Articles: {total_articles}\nTotal Topics: {total_topics}")
        )
        ax.legend(handles=legend_elements, title="Legend",
                  bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0, fontsize=10)
        return fig

    # -----------------------------------------------------------------------
    # Top 5 topics
    # -----------------------------------------------------------------------
    elif graph_type == "top5":
        all_topics = [t[0] for sublist in df_author["top_2_topics_with_prop"] for t in sublist]
        top5_topics = [t for t, _ in Counter(all_topics).most_common(5)]

        df_author["topic_prop"] = df_author["top_2_topics_with_prop"].apply(
            lambda x: [(t[0], t[1]) for t in x if t[0] in top5_topics]
        )

        df_long = df_author.explode("topic_prop")
        df_long = df_long[df_long["topic_prop"].notna()]
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
        ax.set_title(f"Top 5 Topics – {author}")

        years_min, years_max = int(df_agg["annee"].min()), int(df_agg["annee"].max())
        if (years_max - years_min) > 30:
            years_ticks = np.arange(years_min, years_max + 1, 5)
        else:
            years_ticks = np.arange(years_min, years_max + 1, 1)
        ax.set_xticks(years_ticks)
        ax.tick_params(axis='x', rotation=45, labelsize=8)
        ax.grid(axis="x", linestyle=":", alpha=0.3)
        plt.subplots_adjust(left=0.15, right=0.85, top=0.95, bottom=0.1)

        articles_with_top5 = df_author[df_author["topic_prop"].apply(lambda x: len(x) > 0)]["url"].nunique()
        total_topics = df_long["topics"].nunique()
        ax.legend(
            title=f"Top 5 Topics\n(Size = mean proportion)\nArticles: {articles_with_top5}, Topics: {total_topics}",
            bbox_to_anchor=(1.05, 1),
            loc='upper left',
            borderaxespad=0.,
            fontsize=10
        )
        return fig

    else:
        raise ValueError("graph_type must be 'full' or 'top5'")