import os
import psycopg2
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# 1. Το Groq API Key σου
if not os.environ.get("GROQ_API_KEY"):
    raise SystemExit("Λείπει το GROQ_API_KEY")

# 2. Σύνδεση με τη PostgreSQL για να πάρουμε τα δεδομένα με JOIN
DB_CONFIG = {
    "dbname": os.environ.get("PGDATABASE", "postgres"),
    "user": os.environ.get("PGUSER", "postgres"),
    "password": os.environ.get("PGPASSWORD"),
    "host": os.environ.get("PGHOST", "localhost"),
    "port": os.environ.get("PGPORT", "5432"),
}

def load_reviews_from_postgres():
    print("📥 Ανάκτηση κριτικών με JOIN από τη PostgreSQL...")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # Χρησιμοποιούμε JOIN για να φέρουμε μαζί την κατηγορία και την κριτική
    query = """
        SELECT r.author_name, r.rating, r.comment, r.sentiment, r.ai_suggestion, c.category_name
        FROM reviews r
        LEFT JOIN categories c ON r.category_id = c.id;
    """
    cur.execute(query)
    rows = cur.fetchall()
    
    cur.close()
    conn.close()
    
    docs = []
    for row in rows:
        author, rating, comment, sentiment, suggestion, category = row
        # Δημιουργούμε ένα πλούσιο κείμενο που περιέχει και την κατηγορία
        content = (
            f"Κατηγορία: {category} | Συγγραφέας: {author} | "
            f"Βαθμολογία: {rating}/5 | Σχόλιο: {comment} | "
            f"Συναίσθημα: {sentiment} | Πρόταση AI: {suggestion}"
        )
        docs.append(Document(page_content=content))
        
    return docs

# 3. Φόρτωση δεδομένων από τη βάση
raw_documents = load_reviews_from_postgres()

if not raw_documents:
    print("⚠️ Δεν βρέθηκαν κριτικές στη βάση!")
    exit()

# 4. Τεμαχισμός και δημιουργία Διανυσματικής Βάσης (Chroma)
print("🔄 Δημιουργία διανυσματικής μνήμης...")
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
chunks = text_splitter.split_documents(raw_documents)

embeddings = HuggingFaceEmbeddings(model_name="paraphrase-multilingual-MiniLM-L12-v2")
vectorstore = Chroma.from_documents(documents=chunks, embedding=embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# 5. Αρχικοποίηση AI (Groq + Qwen)
print("🤖 Εκκίνηση AI Assistant...")
llm = ChatGroq(model_name="qwen/qwen3.8-27b", temperature=0)

system_prompt = (
    "Είσαι ένας έξυπνος αναλυτής δεδομένων επιχείρησης. "
    "Χρησιμοποίησε ΜΟΝΟ τα παρακάτω δεδομένα κριτικών από τη βάση δεδομένων για να απαντήσεις. "
    "Αν η απάντηση δεν υπάρχει στα δεδομένα, πες: 'Δεν προκύπτει από τις καταχωρημένες κριτικές'.\n\n"
    "Δεδομένα:\n{context}"
)
prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}")
])

# Συνάρτηση μορφοποίησης των εγγράφων για το LCEL
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# Σύγχρονη αλυσίδα RAG (LCEL)
rag_chain = (
    {"context": retriever | format_docs, "input": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

print("\n--- 🚀 AI Review Intelligence Auditor Online (Γράψε 'έξοδος' για τερματισμό) ---")

while True:
    erotisi = input("\nΚάνε μια ερώτηση για τις κριτικές (π.χ. 'Τι παράπονα υπάρχουν ανά κατηγορία;'): ")
    
    if erotisi.lower() == 'έξοδος':
        print("Τερματισμός προγράμματος...")
        break
        
    response = rag_chain.invoke(erotisi)
    print(f"\n💡 Απάντηση: {response}")