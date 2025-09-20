from config.settings import settings
from database.session import init_db

print("DATABASE_URL:", settings.DATABASE_URL)
init_db()
print("Database initialized successfully!")
