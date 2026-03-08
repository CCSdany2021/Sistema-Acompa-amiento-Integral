import psycopg2

def list_databases(password):
    try:
        # Connect to the default 'postgres' database to list others
        conn = psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password=password,
            host="localhost"
        )
        cursor = conn.cursor()
        
        cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
        rows = cursor.fetchall()
        
        print("\n--- BASES DE DATOS ENCONTRADAS ---")
        found_student_db = False
        for row in rows:
            db_name = row[0]
            print(f"- {db_name}")
            if "estud" in db_name.lower() or "student" in db_name.lower() or "school" in db_name.lower() or "acomp" in db_name.lower():
                found_student_db = True
                
        if found_student_db:
            print("\n[!] Se encontraron bases de datos que podrían contener información de estudiantes.")
        else:
            print("\n[i] No se encontraron bases de datos con nombres obvios de 'estudiantes', pero revisa la lista anterior.")
            
        conn.close()
        return True
        
    except psycopg2.OperationalError as e:
        if "password authentication failed" in str(e):
            print("\n[ERROR] La contraseña 'password' es incorrecta.")
        else:
            print(f"\n[ERROR] No se pudo conectar a PostgreSQL: {e}")
        return False

if __name__ == "__main__":
    # Trying with the default password found in .env
    list_databases("password")
