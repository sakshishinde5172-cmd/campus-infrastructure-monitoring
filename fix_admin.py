from app import app, db, User
with app.app_context():
    u = User.query.filter_by(username='admin').first()
    u.is_admin = True
    db.session.commit()
    print('fixed:', u.username, u.is_admin)
