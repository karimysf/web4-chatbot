from flask import session , render_template,redirect ,url_for,Blueprint
from utils.db import get_db_connection

pedagogie=Blueprint('pedagogie',__name__)


@pedagogie.route('/pedagogical-presence')
def pedagogical_presence():
    if session.get('user_type') != 'ResponsablePedagogique':
        return redirect(url_for('auth.login'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT p.*, a.NiveauDeConnaissance 
            FROM Presence p
            JOIN Apprenants a ON p.apprenant_id = a.id
            ORDER BY p.heure_connexion DESC
        """)
        presences = cursor.fetchall()
        
        return render_template('pedagogical_presence.html', presences=presences)
    except Exception as e:
        print(f"Erreur présence pédagogique : {str(e)}")
        return render_template('pedagogical_presence.html', presences=[])
    finally:
        cursor.close()
        conn.close()

# Configuration pour servir les fichiers statiques



@pedagogie.route('/pedagogical-knowledge-base')
def pedagogical_knowledge_base():
    if session.get('user_type') == 'ResponsablePedagogique':
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM BaseConnaissances")
        files = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('pedagocial_dash.html', files=files)
    return redirect(url_for('auth.login'))

