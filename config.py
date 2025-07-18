import os
from dotenv import load_dotenv



#Definition des Constantes ENV


load_dotenv()

DB_USERNAME = os.getenv('DB_USERNAME')
DB_HOST = os.getenv('DB_HOST')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')
DB_PORT = os.getenv('DB_PORT')
APP_SECRET_KEY = os.getenv('APP_SECRET_KEY')
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')


def urlize(text, max_length=None):
    import re
    url_pattern = re.compile(r'(https?://\S+)')
    # Remplacer les URLs par des liens HTML
    result = re.sub(url_pattern, r'<a href="\1" target="_blank">\1</a>', text)
    # Tronquer le texte si nécessaire
    if max_length:
        result = result[:max_length] + '...' if len(result) > max_length else result
    return result