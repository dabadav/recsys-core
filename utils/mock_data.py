import json
import random
from datetime import datetime
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from pathlib import Path

from models.patient import StrokeInfo, ARAT, MoCA, ClinicalScores, RecoveryProfile, Patient

def generate_random_patient(patient_id: str) -> Patient:
    """Generates a random patient profile based on Pydantic models."""
    demographics = {
        "age": random.randint(50, 80),
        "gender": random.choice(["male", "female"]),
        "height": random.randint(150, 190),
        "handedness": random.choice(["right", "left"])
    }

    stroke_info = StrokeInfo(
        type=random.choice(["ischemic", "hemorrhagic"]),
        location=random.choice(["left MCA", "right MCA", "brainstem", "cerebellum"]),
        heminegligence=random.randint(0, 1),
        paretic_side=random.choice(["left", "right"]),
        onset_date=datetime(2023, random.randint(1, 12), random.randint(1, 28))
    )

    arat_scores = ARAT(
        grasp=random.uniform(0, 18),
        grip=random.uniform(0, 12),
        pinch=random.uniform(0, 18),
        gross_movement=random.uniform(0, 9)
    )

    moca_scores = MoCA(
        VISUOSPATIAL=random.uniform(0, 5),
        NAMING=random.uniform(0, 3),
        MEMORY=random.uniform(0, 5),
        ATTENTION=random.uniform(0, 6),
        LANGUAGE=random.uniform(0, 3),
        ABSTRACTION=random.uniform(0, 2),
        DELAYED_RECALL=random.uniform(0, 5),
        ORIENTATION=random.uniform(0, 6)
    )

    clinical_scores = ClinicalScores(ARAT=arat_scores, MoCA=moca_scores)

    recovery_profile = RecoveryProfile(
        group=random.choice(["A1", "B2", "C3"]),
        expected_adherence=random.uniform(0.5, 1.0),
        motor_trajectory={"slope": random.uniform(0, 1), "variance": random.uniform(0, 0.1)},
        affective_baseline={"mood": random.uniform(1, 5), "motivation": random.uniform(1, 5)}
    )

    gaming_profile = {
        "videogame_experience": random.randint(0, 1),
        "computer_experience": random.randint(0, 1),
        "preferred_modalities": random.sample(["VR", "AR", "controller-based", "touchscreen"], 2)
    }

    tags = random.sample(["mild_neglect", "low_motivation", "prefers_gamification", "needs_guided_rehab"], 2)
    clinician_notes = "Generated patient profile with synthetic data."

    return Patient(
        patient_id=patient_id,
        demographics=demographics,
        stroke_info=stroke_info,
        clinical_scores=clinical_scores,
        recovery_profile=recovery_profile,
        gaming_profile=gaming_profile,
        clinician_notes=clinician_notes,
        tags=tags
    )

def save_patient_to_json(patient: Patient, filename: str):
    """Saves the patient profile to a JSON file."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(patient.model_dump(), f, indent=4, default=str)

if __name__ == "__main__":
    ids = ["P" + f"{i}".zfill(3) for i in range(5, 100)]
    data_dir = Path("../data/patients")
    for id in ids:
        patient = generate_random_patient(id)
        save_patient_to_json(patient, data_dir / Path(f"{id}.json"))
        print("Patient JSON file generated successfully!")
