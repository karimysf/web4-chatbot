from flask import Blueprint, request, session, redirect, url_for, render_template, flash
from utils.db import get_db_connection  
from datetime import datetime
from utils.hash import verify_password

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def login():
    return render_template('login.html', title='login-page')

@auth_bp.route('/authenticate', methods=['POST'])
def authenticate():
    try:
        user_type = request.form.get('user_type')
        email = request.form.get('email')
        password = request.form.get('password')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        table_map = {
            "Apprenants": "Apprenants",
            "ResponsablePedagogique": "ResponsablePedagogique",
            "Responsable_de_centre_de_coding": "Responsable_de_centre_de_coding",
            "Administrateur": "Administrateur"  # Note: There's a typo here - should match your actual table name
        }

        if user_type not in table_map:
            flash("Type d'utilisateur invalide", "error")
            return redirect(url_for('auth.login'))

        # First check if user exists
        cursor.execute(f'''
            SELECT * FROM {table_map[user_type]}
            WHERE AdresseEmail = %s
        ''', (email,))
        user = cursor.fetchone()

        if not user:
            flash("Utilisateur non trouvé", "error")
            cursor.close()
            conn.close()
            return redirect(url_for('auth.login'))

        # Then verify password
        if not verify_password(user['MotDePasse'], password):
            
            flash("Mot de passe incorrect", "error")
            cursor.close()
            conn.close()
            return redirect(url_for('auth.login'))

        # If we get here, authentication was successful
        if user_type == "Apprenants":
            now = datetime.now()
            # Insertion dans les deux tables de présence
            cursor.execute('''
                INSERT INTO Presence
                (apprenant_id, Nom, Prenom, AdresseEmail, Centre, date_connexion, heure_connexion)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (user['id'], user['Nom'], user['Prenom'], user['AdresseEmail'], user['Centre'], now.date(), now))

            cursor.execute('''
                INSERT INTO PresenceCentre
                (apprenant_id, Nom, Prenom, AdresseEmail, Centre, date_connexion, heure_connexion)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (user['id'], user['Nom'], user['Prenom'], user['AdresseEmail'], user['Centre'], now.date(), now))
            conn.commit()

        session['user_type'] = user_type
        session['user_id'] = user['id']
        session['email'] = email

        if user_type == "Responsable_de_centre_de_coding":
            session['centre'] = user['Centre']

        cursor.close()
        conn.close()
        return redirect(url_for('dash.dashboard'))

    except Exception as e:
        print(f"Erreur d'authentification : {str(e)}")
        flash("Une erreur s'est produite lors de l'authentification", "error")
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()
        return redirect(url_for('auth.login'))