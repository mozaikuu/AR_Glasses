from datetime import datetime, timedelta
from random import Random

from sqlalchemy import func, select

from app.db.models import Student
from app.db.session import Base, SessionLocal, engine


FAKE_STUDENTS = [
    {"name": "Ahmed Hassan", "home": "Mansoura - Toriel", "lat": 31.0432, "lng": 31.3841},
    {"name": "Sara Mostafa", "home": "Mansoura - El Gomhoria", "lat": 31.0368, "lng": 31.3722},
    {"name": "Youssef Emad", "home": "Mansoura - El Mashaya", "lat": 31.0274, "lng": 31.3657},
    {"name": "Mariam Tarek", "home": "Mansoura - Stadium", "lat": 31.0302, "lng": 31.3951},
    {"name": "Omar Adel", "home": "Talkha", "lat": 31.0601, "lng": 31.3778},
    {"name": "Nour Ali", "home": "Mansoura - Sandoub", "lat": 31.0127, "lng": 31.4095},
    {"name": "Hana Khaled", "home": "Mansoura - University District", "lat": 31.0421, "lng": 31.3520},
    {"name": "Kareem Fawzy", "home": "Mansoura - Gihan St.", "lat": 31.0261, "lng": 31.3509},
]


def init_db_and_seed_students() -> None:
    Base.metadata.create_all(bind=engine)

    rng = Random(2026)
    now = datetime.utcnow()

    with SessionLocal() as db:
        existing_count = db.scalar(select(func.count(Student.id)))
        if existing_count and existing_count > 0:
            return

        seeded_rows: list[Student] = []
        for entry in FAKE_STUDENTS:
            is_active = rng.random() > 0.35
            seeded_rows.append(
                Student(
                    name=entry["name"],
                    home_location=entry["home"],
                    home_lat=entry["lat"],
                    home_lng=entry["lng"],
                    wallet_balance=round(rng.uniform(40, 260), 2),
                    subscription_status="active" if is_active else "inactive",
                    subscription_expires_at=(now + timedelta(days=rng.randint(7, 35)))
                    if is_active
                    else None,
                    usage_history=[],
                )
            )

        db.add_all(seeded_rows)
        db.commit()
