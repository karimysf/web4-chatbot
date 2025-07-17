

from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session, jsonify, flash
import mysql.connector
import os
from datetime import datetime
from io import BytesIO
import pandas as pd
from flask import send_file
import re
from werkzeug.utils import secure_filename
import io
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
import requests
from bs4 import BeautifulSoup
import uuid
from dotenv import load_dotenv

#Definition des Constantes ENV
load_dotenv()
DB_USERNAME=os.getenv('DB_USERNAME')
DB_HOST=os.getenv('DB_HOST')
DB_PASSWORD=os.getenv('DB_PASSWORD')
DB_NAME=os.getenv('DB_NAME')
DB_PORT=os.getenv('DB_PORT')
APP_SECRET_KEY=os.getenv('APP_SECRET_KEY')
UPLOAD_FOLDER=os.getenv('UPLOAD_FOLDER')
GROQ_API_KEY=os.getenv('GROQ_API_KEY')



app = Flask(__name__)
#utiliser un env au lieu de le taper la 
app.secret_key = APP_SECRET_KEY



#utilise un env pour les mot de pass et username 
def get_db_connection():
    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USERNAME,
        port=DB_PORT,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    return conn
print(DB_HOST)

# Ajoutez cette fonction après la création de l'application Flask
def urlize(text, max_length=None):
    import re
    url_pattern = re.compile(r'(https?://\S+)')
    # Remplacer les URLs par des liens HTML
    result = re.sub(url_pattern, r'<a href="\1" target="_blank">\1</a>', text)
    # Tronquer le texte si nécessaire
    if max_length:
        result = result[:max_length] + '...' if len(result) > max_length else result
    return result

app.jinja_env.filters['urlize'] = urlize

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'json'}


if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)



# Fonction appel API Groq
def call_groq_mixtral(prompt):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama3-8b-8192",  # modèle stable sur Groq
        "messages": [
            {"role": "system", "content": "Tu es un assistant pédagogique intelligent."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 500
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        print("Erreur API Groq :", e)
        if 'response' in locals():
            print("Contenu de la réponse :", response.text)
        return "❌ Erreur avec le modèle IA."



# Fonction RAG complète dans une seule fonction
def rag_chat(question):
    try:
        documents = get_documents()
        if not documents:
            return "Aucun document trouvé dans la base de connaissances."

        langchain_docs = [
            Document(page_content=doc["description"], metadata={"titre": doc["titre"], "lien_web": doc.get("lien_web")})
            for doc in documents
        ]

        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        vectordb = Chroma.from_documents(langchain_docs, embeddings)
        retriever = vectordb.as_retriever()

        docs = retriever.invoke(question)
        context = "\n".join([doc.page_content for doc in docs[:3]])

        prompt = f"""Voici un contexte extrait d'une base de connaissances :
{context}

Question : {question}
Réponds en 4 phrases max de maniere claire , humain ,  sympa précise et pédagogique."""
        return call_groq_mixtral(prompt)

    except Exception as e:
        print("Erreur RAG :", e)
        return "Une erreur est survenue dans le traitement."



def get_documents():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT titre, description, lien_web FROM BaseConnaissances")
    documents = cursor.fetchall()
    cursor.close()
    conn.close()

    processed_documents = []
    for doc in documents:
        if doc['lien_web']:
            web_content = process_web_content(doc['lien_web'])
            if web_content:
                doc['description'] += f" Contenu du lien web: {web_content}"
        processed_documents.append(doc)

    return processed_documents


def fetch_web_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Vérifie si la requête a réussi
        soup = BeautifulSoup(response.text, 'html.parser')

        # Supprime les scripts et les styles
        for script in soup(["script", "style"]):
            script.decompose()

        # Récupère le texte
        text = soup.get_text(separator=' ', strip=True)
        return text
    except Exception as e:
        print(f"Erreur lors de la récupération du contenu de {url}: {e}")
        return None

def process_web_content(url):
    content = fetch_web_content(url)
    if content:
        # Assurez-vous que le contenu est valide en UTF-8
        try:
            content = content.encode('utf-8', errors='replace').decode('utf-8')
        except UnicodeEncodeError as e:
            print(f"Erreur d'encodage : {e}")
            return None
        return content
    return None




ADMIN_COURSES_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Listes des parcours de formation- Administrateur</title>
    <style>
        body {
            font-family: 'Arial', sans-serif;
            background-color: #f4f4f4;
            display: flex;
        }
        .sidebar {
            width: 260px;
            height: 100vh;
            background-color: #2c2c6c;
            color: white;
            display: flex;
            flex-direction: column;
            position: fixed;
            left: 0;
            top: 0;
            box-shadow: 2px 0 6px rgba(0,0,0,0.1);
            transition: width 0.3s;
        }
        .sidebar.collapsed {
            width: 0;
            overflow: hidden;
        }
        .sidebar .logo {
            padding: 20px;
            text-align: center;
        }
        .sidebar .logo img {
            width: 100px;
        }
        .sidebar .menu {
            flex: 1;
        }
        .sidebar .menu a {
            padding: 15px 20px;
            text-decoration: none;
            color: white;
            transition: background-color 0.2s;
            font-size: 14px;
            display: flex;
            align-items: center;
        }
        .sidebar .menu a:hover {
            background-color: #4a4a99;
        }
        .sidebar .menu a .icon {
            margin-right: 10px;
        }
        .main-content {
            margin-left: 260px;
            padding: 30px;
            flex: 1;
            transition: margin-left 0.3s;
        }
        .main-content.expanded {
            margin-left: 0;
        }
        .menu-toggle {
            position: fixed;
            top: 20px;
            left: 20px;
            background: #8052e6;
            color: white;
            border: none;
            padding: 10px;
            border-radius: 4px;
            cursor: pointer;
            z-index: 1000;
        }
        .menu-toggle:hover {
            background: #6a40d0;
        }
        .knowledge-base-container {
            background-color: white;
            border-radius: 10px;
            padding: 25px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .knowledge-base-header {
            margin-bottom: 25px;
        }
        .knowledge-base-header h2 {
            color: #8052e6;
            margin-top: 0;
        }
        .search-container {
            display: flex;
            margin-bottom: 20px;
            gap: 10px;
        }
        .search-container input {
            flex: 1;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }
        .search-container button {
            padding: 12px 20px;
            background-color: #8052e6;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }
        .search-container button:hover {
            background-color: #6a40d0;
        }
        .action-buttons {
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
        }
        .action-button {
            padding: 12px 20px;
            background-color: #8052e6;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            display: flex;
            align-items: center;
            transition: all 0.3s ease;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }
        .action-button:hover {
            background-color: #6a40d0;
            transform: translateY(-2px);
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.3);
        }
        .action-button:active {
            transform: translateY(0);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }
        .delete-button {
            padding: 12px 20px;
            background-color: #e74c3c;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            display: flex;
            align-items: center;
            transition: all 0.3s ease;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }
        .delete-button:hover {
            background-color: #c0392b;
            transform: translateY(-2px);
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.3);
        }
        .delete-button:active {
            transform: translateY(0);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }
        .button-icon {
            margin-right: 8px;
            font-size: 16px;
        }
        .visualize-button {
            padding: 12px 20px;
            background-color: #28a745;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            display: flex;
            align-items: center;
            transition: all 0.3s ease;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }
        .visualize-button:hover {
            background-color: #218838;
            transform: translateY(-2px);
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.3);
        }
        .visualize-button:active {
            transform: translateY(0);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }
    </style>
</head>
<body>
    <button id="menu-toggle" class="menu-toggle">☰</button>
    <div class="sidebar">
        <div class="logo">
            <img src="/static/PROFIL.png" alt="Web4.Jobs Logo">
        </div>
         <div class="menu">
            <a href="/dashboard"><span class="icon">🏠</span> Accueil</a>
           
            
            <a href="/centre-courses"><span class="icon">📊</span> Listes des parcours de formation</a>
            <a href="/Responsable_de_centre_de_coding-knowledge-base"><span class="icon">📚</span> Base de connaissances</a>
            <a href="/chatbot"><span class="icon">🤖</span> Chatbot</a>
            <a href="/messagerie">
    <a href="/messagerie">
    <span class="icon">💬</span> Messagerie
    <span id="notification-badge" style="display: none;" class="unread-count">3</span>
</a>

<style>
    .unread-count {
        background-color: red;
        color: white;
        border-radius: 50%;
        padding: 2px 6px;
        font-size: 12px;
        margin-left: 6px;
        display: inline-block;
        min-width: 18px;
        text-align: center;
    }
</style>

            <a href="/centre-apprenants"><span class="icon">👥</span> Apprenants</a>

            <a href="/rapports"><span class="icon">📈</span> Rapports</a>

            <a href="/logout"><span class="icon">🔓</span> Déconnexion</a>
        </div>
    </div>

    <div class="main-content">
        <div class="knowledge-base-container">
            <div class="knowledge-base-header">
                <h2>Listes des parcours de formation</h2>
            </div>

            <div class="search-container">
                <input type="text" placeholder="Rechercher dans listes des parcours de formation...">
                <button>Rechercher</button>
            </div>

            <div class="action-buttons">
                <button class="action-button"><span class="button-icon">+</span> Ajouter</button>
                <button class="delete-button"><span class="button-icon"></span> Supprimer</button>
                <button class="visualize-button"><span class="button-icon"></span> Visualiser</button>
            </div>
        </div>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const menuToggle = document.getElementById('menu-toggle');
            const sidebar = document.querySelector('.sidebar');
            const mainContent = document.querySelector('.main-content');

            menuToggle.addEventListener('click', function() {
                sidebar.classList.toggle('collapsed');
                mainContent.classList.toggle('expanded');
            });

            // Fonctionnalité de recherche
            const searchButton = document.querySelector('.search-container button');
            const searchInput = document.querySelector('.search-container input');

            searchButton.addEventListener('click', function() {
                const query = searchInput.value;
                if (query) {
                    // Implémentez ici la logique de recherche
                    console.log('Recherche:', query);
                }
            });

            // Permettre la recherche avec la touche Entrée
            searchInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    searchButton.click();
                }
            });
        });
        <script>
    // Notification auto-refresh
    function checkMessages() {
        fetch('/check-messages')
            .then(response => response.json())
            .then(data => {
                console.log("Nombre de messages non lus:", data.count);  // Log pour vérifier le nombre de messages non lus
                const badge = document.getElementById('notification-badge');
                if (data.count > 0) {
                    badge.textContent = data.count;
                    badge.style.display = 'inline-block';
                } else {
                    badge.style.display = 'none';
                }
            })
            .catch(error => {
                console.error("Erreur lors de la vérification des messages:", error);  // Log pour vérifier les erreurs
            });
    }
    setInterval(checkMessages, 30000);
    checkMessages(); // Initial check
</script>

    </script>
</body>
</html>"""


@app.route('/admin-dashboard')
def admin_dashboard():
    return render_template('admin_rapports.html', url_for=url_for)

@app.route('/get-admin-data')
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






@app.route('/rapports')
def rapports():
    return render_template('rapports.html', url_for=url_for)    



@app.route('/get-questions-data')
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







def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



@app.route('/upload', methods=['POST'])
def upload_file():
    titre = request.form.get('titre')
    description = request.form.get('description')
    fichier = request.files.get('fichier')
    lien_web = request.form.get('lien_web')

    if not titre or not description:
        return 'Le titre et la description sont requis', 400

    fichier_data = b''  # Valeur par défaut pour fichier_data
    type_fichier = 'none'  # Valeur par défaut pour type_fichier

    if fichier and fichier.filename != '':
        filename = fichier.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        fichier.save(filepath)

        with open(filepath, 'rb') as f:
            fichier_data = f.read()
        type_fichier = filename.rsplit('.', 1)[1].lower()

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO BaseConnaissances (titre, description, fichier, type_fichier, lien_web)
            VALUES (%s, %s, %s, %s, %s)
        """, (titre, description, fichier_data, type_fichier, lien_web))
        conn.commit()
    except mysql.connector.Error as err:
        print(f"Erreur MySQL: {err}")
        return f"Erreur de base de données: {err}", 500
    finally:
        cursor.close()
        conn.close()

    return 'Fichier ou lien téléchargé avec succès', 200


@app.route('/delete-session/<session_id>', methods=['DELETE'])
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

@app.route("/chatbot")
def chatbot():
    return render_template('chatbot.html', url_for=url_for)


@app.route("/chat", methods=["POST"])
def chat():
    question = request.json.get("question", "")
    response = rag_chat(question)

    user_id = session.get('user_id')

    # Gérer l'identifiant de session : nouveau ou existant
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

@app.route("/new-chat", methods=["POST"])
def new_chat():
    session.pop("session_id", None)
    return jsonify({"status": "new session started"})


@app.route('/get-history')
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



@app.route('/delete-conversation/<int:conversation_id>', methods=['DELETE'])
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

@app.route('/delete-all-conversations', methods=['DELETE'])
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


@app.route('/messagerie/supprimer', methods=['POST'])
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
@app.route('/messagerie')
def messagerie():
    if 'email' not in session:
        return redirect(url_for('login'))

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
@app.route('/messagerie/envoyer', methods=['GET', 'POST'])
def envoyer_message():
    if 'email' not in session:
        return redirect(url_for('login'))

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
                return redirect(url_for('envoyer_message'))
          
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

        return redirect(url_for('messagerie'))

    return render_template('envoyer_message.html')



@app.route('/messagerie/<correspondant>')
def conversation(correspondant):
    if 'email' not in session:
        return redirect(url_for('login'))

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

@app.route('/check-messages')
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



def extract_youtube_id(url):
    if not url:
        return None
    pattern = r'(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=))([^?&]+)'
    match = re.search(pattern, url)
    return match.group(1) if match else None


@app.route('/centre-courses', methods=['GET', 'POST'])
def centre_courses():
    if session.get('user_type') != 'Responsable_de_centre_de_coding':
        return redirect(url_for('login'))

    centre = session.get('centre')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        email = request.form.get('email')
        intitule = request.form.get('intitule')
        description = request.form.get('description')
        objectifs = request.form.get('objectifs')
        video_url = request.form.get('video_url')
        date_debut = request.form.get('date_debut')
        date_fin = request.form.get('date_fin')
        centre = request.form.get('centre')

        # Vérification que l'apprenant existe dans le même centre
        cursor.execute("""
            SELECT id FROM Apprenants
            WHERE AdresseEmail = %s AND Centre = %s
        """, (email, centre))

        if not cursor.fetchone():
            flash("L'apprenant n'existe pas dans votre centre", 'error')
            return redirect(url_for('centre_courses'))

        video_id = extract_youtube_id(video_url)
        if not video_id:
            flash("Lien YouTube invalide", 'error')
            return redirect(url_for('centre_courses'))

        try:
            cursor.execute("""
                INSERT INTO Parcours
                (intitule, description, objectifs, video_url, date_debut, date_fin, email_apprenant, centre)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (intitule, description, objectifs, video_id, date_debut, date_fin, email, centre))

            conn.commit()
            flash("Parcours créé avec succès", 'success')
        except Exception as e:
            conn.rollback()
            flash(f"Erreur de création : {str(e)}", 'error')

    # Récupération des parcours du centre
    cursor.execute("""
        SELECT p.*, a.Nom AS nom_apprenant, a.Prenom AS prenom_apprenant
        FROM Parcours p
        JOIN Apprenants a ON p.email_apprenant = a.AdresseEmail
        WHERE p.centre = %s
    """, (centre,))

    parcours = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('centre_courses.html', parcours=parcours, centre=centre)


@app.route('/api/delete-parcours/<int:parcours_id>', methods=['DELETE'])
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



@app.route('/download-apprenants-excel')
def download_apprenants_excel():
    if session.get('user_type') != 'Administrateur':
        return redirect(url_for('login'))

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
        return redirect(url_for('admin_apprenants'))

@app.route('/download-pedagogues-excel')
def download_pedagogues_excel():
    if session.get('user_type') != 'Administrateur':
        return redirect(url_for('login'))

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
        return redirect(url_for('admin_pedagogues'))

@app.route('/download-responsables-excel')
def download_responsables_excel():
    if session.get('user_type') != 'Administrateur':
        return redirect(url_for('login'))

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
        return redirect(url_for('admin_centres'))

@app.route('/get-apprenants')
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

@app.route('/get-pedagogues')
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


@app.route('/get-centres')
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

@app.route('/export-centre-presence-excel')
def export_centre_presence_excel():
    if session.get('user_type') != 'Responsable_de_centre_de_coding':
        return redirect(url_for('login'))

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



@app.route('/centre-apprenants')
def centre_apprenants():
    if session.get('user_type') != 'Responsable_de_centre_de_coding':
        return redirect(url_for('login'))
    
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


@app.route('/admin-pedagogues')
def admin_pedagogues():
    if session.get('user_type') != 'Administrateur':
        return redirect(url_for('login'))
    
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

    @app.route(f'/admin/save-{table_type}', methods=['POST'], endpoint=f'save_{endpoint}')
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







@app.route('/save-pedagogues', methods=['POST'])
def save_pedagogues():
    if session.get('user_type') != 'Administrateur':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()

        for change in data:
            # Logique de création
            if change['action'] == 'create':
                cursor.execute("""
                    INSERT INTO ResponsablePedagogique
                    (Nom, Prenom, AdresseEmail, MotDePasse, Phone, Ville, CodeCoupon, Centre)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    change.get('Nom', ''),
                    change.get('Prenom', ''),
                    change.get('AdresseEmail', ''),
                    change.get('MotDePasse', ''),
                    change.get('Phone', ''),
                    change.get('Ville', ''),
                    change.get('CodeCoupon', ''),
                    change.get('Centre', '')
                ))

            # Logique de mise à jour
            elif change['action'] == 'update':
                fields = change.get('fields', {})
                set_clause = []
                values = []

                for field, value in fields.items():
                    set_clause.append(f"{field} = %s")
                    values.append(value)

                values.append(change['id'])  # pour WHERE id = %s

                query = f"""
                    UPDATE ResponsablePedagogique
                    SET {', '.join(set_clause)}
                    WHERE id = %s
                """
                cursor.execute(query, values)

            # Logique de suppression
            elif change['action'] == 'delete':
                cursor.execute("""
                    DELETE FROM ResponsablePedagogique
                    WHERE id = %s
                """, (change['id'],))

        conn.commit()
        return jsonify({'status': 'success', 'message': 'Modifications sauvegardées'})

    except mysql.connector.Error as err:
        conn.rollback()
        print(f"Database error: {err}")
        return jsonify({'status': 'error', 'message': str(err)}), 500

    except Exception as e:
        conn.rollback()
        print(f"General error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

        
@app.route('/add-pedagogue', methods=['POST'])
def add_pedagogue():
    if session.get('user_type') != 'Administrateur':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO ResponsablePedagogique 
            (Nom, Prenom, AdresseEmail, MotDePasse, Phone, Ville, CodeCoupon, Centre)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data['Nom'],
            data['Prenom'],
            data['AdresseEmail'],
            data['MotDePasse'],
            data['Phone'],
            data['Ville'],
            data['CodeCoupon'],
            data['Centre']
        ))
        
        conn.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/delete-pedagogue/<int:pedagogue_id>', methods=["DELETE"])
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
@app.route('/admin/save-responsables', methods=['POST'])
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

@app.route('/admin/add-responsable', methods=['POST'])
def add_responsable():
    if session.get('user_type') != 'Administrateur':
        return redirect(url_for('login'))
    
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

@app.route('/admin/delete-responsable/<int:responsable_id>')
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

# Mise à jour de la route /admin/save-apprenants
@app.route('/admin/save-apprenants', methods=['POST'])
def save_apprenants():
    if session.get('user_type') != 'Administrateur':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

    conn = None
    cursor = None
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()

        # Convertir les dates vides en NULL
        def parse_date(value):
            return None if value in ['', None] else value

        for change in data:
            action = change.get('action')
            
            if action == 'create':
                fields = change.get('fields', {})
                
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
                    fields.get('CodeCoupon') or None,  # Conversion en NULL si vide
                    parse_date(fields.get('DateDebutFormation')),
                    parse_date(fields.get('DateFinFormation')),
                    fields.get('Centre'),
                    fields.get('NiveauDeConnaissance')
                ))

            elif action == 'update':
                fields = change.get('fields', {})
                set_clause = []
                values = []
                
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
                # Suppression en cascade manuelle
                cursor.execute("DELETE FROM Presence WHERE apprenant_id = %s", (apprenant_id,))
                cursor.execute("DELETE FROM PresenceCentre WHERE apprenant_id = %s", (apprenant_id,))
                cursor.execute("DELETE FROM Apprenants WHERE id = %s", (apprenant_id,))

        conn.commit()
        return jsonify({
            'status': 'success',
            'message': f'{len(data)} modifications sauvegardées avec succès'
        })

    except mysql.connector.Error as err:
        conn.rollback()
        print(f"Erreur MySQL: {err.msg}")
        return jsonify({
            'status': 'error',
            'message': f'Erreur de base de données: {err.msg}',
            'code': err.errno
        }), 500

    except Exception as e:
        conn.rollback()
        print(f"Erreur générale: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Erreur inattendue: {str(e)}'
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route('/admin/add-apprenant', methods=['POST'])
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
@app.route('/admin/delete-apprenant/<int:apprenant_id>', methods=['DELETE'])
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


ALLOWED_FIELDS = {'Nom', 'Prenom', 'AdresseEmail', 'MotDePasse', 'Phone', 'Ville', 'CodeCoupon', 'Centre'}

@app.route('/save-centres', methods=['POST'])
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




def get_field_name(index):
    fields = ['Nom', 'Prenom', 'AdresseEmail', 'MotDePasse', 'Phone', 'Ville', 'CodeCoupon', 'Centre']
    return fields[index-1]




@app.route('/export-presence-excel')
def export_presence_excel():
    if session.get('user_type') != 'ResponsablePedagogique':
        return redirect(url_for('login'))
    
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




@app.route('/pedagogical-presence')
def pedagogical_presence():
    if session.get('user_type') != 'ResponsablePedagogique':
        return redirect(url_for('login'))
    
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
@app.route('/static/<path:filename>')
def serve_static(filename):
    root_dir = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(root_dir, filename)

@app.route('/')
def login():
    return render_template('login.html',title='login-page')



@app.route('/authenticate', methods=['POST'])
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
            "Administrateur": "Administrateur"
        }

        if user_type not in table_map:
            return redirect(url_for('login'))

        cursor.execute(f'''
            SELECT * FROM {table_map[user_type]}
            WHERE AdresseEmail = %s AND MotDePasse = %s
        ''', (email, password))
        user = cursor.fetchone()

        if user:
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
            session['email'] = email  # Ajout de l'email dans la session

            if user_type == "Responsable_de_centre_de_coding":
                session['centre'] = user['Centre']

            cursor.close()
            conn.close()
            return redirect(url_for('dashboard'))

        cursor.close()
        conn.close()
        return redirect(url_for('login'))

    except Exception as e:
        print(f"Erreur d'authentification : {str(e)}")
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()
        return redirect(url_for('login'))






    
@app.route('/admin-centres', endpoint='admin_centres_unique')
def admin_centres():
    if session.get('user_type') != 'Administrateur':
        return redirect(url_for('login'))
    
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


@app.route('/admin/apprenants/<int:apprenant_id>', methods=['PATCH', 'DELETE'])
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


@app.route('/admin-apprenants')
def admin_apprenants():
    if 'user_type' not in session or session.get('user_type') != 'Administrateur':
        return redirect(url_for('login'))

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


@app.route('/admin/add-user', methods=['POST'])
def admin_add_user():
    if session.get('user_type') != 'Administrateur':
        return redirect(url_for('login'))
    
    user_type = request.form.get('user_type')
    # Récupérez les autres champs du formulaire
    
    try:
        print("hacked yeah!!!!!")
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

@app.route('/admin/delete-user/<user_type>/<int:user_id>')
def admin_delete_user(user_type, user_id):
    if session.get('user_type') != 'Administrateur':
        return redirect(url_for('login'))
    
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

@app.route('/dashboard')
def dashboard():
    user_type = session.get('user_type')

    if not user_type:
        return redirect(url_for('login'))

    if user_type == "Responsable_de_centre_de_coding":
        return render_template('respo_coding_dashboard.html',title="respo_coding_dash")
    elif user_type == "Apprenants":
        return render_template('learn_dashboard.html')
    elif user_type == "ResponsablePedagogique":
        return render_template('pedagogical_dash.html')
    elif user_type == "Administrateur":
        return render_template('admin_dash.html')

    return redirect(url_for('login'))

@app.route('/knowledge-base')
def knowledge_base():
    # Redirection immédiate pour tous les utilisateurs non autorisés
    if session.get('user_type') not in ['ResponsablePedagogique', 'Responsable_de_centre_de_coding']:
        return redirect(url_for('dashboard'))
    return render_template('knowledge_base_2')

@app.route('/tutorials')
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
    return redirect(url_for('login'))


@app.route('/courses')
def courses():
    if session.get('user_type') != 'Apprenants':
        return redirect(url_for('login'))

    email = session.get('email')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Utilisation de DISTINCT pour éviter les doublons
    cursor.execute("""
        SELECT DISTINCT p.*
        FROM Parcours p
        JOIN Apprenants a ON p.email_apprenant = a.AdresseEmail
        WHERE a.AdresseEmail = %s
    """, (email,))

    parcours_list = cursor.fetchall()

    for parcours in parcours_list:
        parcours['video_id'] = parcours['video_url']  # Déjà stocké comme ID

    cursor.close()
    conn.close()

    return render_template('courses.html', mes_parcours=parcours_list)



@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')
    results = perform_search(query)
    return render_template('search_results.html', results=results)


@app.route('/view/<int:file_id>')
def view_file(file_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM BaseConnaissances WHERE id = %s", (file_id,))
    file_data = cursor.fetchone()
    cursor.close()
    conn.close()

    if file_data:
        return send_file(
            io.BytesIO(file_data['fichier']),
            mimetype=f'application/{file_data["type_fichier"]}',
            as_attachment=False,
            download_name=f'{file_data["titre"]}.{file_data["type_fichier"]}'
        )
    else:
        return 'Fichier non trouvé', 404

@app.route('/pedagogical-knowledge-base')
def pedagogical_knowledge_base():
    if session.get('user_type') == 'ResponsablePedagogique':
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM BaseConnaissances")
        files = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('pedagocial_dash.html', files=files)
    return redirect(url_for('login'))

@app.route('/pedagogical-tutorials', methods=['GET', 'POST'])
def pedagogical_tutorials():
    if session.get('user_type') != 'ResponsablePedagogique':
        return redirect(url_for('login'))

    if request.method == 'POST':
        categorie = request.form.get('categorie')
        video_url = request.form.get('video-url')
        description = request.form.get('description')
        objectifs = request.form.get('objectifs')

        if not video_url:
            return "Veuillez insérer un lien YouTube", 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Tutoriels (categorie, video_url, description, objectifs)
            VALUES (%s, %s, %s, %s)
        """, (categorie, video_url, description, objectifs))
        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for('pedagogical_tutorials'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Tutoriels")
    tutoriels = cursor.fetchall()
    cursor.close()
    conn.close()
    
    # Correction de l'indentation ici
    for tuto in tutoriels:
        match = re.search(
            r'(?:youtu\.be/|youtube\.com/(?:embed/|v/|watch\?v=|watch\?.+&v=))([^?&]+)',
            tuto['video_url']
        )
        tuto['video_id'] = match.group(1) if match else None

    return render_template('pedagogical_tuto.html', tutoriels=tutoriels)


@app.route('/api/add-tutorial', methods=['POST'])
def api_add_tutorial():
    data = request.get_json()
    categorie = data.get('categorie')
    video_url = data.get('video_url')
    description = data.get('description')
    objectifs = data.get('objectifs')

    if not video_url:
        return jsonify({'error': 'URL manquante'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Tutoriels (categorie, video_url, description, objectifs)
        VALUES (%s, %s, %s, %s)
    """, (categorie, video_url, description, objectifs))
    conn.commit()

    # Récupérer l’ID vidéo YouTube
    match = re.search(r'(?:youtu\.be/|youtube\.com/(?:embed/|v/|watch\?v=|watch\?.+&v=))([^?&]+)', video_url)
    video_id = match.group(1) if match else None

    cursor.close()
    conn.close()

    return jsonify({
        'categorie': categorie,
        'description': description,
        'objectifs': objectifs,
        'video_id': video_id
    }), 200
    
@app.route('/api/delete-tutorial/<int:tuto_id>', methods=['DELETE'])
def delete_tutorial(tuto_id):
    if session.get('user_type') != 'ResponsablePedagogique':
        return jsonify({'error': 'Non autorisé'}), 403

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Tutoriels WHERE id = %s", (tuto_id,))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'message': 'Tutoriel supprimé'}), 200



# Responsable de centre de coding
@app.route('/Responsable_de_centre_de_coding-knowledge-base')
def responsable_centre_knowledge_base():
    if session.get('user_type') == 'Responsable_de_centre_de_coding':
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM BaseConnaissances")
        files = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('admin_knowledge.html', files=files)
    return redirect(url_for('login'))


@app.route('/api/delete-knowledge/<int:file_id>', methods=['DELETE'])
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


@app.route('/Responsable_de_centre_de_coding-tutorials')
def responsable_centre_tutorials():
    if session.get('user_type') == 'Responsable_de_centre_de_coding':
        return render_template('admin_tuto.html')
    return redirect(url_for('login'))


@app.route('/logout')
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
    return redirect(url_for('login'))


def perform_search(query):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT title, content FROM knowledge_base WHERE content LIKE %s', ('%' + query + '%',))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results





if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)


