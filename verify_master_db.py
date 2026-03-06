import psycopg2

def list_dbs_and_tables():
    password = 'admin8128'
    host = 'localhost'
    user = 'postgres'
    
    try:
        conn = psycopg2.connect(dbname='postgres', user=user, password=password, host=host)
        cursor = conn.cursor()
        cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
        dbs = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        for db in dbs:
            try:
                c = psycopg2.connect(dbname=db, user=user, password=password, host=host)
                cr = c.cursor()
                cr.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
                tables = [r[0] for r in cr.fetchall()]
                print(f"Base de datos: '{db}' -> Tablas: {tables}")
                c.close()
            except Exception as e:
                print(f"No se pudo leer '{db}': {e}")
                
    except Exception as e:
        print(f"Error principal: {e}")

if __name__ == '__main__':
    list_dbs_and_tables()
