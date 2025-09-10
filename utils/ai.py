from config import GROQ_API_KEY
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.docstore.document import Document
from bs4 import BeautifulSoup
from utils.db import get_db_connection
import requests
from groq import Groq
import os

# Initialiser client Groq
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# === Fonction API Groq ===
def call_groq_mixtral(prompt):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.1-8b-instant",
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


# === Fonction RAG améliorée ===
def rag_chat(question):
    try:
        documents = get_documents()

        if documents:
            langchain_docs = [
                Document(
                    page_content=doc["description"],
                    metadata={"titre": doc["titre"], "lien_web": doc.get("lien_web")}
                )
                for doc in documents
            ]

            # Embeddings et vectordb
            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            vectordb = Chroma.from_documents(langchain_docs, embeddings)
            retriever = vectordb.as_retriever()

            # Récupération des docs pertinents
            docs = retriever.invoke(question)
            if docs:
                context = "\n".join([doc.page_content for doc in docs[:3]])
                prompt = f"""Voici un contexte extrait d'une base de connaissances :
{context}
        

Question : {question}
Réponds en 4 phrases max, de manière claire, humaine, sympa, précise et pédagogique."""
                print(context)
                return call_groq_mixtral(prompt)

        # Fallback si aucun doc pertinent trouvé
        print("⚠️ Aucun contexte trouvé -> recherche Web")
        web_content = search_web(question)
        if web_content:
            prompt = f"""Voici des informations trouvées sur le web :
{web_content}

Question : {question}
Réponds en 4 phrases max de manière claire, humaine, sympa, précise et pédagogique."""
            return call_groq_mixtral(prompt)

        # Fallback ultime (réponse directe sans contexte)
        return call_groq_mixtral(question)

    except Exception as e:
        print("Erreur RAG :", e)
        return "❌ Une erreur est survenue dans le traitement."


# === Gestion de la base de connaissances ===
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
                doc['description'] += f" Contenu du lien web: {web_content[:1000]}..."  # Limite pour éviter surcharge
        processed_documents.append(doc)
    return processed_documents


# === Scraping web ===
def fetch_web_content(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text(separator=' ', strip=True)
        return text
    except Exception as e:
        print(f"Erreur lors de la récupération du contenu de {url}: {e}")
        return None

def process_web_content(url):
    content = fetch_web_content(url)
    if content:
        try:
            content = content.encode('utf-8', errors='replace').decode('utf-8')
            return content
        except UnicodeEncodeError as e:
            print(f"Erreur d'encodage : {e}")
            return None
    return None


# === Fallback recherche web (API / scraping simple) ===
def search_web(query):
    try:
        url = f"https://duckduckgo.com/html/?q={query}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        results = soup.find_all("a", {"class": "result__a"}, limit=3)
        texts = [r.get_text() for r in results]
        return " ".join(texts) if texts else None
    except Exception as e:
        print(f"Erreur recherche web: {e}")
        return None
