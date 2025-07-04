from main import app, db  # Change 'your_app_module' to your actual app filename (without .py)

with app.app_context():
    db.create_all()
    print("✅ Database tables created successfully.")