from flask import Flask, render_template, request, redirect, flash, jsonify
from graph import get_graphs               # Reading from local CSV files
from contact import send_email
from topics import get_lda_topics          # Reading from JSON
from topics_viz import get_lda_insights    # Reading from local CSV files
import topic_author_viz                     # Author graphs from CSV
import io
import base64
import matplotlib.pyplot as plt

app = Flask(__name__)
app.secret_key = "secret"

# ---------------------------------------------------------------------------
# MAIN ROUTE
# ---------------------------------------------------------------------------
@app.route("/", methods=['GET'])
def index():
    """
    Main route that assembles graphs, LDA data, and Insights visualizations.
    """
    # 1. Get time series graphs (Base64)
    graph_mon, graph_cairn = get_graphs()
    
    # 2. Get LDA topics list from JSON
    lda_topics = get_lda_topics()
    
    # 3. Get LDA insights (Base64 graphs + stats dictionary)
    g_freq, g_prop, g_comb, g_disp, author_stats = get_lda_insights()
    
    # 4. Send all variables to index.html template, including author list
    return render_template(
        "index.html",
        graph_mon=graph_mon,
        graph_cairn=graph_cairn,
        topics=lda_topics,
        g_freq=g_freq,
        g_prop=g_prop,
        g_comb=g_comb,
        g_disp=g_disp,
        author_stats=author_stats,
        unique_names=topic_author_viz.unique_names  # dropdown with authors
    )

# ---------------------------------------------------------------------------
# CONTACT ROUTE
# ---------------------------------------------------------------------------
@app.route("/contact", methods=['POST'])
def contact_route():
    """
    Contact form handler.
    """
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
# AUTHOR GRAPHS ROUTE
# ---------------------------------------------------------------------------
@app.route("/author_graphs", methods=["POST"])
def author_graphs():
    """
    Generates a graph for a given author (full or top5) and returns the image in Base64.
    """
    data = request.json
    author = data.get("author")
    graph_type = data.get("graph_type", "full")  # "full" or "top5"

    # Create graph via topic_author_viz
    fig = topic_author_viz.plot_author_topics(author, graph_type=graph_type)

    # Convert to Base64 for frontend
    img_bytes = io.BytesIO()
    fig.savefig(img_bytes, format="png", bbox_inches="tight")
    plt.close(fig)
    img_bytes.seek(0)
    img_base64 = base64.b64encode(img_bytes.read()).decode("utf-8")

    return jsonify({"img": img_base64})

# ---------------------------------------------------------------------------
# SERVER LAUNCH
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Launch server on port 8080
    app.run(host='0.0.0.0', port=8080, debug=True)