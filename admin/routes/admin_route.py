

from utils.db import get_db_connection
from flask import Blueprint, render_template, request, redirect, url_for,  session, jsonify
import mysql.connector
from utils.hash import hash_password,is_hashed

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin-dashboard')

def admin_dashboard():
    return render_template('admin_rapports.html', url_for=url_for)

@admin_bp.route('/get-admin-data')

def get_admin_data():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Requête Apprenants
    cursor.execute("SELECT COUNT(*) as total FROM Apprenants")
    total_apprenants = cursor.fetchone()['total']

    # Requête Responsables pédagogiques
    cursor.execute("SELECT COUNT(*) as total FROM ResponsablePedagogique")
    total_responsables_pedagogiques = cursor.fetchone()['total']

    # Requête CENTRE — ❗ vérifier si tu as bien une table "Centre"
    cursor.execute("SELECT COUNT(DISTINCT Centre) as total FROM Apprenants")
    total_centres = cursor.fetchone()['total']

    # Requête Responsables Coding
    cursor.execute("SELECT COUNT(*) as total FROM Responsable_de_centre_de_coding")
    total_responsables_coding = cursor.fetchone()['total']

    cursor.close()
    conn.close()

    return jsonify({
        "total_apprenants": total_apprenants,
        "total_responsables_pedagogiques": total_responsables_pedagogiques,
        "total_centres": total_centres,
        "total_responsables_coding": total_responsables_coding
    })




@admin_bp.route('/admin-pedagogues')
def admin_pedagogues():
    if session.get('user_type') != 'Administrateur':
        return redirect(url_for('auth.login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT id, Nom, Prenom, AdresseEmail, MotDePasse,
                   Phone, Ville, CodeCoupon, Centre 
            FROM ResponsablePedagogique
        """)
        pedagogues = cursor.fetchall()
        return render_template('admin_pedagogues.html', pedagogues=pedagogues)
    
    except Exception as e:
        print(f"Erreur base de données : {str(e)}")
        return render_template('admin_pedagogues.html', pedagogues=[])
    
    finally:
        cursor.close()
        conn.close()

def create_crud_routes(table_type):
    endpoint = table_type.lower().replace('_', '') + "_crud"

    @admin_bp.route(f'/admin/save-{table_type}', methods=['POST'], endpoint=f'save_{endpoint}')
    def save_handler():
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            for item in data:
                if item['id'] == 'new':
                    cursor.execute(f"""
                        INSERT INTO {table_type} 
                        (Nom, Prenom, AdresseEmail, MotDePasse, Phone, Ville, CodeCoupon, Centre)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        item['data']['Nom'],
                        item['data']['Prenom'],
                        item['data']['AdresseEmail'],
                        item['data']['MotDePasse'],
                        item['data']['Phone'],
                        item['data']['Ville'],
                        item['data']['CodeCoupon'],
                        item['data']['Centre']
                    ))
                else:
                    cursor.execute(f"""
                        UPDATE {table_type} SET
                        Nom = %s,
                        Prenom = %s,
                        AdresseEmail = %s,
                        MotDePasse = %s,
                        Phone = %s,
                        Ville = %s,
                        CodeCoupon = %s,
                        Centre = %s
                        WHERE id = %s
                    """, (
                        item['data']['Nom'],
                        item['data']['Prenom'],
                        item['data']['AdresseEmail'],
                        item['data']['MotDePasse'],
                        item['data']['Phone'],
                        item['data']['Ville'],
                        item['data']['CodeCoupon'],
                        item['data']['Centre'],
                        item['id']
                    ))
            conn.commit()
            return jsonify({'status': 'success'})
        except Exception as e:
            conn.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            cursor.close()
            conn.close()

create_crud_routes('Responsable_de_centre_de_coding')
create_crud_routes('ResponsablePedagogique')







@admin_bp.route('/save-pedagogues', methods=['POST'])
def save_pedagogues():
    if session.get('user_type') != 'Administrateur':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()

        # First pass: Validate all emails before making any changes
        for change in data:
            if change['action'] in ['create', 'update']:
                email = change.get('AdresseEmail') or change.get('fields', {}).get('AdresseEmail')
                if email:
                    # Check if email exists (excluding current record for updates)
                    query = """
                        SELECT id FROM ResponsablePedagogique 
                        WHERE LOWER(AdresseEmail) = LOWER(%s)
                    """
                    params = [email]
                    
                    if change['action'] == 'update':
                        query += " AND id != %s"
                        params.append(change['id'])
                    
                    cursor.execute(query, params)
                    if cursor.fetchone():
                        return jsonify({
                            'status': 'error',
                            'message': f"L'email {email} est déjà utilisé",
                            'error_code': 'email_taken',
                            'duplicate_email': email
                        }), 400

        # Second pass: Process changes if all validations passed
        new_ids = []
        for change in data:
            if change['action'] == 'create':
                cursor.execute("""
                    INSERT INTO ResponsablePedagogique
                    (Nom, Prenom, AdresseEmail, MotDePasse, Phone, Ville, CodeCoupon, Centre)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    change.get('Nom', ''),
                    change.get('Prenom', ''),
                    change.get('AdresseEmail', ''),
                    change.get('MotDePasse', ''),  # Should be hashed
                    change.get('Phone', ''),
                    change.get('Ville', ''),
                    change.get('CodeCoupon', ''),
                    change.get('Centre', '')
                ))
                new_ids.append(cursor.lastrowid)

            elif change['action'] == 'update':
                fields = change.get('fields', {})
                if fields:
                    set_clause = []
                    values = []
                    for field, value in fields.items():
                        set_clause.append(f"{field} = %s")
                        values.append(value)
                    values.append(change['id'])

                    query = f"""
                        UPDATE ResponsablePedagogique
                        SET {', '.join(set_clause)}
                        WHERE id = %s
                    """
                    cursor.execute(query, values)

            elif change['action'] == 'delete':
                cursor.execute("""
                    DELETE FROM ResponsablePedagogique
                    WHERE id = %s
                """, (change['id'],))

        conn.commit()
        return jsonify({
            'status': 'success',
            'message': 'Modifications sauvegardées',
            'new_ids': new_ids
        })

    except mysql.connector.Error as err:
        conn.rollback()
        error_msg = f"Database error: {err}"
        print(error_msg)
        return jsonify({
            'status': 'error',
            'message': 'Erreur de base de données',
            'error_details': str(err)
        }), 500

    except Exception as e:
        conn.rollback()
        error_msg = f"General error: {str(e)}"
        print(error_msg)
        return jsonify({
            'status': 'error',
            'message': 'Erreur lors de la sauvegarde',
            'error_details': str(e)
        }), 500

    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()
        
@admin_bp.route('/add-pedagogue', methods=['POST'])
def add_pedagogue():
    if session.get('user_type') != 'Administrateur':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # First check if email already exists (case-insensitive comparison)
        cursor.execute("""
            SELECT id FROM ResponsablePedagogique 
            WHERE LOWER(AdresseEmail) = LOWER(%s)
            LIMIT 1
        """, (data['AdresseEmail'],))
        
        existing_pedagogue = cursor.fetchone()
        print("what is this !!")
        if existing_pedagogue:
            return jsonify({
                'status': 'error',
                'message': 'Cet email est déjà utilisé par un autre responsable',
                'error_code': 'email_taken'
            }), 400
        
        # If email is unique, proceed with insertion
        cursor.execute("""
            INSERT INTO ResponsablePedagogique 
            (Nom, Prenom, AdresseEmail, MotDePasse, Phone, Ville, CodeCoupon, Centre)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            data['Nom'],
            data['Prenom'],
            data['AdresseEmail'],
            data['MotDePasse'],  # Note: You should hash the password before storing
            data['Phone'],
            data['Ville'],
            data['CodeCoupon'],
            data['Centre']
        ))
        
        # Get the ID of the newly created pedagogue
        new_id = cursor.fetchone()[0]
        conn.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Responsable pédagogique ajouté avec succès',
            'pedagogue_id': new_id
        })
        
    except Exception as e:
        conn.rollback()
        return jsonify({
            'status': 'error',
            'message': f"Une erreur s'est produite: {str(e)}"
        }), 500
        
    finally:
        cursor.close()
        conn.close()

@admin_bp.route('/delete-pedagogue/<int:pedagogue_id>', methods=["DELETE"])
def delete_pedagogue(pedagogue_id):
    if session.get('user_type') != 'Administrateur':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ResponsablePedagogique WHERE id = %s", (pedagogue_id,))
        conn.commit()
        return jsonify({'status': 'success'})  # ✅ Retour JSON
    except Exception as e:
        conn.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# Routes pour Responsables de Centre
@admin_bp.route('/admin/save-responsables', methods=['POST'])
def save_responsables():
    if session.get('user_type') != 'Administrateur':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()

        for change in data:
            if change['action'] == 'update':
                field_name = ['Nom','Prenom','AdresseEmail','Phone','Ville','Centre'][change['field']-1]
                cursor.execute(f"""
                    UPDATE Responsable_de_centre_de_coding 
                    SET {field_name} = %s 
                    WHERE id = %s
                """, (change['value'], change['id']))

        conn.commit()
        return jsonify({'status': 'success'})
    
    except Exception as e:
        conn.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@admin_bp.route('/admin/add-responsable', methods=['POST'])
def add_responsable():
    if session.get('user_type') != 'Administrateur':
        return redirect(url_for('auth.login'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        print(request.form)
        data = request.get_json()

        cursor.execute("""
        INSERT INTO Responsable_de_centre_de_coding 
        (Nom, Prenom, AdresseEmail,MotDePasse, Phone, Ville, Centre)
        VALUES (%s, %s, %s, %s, %s, %s)
        """, (
        data.get('Nom'),
        
        data.get('Email'),
        data.get('MotDePasse'),
        data.get('Phone'),
        data.get('Ville'),
        data.get('Centre')
        ))

        
        conn.commit()
        return jsonify({'status': 'success'})
    
    except Exception as e:
        conn.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@admin_bp.route('/admin/delete-responsable/<int:responsable_id>')
def delete_responsable(responsable_id):
    if session.get('user_type') != 'Administrateur':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Responsable_de_centre_de_coding WHERE id = %s", (responsable_id,))
        conn.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        conn.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()



# Routes associées
ALLOWED_FIELDS_APPRENANTS = {
    'Nom', 'Prenom', 'AdresseEmail', 'MotDePasse', 'Phone', 'Ville',
    'TypeDeFormation', 'CodeCoupon', 'DateDebutFormation',
    'DateFinFormation', 'Centre', 'NiveauDeConnaissance'
}

@admin_bp.route('/admin/save-apprenants', methods=['POST'])
def save_apprenants():
    if session.get('user_type') != 'Administrateur':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

    conn = None
    cursor = None
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()

        def parse_date(value):
            return None if value in ['', None] else value

        for change in data:
            action = change.get('action')
            
            if action == 'create':
                fields = change.get('fields', {})
                
                # Handle password hashing for new apprenants
                if 'MotDePasse' in fields and fields['MotDePasse']:
                    if not is_hashed(fields['MotDePasse']):
                        fields['MotDePasse'] = hash_password(fields['MotDePasse'])
                
                cursor.execute("""
                    INSERT INTO Apprenants (
                        Nom, Prenom, AdresseEmail, MotDePasse, Phone, Ville,
                        TypeDeFormation, CodeCoupon, DateDebutFormation,
                        DateFinFormation, Centre, NiveauDeConnaissance
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    fields.get('Nom'),
                    fields.get('Prenom'),
                    fields.get('AdresseEmail'),
                    fields.get('MotDePasse'),
                    fields.get('Phone'),
                    fields.get('Ville'),
                    fields.get('TypeDeFormation'),
                    fields.get('CodeCoupon') or None,
                    parse_date(fields.get('DateDebutFormation')),
                    parse_date(fields.get('DateFinFormation')),
                    fields.get('Centre'),
                    fields.get('NiveauDeConnaissance')
                ))

            elif action == 'update':
                fields = change.get('fields', {})
                set_clause = []
                values = []
                
                # Handle password hashing for updates
                if 'MotDePasse' in fields and fields['MotDePasse']:
                    if not is_hashed(fields['MotDePasse']):
                        fields['MotDePasse'] = hash_password(fields['MotDePasse'])
                
                for field, value in fields.items():
                    if field == 'DateDebutFormation' or field == 'DateFinFormation':
                        value = parse_date(value)
                    if field == 'CodeCoupon' and value == '':
                        value = None
                    
                    set_clause.append(f"`{field}` = %s")
                    values.append(value)
                
                values.append(change.get('id'))
                
                cursor.execute(f"""
                    UPDATE Apprenants 
                    SET {', '.join(set_clause)}
                    WHERE id = %s
                """, values)

            elif action == 'delete':
                apprenant_id = change.get('id')
                cursor.execute("DELETE FROM Presence WHERE apprenant_id = %s", (apprenant_id,))
                cursor.execute("DELETE FROM PresenceCentre WHERE apprenant_id = %s", (apprenant_id,))
                cursor.execute("DELETE FROM Apprenants WHERE id = %s", (apprenant_id,))

        conn.commit()
        return jsonify({
            'status': 'success',
            'message': f'{len(data)} modifications sauvegardées avec succès'
        })

    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Erreur de base de données: {err.msg}',
            'code': err.errno
        }), 500

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Erreur inattendue: {str(e)}'
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@admin_bp.route('/admin/add-apprenant', methods=['POST'])
def add_apprenant():
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO Apprenants (
                Nom, Prenom, AdresseEmail, MotDePasse, Phone, Ville,
                TypeDeFormation, CodeCoupon, DateDebutFormation,
                DateFinFormation, Centre, NiveauDeConnaissance
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data['Nom'], data['Prenom'], data['AdresseEmail'],
            data['MotDePasse'], data['Phone'], data['Ville'],
            data['TypeDeFormation'], data['CodeCoupon'],
            data['DateDebutFormation'], data['DateFinFormation'],
            data['Centre'], data['NiveauDeConnaissance']
        ))
        
        conn.commit()
        return jsonify({'status': 'success'})
    
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()
@admin_bp.route('/admin/delete-apprenant/<int:apprenant_id>', methods=['DELETE'])
def delete_apprenant(apprenant_id):
    if session.get('user_type') != 'Administrateur':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM Apprenants WHERE id = %s", (apprenant_id,))
        conn.commit()
        return jsonify({'status': 'success'})

    except Exception as e:
        conn.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

    finally:
        cursor.close()
        conn.close()



@admin_bp.route('/admin/update-passwords', methods=['POST'])
def update_passwords():
    if session.get('user_type') != 'Administrateur':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

    conn = None
    cursor = None
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()

        for change in data:
            apprenant_id = change.get('id')
            new_password = change.get('fields', {}).get('MotDePasse', '')
            
            if new_password:
                # Vérifier si le mot de passe est déjà hashé
                if not is_hashed(new_password):
                    hashed_password = hash_password(new_password)
                    cursor.execute(
                        "UPDATE Apprenants SET MotDePasse = %s WHERE id = %s",
                        (hashed_password, apprenant_id)
                    )

        conn.commit()
        return jsonify({
            'status': 'success',
            'message': f'{len(data)} mots de passe mis à jour avec succès'
        })

    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Erreur de base de données: {err.msg}',
            'code': err.errno
        }), 500

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Erreur inattendue: {str(e)}'
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

ALLOWED_FIELDS = {'Nom', 'Prenom', 'AdresseEmail', 'MotDePasse', 'Phone', 'Ville', 'CodeCoupon', 'Centre'}

@admin_bp.route('/save-centres', methods=['POST'])
def save_centres():
    if session.get('user_type') != 'Administrateur':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()

        for change in data:
            print("Processing change:", change)

            if change['action'] == 'update':
                # Correction ici : on boucle sur change['fields']
                for field_name, field_value in change.get("fields", {}).items():
                    if field_name not in ALLOWED_FIELDS:
                        print(f"Champ non autorisé ignoré: {field_name}")
                        continue

                    query = f"""
                        UPDATE Responsable_de_centre_de_coding
                        SET {field_name} = %s
                        WHERE id = %s
                    """
                    cursor.execute(query, (field_value, change['id']))

            elif change['action'] == 'create':
                new_data = change.get('data', {})
                
                query = """
                    INSERT INTO Responsable_de_centre_de_coding
                    (Nom, Prenom, AdresseEmail, MotDePasse, Phone, Ville, CodeCoupon, Centre)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                values = (
                    new_data.get('Nom', ''),
                    new_data.get('Prenom', ''),
                    new_data.get('AdresseEmail', ''),
                    new_data.get('MotDePasse', ''),
                    new_data.get('Phone', ''),
                    new_data.get('Ville', ''),
                    new_data.get('CodeCoupon', ''),
                    new_data.get('Centre', '')
                )
                cursor.execute(query, values)

            elif change['action'] == 'delete':
                cursor.execute("DELETE FROM Responsable_de_centre_de_coding WHERE id = %s", (change['id'],))

        conn.commit()
        return jsonify({'status': 'success'})

    except Exception as e:
        print("Erreur lors de la sauvegarde:", str(e))
        conn.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

    finally:
        cursor.close()
        conn.close()

@admin_bp.route('/admin/update-responsable-passwords', methods=['POST'])
def update_responsable_passwords():
    if session.get('user_type') != 'Administrateur':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

    conn = None
    cursor = None
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()

        for change in data:
            responsable_id = change.get('id')
            new_password = change.get('fields', {}).get('MotDePasse', '')
            
            if new_password:
                # Vérifier si le mot de passe est déjà hashé
                if not is_hashed(new_password):
                    hashed_password = hash_password(new_password)
                    cursor.execute(
                        "UPDATE Responsable_de_centre_de_coding SET MotDePasse = %s WHERE id = %s",
                        (hashed_password, responsable_id)
                    )

        conn.commit()
        return jsonify({
            'status': 'success',
            'message': f'{len(data)} mots de passe mis à jour avec succès'
        })

    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Erreur de base de données: {err.msg}',
            'code': err.errno
        }), 500

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Erreur inattendue: {str(e)}'
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
@admin_bp.route('/admin/add-user', methods=['POST'])
def admin_add_user():
    if session.get('user_type') != 'Administrateur':
        return redirect(url_for('auth.login'))
    
    user_type = request.form.get('user_type')
    # Récupérez les autres champs du formulaire
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if user_type == "Apprenants":
            cursor.execute('INSERT INTO Apprenants (...) VALUES (...)')
        elif user_type == "ResponsablePedagogique":
            cursor.execute('INSERT INTO ResponsablePedagogique (...) VALUES (...)')
        elif user_type == "Responsable_de_centre_de_coding":
            cursor.execute('INSERT INTO Responsable_de_centre_de_coding (...) VALUES (...)')
            
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for(f'admin_{user_type.lower()}'))
    except Exception as e:
        print(f"Erreur lors de l'ajout: {str(e)}")
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()
        return redirect(url_for('dashboard'))

@admin_bp.route('/admin/delete-user/<user_type>/<int:user_id>')
def admin_delete_user(user_type, user_id):
    if session.get('user_type') != 'Administrateur':
        return redirect(url_for('auth.login'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if user_type == "Apprenants":
            cursor.execute('DELETE FROM Apprenants WHERE id = %s', (user_id,))
        elif user_type == "ResponsablePedagogique":
            cursor.execute('DELETE FROM ResponsablePedagogique WHERE id = %s', (user_id,))
        elif user_type == "Responsable_de_centre_de_coding":
            cursor.execute('DELETE FROM Responsable_de_centre_de_coding WHERE id = %s', (user_id,))
            
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for(f'admin_{user_type.lower()}'))
    except Exception as e:
        print(f"Erreur lors de la suppression: {str(e)}")
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()
        return redirect(url_for('dashboard'))    

@admin_bp.route('/admin/apprenants/<int:apprenant_id>', methods=['PATCH', 'DELETE'])
def handle_apprenant(apprenant_id):
    if session.get('user_type') != 'Administrateur':
        return jsonify({'error': 'Unauthorized'}), 403
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if request.method == 'PATCH':
            data = request.json
            field = data['field']
            value = data['value']
            
            # Validation des champs modifiables
            allowed_fields = {
                'Nom', 'Prenom', 'AdresseEmail', 'MotDePasse',
                'Phone', 'Ville', 'TypeDeFormation', 'CodeCoupon',
                'DateDebutFormation', 'DateFinFormation', 'Centre',
                'NiveauDeConnaissance'
            }
            
            if field not in allowed_fields:
                return jsonify({'error': 'Champ non autorisé'}), 400

            cursor.execute(f"""
                UPDATE Apprenants 
                SET {field} = %s 
                WHERE id = %s
            """, (value, apprenant_id))
            
            conn.commit()
            return jsonify({'status': 'success'})
            
        elif request.method == 'DELETE':
            cursor.execute("DELETE FROM Apprenants WHERE id = %s", (apprenant_id,))
            conn.commit()
            return jsonify({'status': 'success'})
            
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@admin_bp.route('/admin-apprenants')
def admin_apprenants():
    if 'user_type' not in session or session.get('user_type') != 'Administrateur':
        return redirect(url_for('auth.login'))

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                id,
                Nom,
                Prenom,
                AdresseEmail,
                MotDePasse,
                Phone,
                Ville,
                TypeDeFormation,
                COALESCE(CodeCoupon, '') AS CodeCoupon,
                DATE_FORMAT(DateDebutFormation, '%Y-%m-%d') AS DateDebutFormation,
                DATE_FORMAT(DateFinFormation, '%Y-%m-%d') AS DateFinFormation,
                Centre,
                NiveauDeConnaissance
            FROM Apprenants
            ORDER BY id ASC
        """)

        apprenants = cursor.fetchall()

        return render_template(
            'admin_apprenants.html',
            apprenants=apprenants
        )

    except mysql.connector.Error as err:
        print(f"Erreur MySQL: {err}")
        return render_template('admin_apprenants.html',
                                   apprenants=[],
                                   error="Erreur de base de données")

    except Exception as e:
        print(f"Erreur générale: {str(e)}")
        return render_template('admin_apprenants.html',
                                   apprenants=[],
                                   error="Erreur inattendue")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
 # Passage correct de la variable



    
@admin_bp.route('/admin-centres', endpoint='admin_centres_unique')
def admin_centres():
    if session.get('user_type') != 'Administrateur':
        return redirect(url_for('auth.login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Modification ici : Ajout de MotDePasse dans la requête
        cursor.execute("""
            SELECT id, Nom, Prenom, AdresseEmail, MotDePasse,
                   Phone, Ville, CodeCoupon, Centre 
            FROM Responsable_de_centre_de_coding
        """)
        responsables = cursor.fetchall()
        return render_template('admin_centre.html', responsables=responsables)
    
    except Exception as e:
        print(f"Erreur base de données : {str(e)}")
        return render_template('admin_centre.html', responsables=[])
    
    finally:
        cursor.close()
        conn.close()




@admin_bp.route('/get-apprenants')
def get_apprenants():
    if session.get('user_type') != 'Administrateur':
        return jsonify([])
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT id, Nom, Prenom, AdresseEmail, MotDePasse, Phone, Ville,
                   TypeDeFormation, CodeCoupon, 
                   DATE_FORMAT(DateDebutFormation, '%%Y-%%m-%%d') as DateDebutFormation,
                   DATE_FORMAT(DateFinFormation, '%%Y-%%m-%%d') as DateFinFormation,
                   Centre, NiveauDeConnaissance
            FROM Apprenants
        """)
        return jsonify(cursor.fetchall())
    except Exception as e:
        return jsonify([])
    finally:
        cursor.close()
        conn.close()

@admin_bp.route('/get-pedagogues')
def get_pedagogues():
    if session.get('user_type') != 'Administrateur':
        return jsonify([])
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM ResponsablePedagogique")
    pedagogues = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return jsonify(pedagogues)
@admin_bp.route('/get-centres')
def get_centres():
    if session.get('user_type') != 'Administrateur':
        return jsonify([])
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Responsable_de_centre_de_coding")
    responsables = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return jsonify(responsables)




@admin_bp.route('/rapports')
def rapports():
    return render_template('rapports.html', url_for=url_for)    
