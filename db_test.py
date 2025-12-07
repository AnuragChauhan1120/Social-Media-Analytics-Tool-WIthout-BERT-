from sqlalchemy import create_engine, text

DB_URI =  "postgresql://anurag:Anurag%40011@localhost:5432/social_analytics"

print("Using DB_URI:", DB_URI)

try:
    engine = create_engine(DB_URI)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print(" Database connection successful!", result.fetchone())
except Exception as e:
    print(" Database connection failed:", e)
