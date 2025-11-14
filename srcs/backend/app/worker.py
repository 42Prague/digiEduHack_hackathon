import time
from datetime import datetime
from sqlmodel import Session, select

from .db import engine, init_db
from .models import FileMeta
from .analysis import analyze_file

POLL_INTERVAL = 5  # seconds

def main():
    init_db()

    while True:
        with Session(engine) as session:
            pending_files = session.exec(
                select(FileMeta).where(FileMeta.analysis_status == "pending")
            ).all()

            if not pending_files:
                time.sleep(POLL_INTERVAL)
                continue

            for f in pending_files:
                f.analysis_status = "processing"
                f.analysis_started_at = datetime.utcnow()
                session.add(f)
                session.commit()

                try:
                    analyze_file(session, f)
                    f.analysis_status = "done"
                    f.analysis_finished_at = datetime.utcnow()
                    f.analysis_error = None
                except Exception as e:
                    f.analysis_status = "failed"
                    f.analysis_finished_at = datetime.utcnow()
                    f.analysis_error = str(e)[:512]

                session.add(f)
                session.commit()

if __name__ == "__main__":
    main()
