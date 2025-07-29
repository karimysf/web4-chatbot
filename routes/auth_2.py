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
        user_type = request.form.get('user_type')
        email = request.form.get('email')
        password = request.form.get('password')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        table_map = {
            "Apprenants",
            "ResponsablePedagogique",
             "Responsable_de_centre_de_coding",
            "Administrateur"  
        }

        if user_type not in table_map:
            flash("Type d'utilisateur invalide", "error")
            return redirect(url_for('auth.login'))

        # First check if user exists
        cursor.execute(f'''
            SELECT * FROM {user_type}
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
    

@auth_bp.route('/register', methods=['GET'])
def register():
    return render_template('register.html')


@auth_bp.route('/register', methods=['POST'])
def handle_register():
    # Get form data
    user_type = request.form.get('user_type')
    nom = request.form.get('nom')
    prenom = request.form.get('prenom')
    email = request.form.get('email')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    phone = request.form.get('phone')
    ville = request.form.get('ville')
    
    # Validate passwords match
    if password != confirm_password:
        flash('Les mots de passe ne correspondent pas', 'error')
        return redirect(url_for('auth.register'))
    
    # Hash the password
    hashed_password = hash_password(password)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if email already exists
        cursor.execute(f"SELECT AdresseEmail FROM {user_type} WHERE AdresseEmail = %s", (email,))
        if cursor.fetchone():
            flash('Cet email est déjà utilisé', 'error')
            return redirect(url_for('auth.register'))
        
        # Handle different user types
        if user_type == 'Apprenants':
            type_formation = request.form.get('type_formation')
            code_coupon = request.form.get('code_coupon')
            niveau_connaissance = request.form.get('niveau_connaissance')
            
            cursor.execute("""
                INSERT INTO Apprenants 
                (Nom, Prenom, AdresseEmail, MotDePasse, Phone, Ville, 
                 TypeDeFormation, CodeCoupon, NiveauDeConnaissance)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                nom, prenom, email, hashed_password, phone, ville,
                type_formation, code_coupon, niveau_connaissance
            ))
            
        elif user_type == 'Responsable_de_centre_de_coding':
            centre = request.form.get('centre')
            
            cursor.execute("""
                INSERT INTO Responsable_de_centre_de_coding 
                (Nom, Prenom, AdresseEmail, MotDePasse, Phone, Ville, Centre)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                nom, prenom, email, hashed_password, phone, ville, centre
            ))
            
        elif user_type == 'ResponsablePedagogique':
            # Add specific fields for Responsable Pédagogique if needed
            cursor.execute("""
                INSERT INTO ResponsablePedagogique 
                (Nom, Prenom, AdresseEmail, MotDePasse, Phone, Ville)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                nom, prenom, email, hashed_password, phone, ville
            ))
            
        conn.commit()
        flash('Inscription réussie! Vous pouvez maintenant vous connecter.', 'success')
        return redirect(url_for('auth.login'))
        
    except Exception as e:
        conn.rollback()
        flash(f"Erreur lors de l'inscription: {str(e)}", 'error')
        return redirect(url_for('auth.register'))
    finally:
        cursor.close()
        conn.close()