from app import app, db, Complaint
from datetime import datetime, timedelta

with app.app_context():
    c = Complaint.query.order_by(Complaint.created_at.desc()).first()
    if c:
        c.created_at = datetime.utcnow() - timedelta(days=7)
        db.session.commit()
        print(f"Updated complaint #{c.id} ('{c.title}') to 7 days ago.")
    else:
        print("No complaints found.")