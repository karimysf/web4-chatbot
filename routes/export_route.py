from flask import Blueprint,session,redirect,url_for,send_file
import pandas as pd
from utils.db import get_db_connection
from io import BytesIO


export_bp = Blueprint('export',__name__)

 

@export_bp.route('/export-presence-excel')
def export_presence_excel():
    if session.get('user_type') != 'ResponsablePedagogique':
        return redirect(url_for('auth.login'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Récupérer toutes les présences
        cursor.execute("""
            SELECT Nom, Prenom, AdresseEmail, date_connexion, 
                   heure_connexion, heure_deconnexion, Centre,
                   CASE WHEN heure_deconnexion IS NULL THEN 'Connecté' ELSE 'Déconnecté' END as statut
            FROM Presence 
            ORDER BY heure_connexion DESC
        """)
        presences = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Convertir en DataFrame pandas
        df = pd.DataFrame(presences)
        
        # Créer un fichier Excel en mémoire
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        df.to_excel(writer, sheet_name='Presences', index=False)
        writer.close()
        output.seek(0)
        
        # Envoyer le fichier
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='presences_web4jobs.xlsx'
        )
    except Exception as e:
        print(f"Erreur lors de l'export Excel : {str(e)}")
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()
        return redirect(url_for('pedagogical_presence'))



@export_bp.route('/export-centre-presence-excel')
def export_centre_presence_excel():
    if session.get('user_type') != 'Responsable_de_centre_de_coding':
        return redirect(url_for('auth.login'))

    centre = session.get('centre')
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Récupérer les présences du centre spécifique
        cursor.execute("""
            SELECT Nom, Prenom, AdresseEmail, date_connexion,
                   heure_connexion, heure_deconnexion, Centre,
                   CASE WHEN heure_deconnexion IS NULL THEN 'Connecté' ELSE 'Déconnecté' END as statut
            FROM PresenceCentre
            WHERE Centre = %s
            ORDER BY heure_connexion DESC
        """, (centre,))
        presences = cursor.fetchall()

        cursor.close()
        conn.close()

        # Convertir en DataFrame pandas
        df = pd.DataFrame(presences)

        # Créer un fichier Excel en mémoire
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        df.to_excel(writer, sheet_name='Presences', index=False)
        writer.close()
        output.seek(0)

        # Envoyer le fichier
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='presences_centre_web4jobs.xlsx'
        )
    except Exception as e:
        print(f"Erreur lors de l'export Excel : {str(e)}")
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()
        return redirect(url_for('centre_apprenants'))
