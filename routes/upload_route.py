

from flask import request ,Blueprint,send_file,send_from_directory
import os 
import io 
from utils.db import get_db_connection
import mysql.connector
from config import UPLOAD_FOLDER

upload_bp = Blueprint('upload',__name__)

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'json'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



@upload_bp.route('/upload', methods=['POST'])
def upload_file():
    print(">>> upload_file() called !")

    titre = request.form.get('titre')
    description = request.form.get('description')
    fichier = request.files.get('fichier')
    lien_web = request.form.get('lien_web')

    if not titre or not description:
        return 'Le titre et la description sont requis', 400

    fichier_data = b''  # Valeur par défaut pour fichier_data
    type_fichier = 'none'  # Valeur par défaut pour type_fichier

    if fichier and fichier.filename != '':
        filename = fichier.filename
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        fichier.save(filepath)

        with open(filepath, 'rb') as f:
            fichier_data = f.read()
        type_fichier = filename.rsplit('.', 1)[1].lower()

    conn = get_db_connection()
    cursor = conn.cursor()
    print("Titre:", titre)
    print("Description:", description)
    print("Type fichier:", type_fichier) 
    print("Lien:", lien_web)
    print("File size:", len(fichier_data))

    try:
        cursor.execute("""
            INSERT INTO BaseConnaissances (titre, description, fichier, type_fichier, lien_web)
            VALUES (%s, %s, %s, %s, %s)
        """, (titre, description, fichier_data, type_fichier, lien_web))
        conn.commit()
    except mysql.connector.Error as err:
        print(f"Erreur MySQL: {err}")
        return f"Erreur de base de données: {err}", 500
    finally:
        cursor.close()
        conn.close()

    return 'Fichier ou lien téléchargé avec succès', 200


@upload_bp.route('/view/<int:file_id>')
def view_file(file_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM BaseConnaissances WHERE id = %s", (file_id,))
    file_data = cursor.fetchone()
    cursor.close()
    conn.close()

    if file_data:
        return send_file(
            io.BytesIO(file_data['fichier']),
            mimetype=f'application/{file_data["type_fichier"]}',
            as_attachment=False,
            download_name=f'{file_data["titre"]}.{file_data["type_fichier"]}'
        )
    else:
        return 'Fichier non trouvé', 404
@upload_bp.route('/static/<path:filename>')
def serve_static(filename):
    root_dir = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(root_dir, filename)


