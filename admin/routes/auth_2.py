from flask import Blueprint, request, session, redirect, url_for, render_template, flash
from utils.db import get_db_connection  
from datetime import datetime
from utils.hash import verify_password,hash_password

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def login():
    return render_template('login.html', title='login-page')

@auth_bp.route('/authenticate', methods=['POST'])
def authenticate():
    try:
        email = request.form.get('email')
        password = request.form.get('password')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Check if admin exists
        cursor.execute('''
            SELECT * FROM Administrateur
            WHERE AdresseEmail = %s
        ''', (email,))
        admin = cursor.fetchone()

        if not admin:
            flash("Administrateur non trouvé", "error")
            cursor.close()
            conn.close()
            return redirect(url_for('auth.login'))

        # Verify password
        if not verify_password(admin['MotDePasse'], password):
            flash("Mot de passe incorrect", "error")
            cursor.close()
            conn.close()
            return redirect(url_for('auth.login'))

        # Store session
        session['user_type'] = "Administrateur"
        session['user_id'] = admin['id']
        session['email'] = email

        cursor.close()
        conn.close()
        return redirect(url_for('dash.dashboard'))

    except Exception as e:
        print(f"Erreur d'authentification admin : {str(e)}")
        flash("Erreur lors de l'authentification", "error")
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        return redirect(url_for('auth.login'))

