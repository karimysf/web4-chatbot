from flask import Blueprint,jsonify,session,render_template,redirect,url_for

from utils.db import get_db_connection
respo_bp=Blueprint('respo',__name__)


# Responsable de centre de coding
@respo_bp.route('/Responsable_de_centre_de_coding-knowledge-base')
def responsable_centre_knowledge_base():
    if session.get('user_type') == 'Responsable_de_centre_de_coding':
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM BaseConnaissances")
        files = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('admin_knowledge.html', files=files)
    return redirect(url_for('auth.login'))


@respo_bp.route('/api/delete-knowledge/<int:file_id>', methods=['DELETE'])
def delete_knowledge_file(file_id):
    if session.get('user_type') != 'Responsable_de_centre_de_coding':
        return jsonify({'error': 'Non autorisé'}), 403

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM BaseConnaissances WHERE id = %s", (file_id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({'error': 'Fichier introuvable'}), 404

    try:
        cursor.execute("DELETE FROM BaseConnaissances WHERE id = %s", (file_id,))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@respo_bp.route('/Responsable_de_centre_de_coding-tutorials')
def responsable_centre_tutorials():
    if session.get('user_type') == 'Responsable_de_centre_de_coding':
        return render_template('admin_tuto.html')
    return redirect(url_for('auth.login'))


@respo_bp.route('/centre-apprenants')
def centre_apprenants():
    if session.get('user_type') != 'Responsable_de_centre_de_coding':
        return redirect(url_for('auth.login'))
    
    centre = session.get('centre')
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT pc.*, a.NiveauDeConnaissance, a.TypeDeFormation
            FROM PresenceCentre pc
            JOIN Apprenants a ON pc.apprenant_id = a.id
            WHERE pc.Centre = %s
            ORDER BY pc.heure_connexion DESC
        """, (centre,))
        
        presences = cursor.fetchall()
        return render_template('centre_apprenants.html', presences=presences)
    except Exception as e:
        print(f"Erreur présence centre : {str(e)}")
        return render_template('centre_apprenants.html', presences=[])
    finally:
        cursor.close()
        conn.close()

@respo_bp.route('/api/delete-parcours/<int:parcours_id>', methods=['DELETE'])
def delete_parcours(parcours_id):
    if session.get('user_type') != 'Responsable_de_centre_de_coding':
        return jsonify({'error': 'Non autorisé'}), 403

    centre = session.get('centre')
    conn = get_db_connection()
    cursor = conn.cursor()

    # Vérifier si le parcours appartient à ce centre
    cursor.execute("SELECT id FROM Parcours WHERE id = %s AND centre = %s", (parcours_id, centre))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({'error': 'Parcours non trouvé'}), 404

    try:
        cursor.execute("DELETE FROM Parcours WHERE id = %s", (parcours_id,))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()