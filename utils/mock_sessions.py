import json
import random
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional
from pathlib import Path
from pydantic import BaseModel, Field
import sys
sys.path.append('..')

# Importing existing models
from models.session import Session, Prescription

OUTPUT_DIR = Path("../data/sessions")
OUTPUT_DIR_PRESC = Path("../data/prescriptions")
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_DIR_PRESC.mkdir(exist_ok=True)
PROTOCOL_DIR = Path("../data/protocols")

# Define mock patient details
PATIENT_ID = "P001"
PROTOCOL_IDS = [f.stem for f in PROTOCOL_DIR.glob("*.json")]
NUM_SESSIONS_PER_WEEK = 28
START_DATE = date(2024, 2, 19)  # Starting Monday
END_DATE = START_DATE + timedelta(days=6)  # End of the week


def generate_mock_prescriptions(patient_id: str) -> List[Prescription]:
    """Generates weekly prescriptions for a patient."""
    prescriptions = []
    for i, protocol_id in enumerate(PROTOCOL_IDS):
        weekday = (START_DATE + timedelta(days=i % 7)).strftime("%A")
        prescription = Prescription(
            prescription_id=f"PRESC{i+1:03d}",
            patient_id=patient_id,
            protocol_id=protocol_id,
            start_date=START_DATE,
            end_date=END_DATE,
            weekday=weekday,
            prescribed_duration=random.randint(30, 60),  # 30-60 minutes per session
            decision_scores={"motor_score": random.uniform(0.5, 1.0)},
            explanation="Generated mock prescription",
            prescribed_difficulty=random.uniform(0, 1)
        )
        prescriptions.append(prescription)
        save_to_json(prescription, OUTPUT_DIR_PRESC / f"{prescription.prescription_id}.json")
    return prescriptions


def generate_mock_sessions(patient_id: str, prescriptions: List[Prescription]) -> List[Session]:
    """Generates 28 sessions per week based on prescriptions, matching weekdays."""
    sessions = []

    for prescription in prescriptions:
        session_date = prescription.start_date
        while session_date <= prescription.end_date:
            if session_date.strftime("%A") == prescription.weekday:
                for _ in range(4):  # 4 sessions per matching weekday
                    session_time = datetime.combine(session_date, datetime.min.time()) + timedelta(hours=random.randint(8, 18))
                    session = Session(
                        session_id=f"S{len(sessions)+1:03d}",
                        patient_id=patient_id,
                        protocol_id=prescription.protocol_id,
                        prescription_id=prescription.prescription_id,
                        timestamp=session_time,
                        duration=random.uniform(15, 60),
                        difficulty_modulator=random.uniform(0, 1),
                        performance_score=random.uniform(0.5, 1.0),
                        _prescription=prescription
                    )
                    sessions.append(session)
                    save_to_json(session, OUTPUT_DIR / f"{session.session_id}.json")
            session_date += timedelta(days=1)  # Move to next day

    return sessions


def save_to_json(data: BaseModel, filename: Path):
    """Saves a Pydantic model to a distinct JSON file."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data.model_dump(), f, indent=4, default=str)


if __name__ == "__main__":
    prescriptions = generate_mock_prescriptions(PATIENT_ID)
    sessions = generate_mock_sessions(PATIENT_ID, prescriptions)
    print("Mock weekly prescription and session JSON files generated successfully!")
