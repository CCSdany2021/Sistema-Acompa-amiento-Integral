import psycopg2

try:
    conn = psycopg2.connect(dbname='admisiones_db', user='postgres', password='admin8128', host='localhost')
    cr = conn.cursor()
    cr.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'personal_estudiante'")
    cols = [r[0] for r in cr.fetchall()]
    print("Columns:", cols)
    
    cr.execute("SELECT * FROM personal_estudiante LIMIT 3")
    print("Data:", cr.fetchall())
    conn.close()
except Exception as e:
    print(e)
