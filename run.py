"""Start the Budtender Feedback System."""
import subprocess
import sys
import os


def main():
    # Ensure data directories exist
    os.makedirs("data/uploads", exist_ok=True)

    # Initialize DB and seed
    print("Initializing database...")
    from app.database import init_db
    init_db()

    print("Seeding demo data...")
    from seed_data import seed
    seed()

    print("\n" + "=" * 60)
    print("  BUDTENDER FEEDBACK SYSTEM - Starting...")
    print("=" * 60)
    print()
    print("  Public Form:      http://localhost:8000/")
    print("  Admin Dashboard:  http://localhost:8000/admin/login")
    print()
    print("  Demo Accounts:")
    print("    Admin:   admin@weeden.com   / admin12345!")
    print("    Founder: founder@weeden.com / founder12345")
    print("    CEO:     ceo@weeden.com     / ceo1234567!")
    print()
    print("=" * 60)
    print()

    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
