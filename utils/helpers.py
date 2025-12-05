import json

def load_config():
    try:
        with open("data/ticket_config.json", "r") as f:
            return json.load(f)
    except:
        return {}

def save_config(data):
    with open("data/ticket_config.json", "w") as f:
        json.dump(data, f, indent=4)
