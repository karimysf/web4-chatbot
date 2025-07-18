from config import GROQ_API_KEY
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.docstore.document import Document
from bs4 import BeautifulSoup
from utils.db import get_db_connection
import requests


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
