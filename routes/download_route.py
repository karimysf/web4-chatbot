from flask import redirect, url_for, session,Blueprint,send_file
from utils.db import get_db_connection
from io import BytesIO
import pandas as pd
download_bp = Blueprint("/download",__name__)

@download_bp.route('/download-apprenants-excel')
def download_apprenants_excel():
    if session.get('user_type') != 'Administrateur':
        return redirect(url_for('auth.login'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT Nom, Prenom, AdresseEmail, Phone, Ville, TypeDeFormation, CodeCoupon,
                   DATE_FORMAT(DateDebutFormation, '%Y-%m-%d') as DateDebutFormation,
                   DATE_FORMAT(DateFinFormation, '%Y-%m-%d') as DateFinFormation,
                   Centre, NiveauDeConnaissance
            FROM Apprenants
        """)
        apprenants = cursor.fetchall()

        cursor.close()
        conn.close()

        # Convertir en DataFrame pandas
        df = pd.DataFrame(apprenants)

        # Créer un fichier Excel en mémoire
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        df.to_excel(writer, sheet_name='Apprenants', index=False)
        writer.close()
        output.seek(0)

        # Envoyer le fichier
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='apprenants_web4jobs.xlsx'
        )
    except Exception as e:
        print(f"Erreur lors de l'export Excel : {str(e)}")
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()
        return redirect(url_for('admin.admin_apprenants'))

@download_bp.route('/download-pedagogues-excel')
def download_pedagogues_excel():
    if session.get('user_type') != 'Administrateur':
        return redirect(url_for('auth.login'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT Nom, Prenom, AdresseEmail, Phone, Ville, CodeCoupon, Centre
            FROM ResponsablePedagogique
        """)
        pedagogues = cursor.fetchall()

        cursor.close()
        conn.close()

        # Convertir en DataFrame pandas
        df = pd.DataFrame(pedagogues)

        # Créer un fichier Excel en mémoire
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        df.to_excel(writer, sheet_name='Pedagogues', index=False)
        writer.close()
        output.seek(0)

        # Envoyer le fichier
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='pedagogues_web4jobs.xlsx'
        )
    except Exception as e:
        print(f"Erreur lors de l'export Excel : {str(e)}")
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()
        return redirect(url_for('admin.admin_pedagogues'))

@download_bp.route('/download-responsables-excel')
def download_responsables_excel():
    if session.get('user_type') != 'Administrateur':
        return redirect(url_for('auth.login'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT Nom, Prenom, AdresseEmail, Phone, Ville, Centre
            FROM Responsable_de_centre_de_coding
        """)
        responsables = cursor.fetchall()

        cursor.close()
        conn.close()

        # Convertir en DataFrame pandas
        df = pd.DataFrame(responsables)

        # Créer un fichier Excel en mémoire
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        df.to_excel(writer, sheet_name='Responsables', index=False)
        writer.close()
        output.seek(0)

        # Envoyer le fichier
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='responsables_web4jobs.xlsx'
        )
    except Exception as e:
        print(f"Erreur lors de l'export Excel : {str(e)}")
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()
        return redirect(url_for('admin.admin_centres'))