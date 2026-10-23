import os
import psycopg2
import matplotlib.pyplot as plt

# Στοιχεία σύνδεσης από το περιβάλλον (ο κωδικός από PGPASSWORD ή ~/.pgpass)
DB_CONFIG = {
    "dbname": os.environ.get("PGDATABASE", "postgres"),
    "user": os.environ.get("PGUSER", "postgres"),
    "password": os.environ.get("PGPASSWORD"),
    "host": os.environ.get("PGHOST", "localhost"),
    "port": os.environ.get("PGPORT", "5432"),
}

def generate_chart():
    print("📊 Δημιουργία γραφήματος από τα δεδομένα της PostgreSQL...")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # Παίρνουμε τον μέσο όρο βαθμολογίας ανά κατηγορία
    query = """
        SELECT c.category_name, ROUND(AVG(r.rating), 2) as avg_rating
        FROM reviews r
        JOIN categories c ON r.category_id = c.id
        GROUP BY c.category_name
        ORDER BY avg_rating DESC;
    """
    cur.execute(query)
    rows = cur.fetchall()
    
    cur.close()
    conn.close()
    
    # Χωρίζουμε τα δεδομένα σε λίστες για τα X και Y
    categories = [row[0] for row in rows]
    ratings = [row[1] for row in rows]
    
    # Δημιουργία γραφήματος
    plt.figure(figsize=(8, 5))
    plt.bar(categories, ratings, color='#3178c6', width=0.5)
    plt.xlabel('Κατηγορία Κριτικής', fontsize=12)
    plt.ylabel('Μέσος Όρος Βαθμολογίας', fontsize=12)
    plt.title('Μέσος Όρος Βαθμολογίας ανά Κατηγορία (AI Review Auditor)', fontsize=14, fontweight='bold')
    plt.ylim(0, 5) # Η βαθμολογία είναι από 1 έως 5
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Αποθήκευση εικόνας
    output_filename = "ratings_chart.png"
    plt.savefig(output_filename, bbox_inches='tight')
    print(f"✅ Το γράφημα αποθηκεύτηκε επιτυχώς ως '{output_filename}'!")
    
    # Εμφάνιση γραφήματος στην οθόνη
    plt.show()

if __name__ == "__main__":
    generate_chart()