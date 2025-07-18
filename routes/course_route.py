from flask import flash ,session,request,redirect,url_for,render_template,Blueprint
from utils.db import get_db_connection
import re 

course_bp=Blueprint('course',__name__)

def extract_youtube_id(url):
    if not url:
        return None
    pattern = r'(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=))([^?&]+)'
    match = re.search(pattern, url)
    return match.group(1) if match else None


@course_bp.route('/centre-courses', methods=['GET', 'POST'])
def centre_courses():
    if session.get('user_type') != 'Responsable_de_centre_de_coding':
        return redirect(url_for('auth.login'))

    centre = session.get('centre')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        email = request.form.get('email')
        intitule = request.form.get('intitule')
        description = request.form.get('description')
        objectifs = request.form.get('objectifs')
        video_url = request.form.get('video_url')
        date_debut = request.form.get('date_debut')
        date_fin = request.form.get('date_fin')
        centre = request.form.get('centre')

        # Vérification que l'apprenant existe dans le même centre
        cursor.execute("""
            SELECT id FROM Apprenants
            WHERE AdresseEmail = %s AND Centre = %s
        """, (email, centre))

        if not cursor.fetchone():
            flash("L'apprenant n'existe pas dans votre centre", 'error')
            return redirect(url_for('course.centre_courses'))

        video_id = extract_youtube_id(video_url)
        if not video_id:
            flash("Lien YouTube invalide", 'error')
            return redirect(url_for('course.centre_courses'))

        try:
            cursor.execute("""
                INSERT INTO Parcours
                (intitule, description, objectifs, video_url, date_debut, date_fin, email_apprenant, centre)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (intitule, description, objectifs, video_id, date_debut, date_fin, email, centre))

            conn.commit()
            flash("Parcours créé avec succès", 'success')
        except Exception as e:
            conn.rollback()
            flash(f"Erreur de création : {str(e)}", 'error')

    # Récupération des parcours du centre
    cursor.execute("""
        SELECT p.*, a.Nom AS nom_apprenant, a.Prenom AS prenom_apprenant
        FROM Parcours p
        JOIN Apprenants a ON p.email_apprenant = a.AdresseEmail
        WHERE p.centre = %s
    """, (centre,))

    parcours = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('centre_courses.html', parcours=parcours, centre=centre)


@course_bp.route('/courses')
def courses():
    if session.get('user_type') != 'Apprenants':
        return redirect(url_for('auth.login'))

    email = session.get('email')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Utilisation de DISTINCT pour éviter les doublons
    cursor.execute("""
        SELECT DISTINCT p.*
        FROM Parcours p
        JOIN Apprenants a ON p.email_apprenant = a.AdresseEmail
        WHERE a.AdresseEmail = %s
    """, (email,))

    parcours_list = cursor.fetchall()

    for parcours in parcours_list:
        parcours['video_id'] = parcours['video_url']  # Déjà stocké comme ID

    cursor.close()
    conn.close()

    return render_template('courses.html', mes_parcours=parcours_list)
