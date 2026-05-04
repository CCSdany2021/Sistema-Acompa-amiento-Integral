from src.database import SessionLocal
from src import models, schemas
import traceback


def check_reports():
    db = SessionLocal()
    try:
        reports = db.query(models.Report).all()
        print(f"Total reports: {len(reports)}")
        for r in reports:
            try:
                # Try to create a schema object, which often reveals validation errors
                s = schemas.Report.from_orm(r)
                print(f"Report {r.id}: OK")
            except Exception as e:
                print(f"Report {r.id}: ERROR during schema conversion")
                print(e)
                # traceback.print_exc()
    except Exception as e:
        print(f"Query error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    check_reports()
