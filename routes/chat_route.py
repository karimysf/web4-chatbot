from flask import Blueprint, render_template, request, redirect, url_for,  session, jsonify,flash
from utils.db import get_db_connection
import uuid
from utils.ai import rag_chat
chatbot_bp=Blueprint('chatbot', __name__)

@chatbot_bp.route("/chatbot")
def chatbot():
    return render_template('chatbot.html', url_for=url_for)


@chatbot_bp.route("/chat", methods=["POST"])
def chat():
    question = request.json.get("question", "")
    response = rag_chat(question)

    user_id = session.get('user_id')

    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())

    session_id = session["session_id"]

    # Enregistrement dans la base
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO historique (user_id, message, response, session_id)
        VALUES (%s, %s, %s, %s)
    """, (user_id, question, response, session_id))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"response": response})

@chatbot_bp.route("/new-chat", methods=["POST"])
def new_chat():
    session.pop("session_id", None)
    return jsonify({"status": "new session started"})


@chatbot_bp.route('/get-history')
def get_history():
    user_id = session.get('user_id')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Récupérer tous les messages du user, groupés par session
    cursor.execute("""
        SELECT session_id, message, response, created_at
        FROM historique
        WHERE user_id = %s
        ORDER BY session_id, created_at
    """, (user_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    # Regrouper par session_id comme des "conversations"
    grouped = {}
    for row in rows:
        sid = row['session_id']
        if sid not in grouped:
            grouped[sid] = {
                "session_id": sid,
                "created_at": row['created_at'],
                "conversations": []
            }
        grouped[sid]["conversations"].append({
            "message": row["message"],
            "response": row["response"]
        })

    # Convertir en liste triée (comme GPT)
    history = sorted(grouped.values(), key=lambda x: x["created_at"], reverse=True)
    return jsonify(history)



@chatbot_bp.route('/delete-conversation/<int:conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM historique
        WHERE id = %s
    """, (conversation_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"status": "success"})

@chatbot_bp.route('/delete-all-conversations', methods=['DELETE'])
def delete_all_conversations():
    user_id = session.get('user_id')  # Assurez-vous que l'utilisateur est connecté
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM historique
        WHERE user_id = %s
    """, (user_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"status": "success"})


@chatbot_bp.route('/messagerie/supprimer', methods=['POST'])
def supprimer_conversation():
    if 'email' not in session:
        return jsonify({'success': False, 'message': 'Non autorisé'}), 401

    user_email = session['email']
    correspondant = request.json.get('correspondant')

    if not correspondant:
        return jsonify({'success': False, 'message': 'Correspondant manquant'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Suppression réelle des messages entre les deux
        cursor.execute('''
            DELETE FROM Messages
            WHERE (expediteur_email = %s AND destinataire_email = %s)
               OR (expediteur_email = %s AND destinataire_email = %s)
        ''', (user_email, correspondant, correspondant, user_email))

        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# Routes pour la messagerie
@chatbot_bp.route('/messagerie')
def messagerie():
    if 'email' not in session:
        return redirect(url_for('auth.login'))

    user_email = session['email']
    user_role = session['user_type']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Récupérer les conversations
    cursor.execute('''
        SELECT DISTINCT
            CASE
                WHEN expediteur_email = %s THEN destinataire_email
                ELSE expediteur_email
            END AS correspondant,
            MAX(date_envoi) AS dernier_message
        FROM Messages
        WHERE (expediteur_email = %s OR destinataire_email = %s)
        AND (expediteur_supprime = FALSE OR destinataire_supprime = FALSE)
        GROUP BY correspondant
        ORDER BY dernier_message DESC
    ''', (user_email, user_email, user_email))

    conversations = cursor.fetchall()

    # Marquer les messages non lus
    unread_count = {}
    for conv in conversations:
        cursor.execute('''
            SELECT COUNT(*) AS count
            FROM Messages
            WHERE destinataire_email = %s
            AND expediteur_email = %s
            AND lu = FALSE
        ''', (user_email, conv['correspondant']))
        unread_count[conv['correspondant']] = cursor.fetchone()['count']

    cursor.close()
    conn.close()

    return render_template('messagerie.html',
                                conversations=conversations,
                                unread_count=unread_count)


# Dans la route /messagerie/envoyer
@chatbot_bp.route('/messagerie/envoyer', methods=['GET', 'POST'])
def envoyer_message():
    if 'email' not in session:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        destinataire = request.form['destinataire']
        sujet = request.form.get('sujet', '')  # Modification ici
        contenu = request.form['contenu']
        

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            # Vérification du destinataire
            cursor.execute('''
                (SELECT 'Apprenant' AS role FROM Apprenants WHERE AdresseEmail = %s LIMIT 1)
                UNION
                (SELECT 'ResponsablePedagogique' FROM ResponsablePedagogique WHERE AdresseEmail = %s LIMIT 1)
                UNION
                (SELECT 'ResponsableCentre' FROM Responsable_de_centre_de_coding WHERE AdresseEmail = %s LIMIT 1)
            ''', (destinataire, destinataire, destinataire))
          
            result = cursor.fetchone()
            if not result:

                flash('Destinataire introuvable', 'error')
                print("Desintataire non introuvable")
                return  jsonify({"Destinatire non trouve"}),400
          
            destinataire_role = result[0]
          
            # Détermination du rôle expéditeur
            role_mapping = {
                'Apprenants': 'Apprenant',
                'ResponsablePedagogique': 'ResponsablePedagogique',
                'Responsable_de_centre_de_coding': 'ResponsableCentre'
            }
            expediteur_role = role_mapping.get(session['user_type'])
           
            # Insertion avec gestion du sujet NULL
            cursor.execute('''
                INSERT INTO Messages
                (expediteur_email, expediteur_role, destinataire_email, destinataire_role, sujet, contenu)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (
                session['email'],
                expediteur_role,
                destinataire,
                destinataire_role,
                sujet if sujet else None,  # Insertion NULL si sujet vide
                contenu
            ))
            conn.commit()
            flash('Message envoyé avec succès', 'success')

        except Exception as e:
            conn.rollback()
            flash(f"Erreur lors de l'envoi: {str(e)}", 'error')
        
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('chatbot.messagerie'))

    return render_template('envoyer_message.html')




@chatbot_bp.route('/messagerie/<correspondant>')
def conversation(correspondant):
    if 'email' not in session:
        return redirect(url_for('auth.login'))

    user_email = session['email']
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Marquer les messages comme lus
    cursor.execute('''
        UPDATE Messages 
        SET lu = TRUE 
        WHERE destinataire_email = %s 
        AND expediteur_email = %s
    ''', (user_email, correspondant))
    conn.commit()
    
    # Récupérer la conversation
    cursor.execute('''
        SELECT * FROM Messages 
        WHERE (expediteur_email = %s AND destinataire_email = %s)
        OR (expediteur_email = %s AND destinataire_email = %s)
        ORDER BY date_envoi ASC
    ''', (user_email, correspondant, correspondant, user_email))
    
    messages = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('conversation.html', 
                                messages=messages,
                                correspondant=correspondant)

@chatbot_bp.route('/check-messages')
def check_messages():
    if 'email' not in session:
        return jsonify(count=0)

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT COUNT(*) FROM Messages
        WHERE destinataire_email = %s
        AND lu = FALSE
        AND destinataire_supprime = FALSE
    ''', (session['email'],))

    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()

    return jsonify(count=count)


@chatbot_bp.route('/delete-session/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    user_id = session.get('user_id')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM historique
        WHERE user_id = %s AND session_id = %s
    """, (user_id, session_id))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"status": "success"})


@chatbot_bp.route('/get-questions-data')
def get_questions_data():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Récupérer le nombre total de questions
    cursor.execute("SELECT COUNT(*) as total_questions FROM historique")
    total_questions = cursor.fetchone()['total_questions']

    # Récupérer le nombre moyen de questions par jour
    cursor.execute("""
        SELECT AVG(question_count) as avg_questions_per_day
        FROM (
            SELECT COUNT(*) as question_count
            FROM historique
            GROUP BY DATE(created_at)
        ) as daily_counts
    """)
    avg_questions_per_day = cursor.fetchone()['avg_questions_per_day']

    # Récupérer les questions fréquentes
    cursor.execute("""
        SELECT message, COUNT(*) as count
        FROM historique
        GROUP BY message
        ORDER BY count DESC
        LIMIT 5
    """)
    frequent_questions = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify({
        "total_questions": total_questions,
        "avg_questions_per_day": avg_questions_per_day,
        "frequent_questions": frequent_questions
    })


