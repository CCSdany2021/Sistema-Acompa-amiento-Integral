from src.database import engine
from sqlalchemy import MetaData

metadata = MetaData()
metadata.reflect(bind=engine)
for table in metadata.sorted_tables:
    print(f"Table: {table.name}")
    for col in table.columns:
        print(f"  Column: {col.name}")
