from flask import jsonify, session , redirect ,url_for,request,render_template,Blueprint
import re
from utils.db import get_db_connection

tuto_bp=Blueprint('tuto',__name__)

@tuto_bp.route('/api/delete-tutorial/<int:tuto_id>', methods=['DELETE'])
def delete_tutorial(tuto_id):
    if session.get('user_type') != 'ResponsablePedagogique':
        return jsonify({'error': 'Non autorisé'}), 403

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Tutoriels WHERE id = %s", (tuto_id,))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'message': 'Tutoriel supprimé'}), 200



@tuto_bp.route('/pedagogical-tutorials', methods=['GET', 'POST'])
def pedagogical_tutorials():
    if session.get('user_type') != 'ResponsablePedagogique':
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        categorie = request.form.get('categorie')
        video_url = request.form.get('video-url')
        description = request.form.get('description')
        objectifs = request.form.get('objectifs')

        if not video_url:
            return "Veuillez insérer un lien YouTube", 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Tutoriels (categorie, video_url, description, objectifs)
            VALUES (%s, %s, %s, %s)
        """, (categorie, video_url, description, objectifs))
        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for('pedagogical_tutorials'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Tutoriels")
    tutoriels = cursor.fetchall()
    cursor.close()
    conn.close()
    
    # Correction de l'indentation ici
    for tuto in tutoriels:
        match = re.search(
            r'(?:youtu\.be/|youtube\.com/(?:embed/|v/|watch\?v=|watch\?.+&v=))([^?&]+)',
            tuto['video_url']
        )
        tuto['video_id'] = match.group(1) if match else None

    return render_template('pedagogical_tuto.html', tutoriels=tutoriels)


@tuto_bp.route('/api/add-tutorial', methods=['POST'])
def api_add_tutorial():
    data = request.get_json()
    categorie = data.get('categorie')
    video_url = data.get('video_url')
    description = data.get('description')
    objectifs = data.get('objectifs')

    if not video_url:
        return jsonify({'error': 'URL manquante'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Tutoriels (categorie, video_url, description, objectifs)
        VALUES (%s, %s, %s, %s)
    """, (categorie, video_url, description, objectifs))
    conn.commit()

    # Récupérer l’ID vidéo YouTube
    match = re.search(r'(?:youtu\.be/|youtube\.com/(?:embed/|v/|watch\?v=|watch\?.+&v=))([^?&]+)', video_url)
    video_id = match.group(1) if match else None

    cursor.close()
    conn.close()

    return jsonify({
        'categorie': categorie,
        'description': description,
        'objectifs': objectifs,
        'video_id': video_id
    }), 200
    