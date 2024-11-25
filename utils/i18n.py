import streamlit as st
import json
import os

class I18nManager:
    def __init__(self):
        self.translations = self._load_translations()

    def _load_translations(self):
        translations = {}
        translations_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'translations')
        
        for lang_file in os.listdir(translations_dir):
            if lang_file.endswith('.json'):
                lang = lang_file.split('.')[0]
                with open(os.path.join(translations_dir, lang_file), 'r', encoding='utf-8') as f:
                    translations[lang] = json.load(f)
        return translations

    def get_text(self, key):
        if not hasattr(st, 'session_state'):
            return key
            
        lang = st.session_state.get('language', 'es')
        if '.' in key:
            section, subkey = key.split('.', 1)
            return self.translations.get(lang, {}).get(section, {}).get(subkey, key)
        return self.translations.get(lang, {}).get(key, key)

