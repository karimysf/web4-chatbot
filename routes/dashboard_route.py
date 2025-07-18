
from flask import render_template , session , redirect , url_for ,request ,Blueprint
from datetime import datetime

from utils.db import get_db_connection
dash_bp=Blueprint('dash',__name__)
@dash_bp.route('/dashboard')
def dashboard():
    user_type = session.get('user_type')

    if not user_type:
        return redirect(url_for('auth.login'))

    if user_type == "Responsable_de_centre_de_coding":
        return render_template('respo_coding_dashboard.html',title="respo_coding_dash")
    elif user_type == "Apprenants":
        return render_template('learn_dashboard.html')
    elif user_type == "ResponsablePedagogique":
        return render_template('pedagogical_dash.html')
    elif user_type == "Administrateur":
        return render_template('admin_dash.html')

    return redirect(url_for('auth.login'))

@dash_bp.route('/knowledge-base')
def knowledge_base():
    # Redirection immédiate pour tous les utilisateurs non autorisés
    if session.get('user_type') not in ['ResponsablePedagogique', 'Responsable_de_centre_de_coding']:
        return redirect(url_for('dash.dashboard'))
    return render_template('knowledge_base_2')

@dash_bp.route('/tutorials')
def tutorials():
    if session.get('user_type') == 'Apprenants':
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Tutoriels")
        tutoriels = cursor.fetchall()
        cursor.close()
        conn.close()

        for tuto in tutoriels:
            match = re.search(
                r'(?:youtu\.be/|youtube\.com/(?:embed/|v/|watch\?v=|watch\?.+&v=))([^?&]+)',
                tuto['video_url']
            )
            tuto['video_id'] = match.group(1) if match else None

        return render_template('learner_tuto.html', tutoriels=tutoriels)
    return redirect(url_for('auth.login'))





@dash_bp.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')
    results = perform_search(query)
    return render_template('search_results.html', results=results)


def perform_search(query):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT title, content FROM knowledge_base WHERE content LIKE %s', ('%' + query + '%',))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results




@dash_bp.route('/logout')
def logout():
    user_type = session.get('user_type')
    user_id = session.get('user_id')
    
    if user_type == "Apprenants" and user_id:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            now = datetime.now()
            # Mise à jour dans les deux tables
            cursor.execute("""
                UPDATE Presence 
                SET heure_deconnexion = %s 
                WHERE apprenant_id = %s 
                ORDER BY heure_connexion DESC 
                LIMIT 1
            """, (now, user_id))
            
            cursor.execute("""
                UPDATE PresenceCentre 
                SET heure_deconnexion = %s 
                WHERE apprenant_id = %s 
                ORDER BY heure_connexion DESC 
                LIMIT 1
            """, (now, user_id))
            
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Erreur déconnexion : {str(e)}")

    session.clear()
    return redirect(url_for('auth.login'))

