import json

def format_topics_data(data):
    """
    Prend des données brutes (dict ou list) et retourne un dictionnaire {topic_id: [mots]}.
    Utile si app.py charge le JSON depuis le Cloud et veut le nettoyer.
    """
    topics_data = {}
    
    try:
        if isinstance(data, dict):
            # Cas {topic_id: [words]}
            for k, v in data.items():
                topics_data[str(k)] = v
                
        elif isinstance(data, list):
            # Cas [{'topic_id': 1, 'topic_words': [...]}, ...]
            for entry in data:
                # On gère les clés variables
                t_id = entry.get('topic_id') or entry.get('id')
                t_words = entry.get('topic_words') or entry.get('words') or entry.get('keywords')
                
                if t_id is not None and t_words is not None:
                    topics_data[str(t_id)] = t_words
        else:
            return {}

        return topics_data

    except Exception as e:
        print(f"Erreur formattage topics: {e}")
        return {}
