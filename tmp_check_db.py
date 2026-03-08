from src.database import engine
from sqlalchemy import text
import pandas as pd

with engine.connect() as conn:
    print("Checking columns in reports table...")
    result = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'reports';"))
    df = pd.DataFrame(result.fetchall(), columns=['column_name', 'data_type'])
    print(df)
