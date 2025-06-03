import json
import os


def load_language(lang_code):
    script_dir = os.path.dirname(__file__)
    lang_dir = os.path.join(script_dir, '..', 'lang')  # Navigate to the lang directory
    lang_file = os.path.join(lang_dir, f"{lang_code}.json")

    if not os.path.exists(lang_file):
        raise FileNotFoundError(f"Language file not found: {lang_file}")

    with open(lang_file, 'r', encoding='utf-8') as f:
        return json.load(f)
