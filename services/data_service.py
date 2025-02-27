# data_service.py
import json
from pathlib import Path
from typing import List
from models import Patient, Protocol

class PatientRepository:
    def __init__(self, data_dir="data/patients"):
        self.data_dir = Path(data_dir)

    def get_all_patient_ids(self) -> List[str]:
        """Get list of all available patient IDs"""
        return [f.stem for f in self.data_dir.glob("*.json")]

    def get_patient(self, patient_id: str) -> Patient:
        """Get single patient by ID"""
        patient_path = self.data_dir / f"{patient_id}.json"
        if not patient_path.exists():
            raise ValueError(f"Patient {patient_id} not found")

        with open(patient_path) as f:
            return Patient(**json.load(f))

class ProtocolRepository:
    def __init__(self, data_dir="data/protocols"):
        self.data_dir = Path(data_dir)

    def get_all_protocols(self) -> List[Protocol]:
        """Get all available protocols"""
        return [self.get_protocol(f.stem) for f in self.data_dir.glob("*.json")]

    def get_protocol(self, protocol_id: str) -> Protocol:
        """Get single protocol by ID"""
        protocol_path = self.data_dir / f"{protocol_id}.json"
        if not protocol_path.exists():
            raise ValueError(f"Protocol {protocol_id} not found")

        with open(protocol_path) as f:
            return Protocol(**json.load(f))