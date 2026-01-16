import json

# ---------------------------------------------------------------------------
# JSON source
# ---------------------------------------------------------------------------
JSON_FILE = "topics_data.json"  # <-- your local JSON file

def get_lda_topics():
    """
    Retrieves LDA topics from a local JSON file and returns them
    as a dictionary identical to the one previously produced by the SQL database.
    """
    try:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        # We assume the JSON is a list of dicts or dict {topic_id: topic_words}
        # We convert to dict {str(topic_id): list of words}
        topics_data = {}
        if isinstance(data, dict):
            # case {topic_id: [words]}
            for k, v in data.items():
                topics_data[str(k)] = v
        elif isinstance(data, list):
            # case [{'topic_id': 1, 'topic_words': [...]}, ...]
            for entry in data:
                topic_id = str(entry['topic_id'])
                topics_data[topic_id] = entry['topic_words']
        else:
            print("Unexpected JSON format")
            return {}

        return topics_data

    except Exception as e:
        print(f"Error reading JSON file: {e}")
        return {}