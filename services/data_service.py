# data_service.py
import json
from pathlib import Path
from typing import List
from collections import defaultdict
from models.patient import Patient
from models.protocol import Protocol
from models.session import Prescription, Session

class PatientRepository:
    def __init__(self, data_dir="data/patients", session_dir="data/sessions", prescription_dir="data/prescriptions"):
        self.data_dir = Path(data_dir)
        self.session_dir = Path(session_dir)
        self.prescription_dir = Path(prescription_dir)

    def get_all_patient_ids(self) -> List[str]:
        """Get list of all available patient IDs"""
        return [f.stem for f in self.data_dir.glob("*.json")]

    def get_all_patients(self) -> List[Protocol]:
        """Get all available protocols"""
        patients = [self.get_patient(patient_id) for patient_id in self.get_all_patient_ids()]
        return self._load_mock_data(patients)

    def get_patient(self, patient_id: str) -> Patient:
        """Get single patient by ID"""
        patient_path = self.data_dir / f"{patient_id}.json"
        if not patient_path.exists():
            raise ValueError(f"Patient {patient_id} not found")

        with open(patient_path) as f:
            return Patient(**json.load(f))

    def _load_mock_data(self, patients: List[Patient]) -> List[Patient]:
        """Loads and assigns mock prescriptions and sessions to patients."""
        # Load mock prescriptions
        prescription_files = list(self.prescription_dir.glob("PRESC*.json"))
        mock_prescriptions = [json.load(open(file, "r")) for file in prescription_files]

        # Load mock sessions
        session_files = list(self.session_dir.glob("S*.json"))
        mock_sessions = [json.load(open(file, "r")) for file in session_files]

        # Organize prescriptions and sessions
        prescriptions_by_patient = defaultdict(list)
        prescriptions_by_id = {}
        sessions_by_prescription = defaultdict(list)

        for presc in mock_prescriptions:
            prescription = Prescription(**presc)
            prescriptions_by_patient[prescription.patient_id].append(prescription)
            prescriptions_by_id[prescription.prescription_id] = prescription  # Store for backref

        for sess in mock_sessions:
            session = Session(**sess)
            sessions_by_prescription[session.prescription_id].append(session)

        # Assign prescriptions and sessions to patients
        for patient in patients:
            patient.prescriptions = prescriptions_by_patient.get(patient.patient_id, [])
            for prescription in patient.prescriptions:
                prescription_sessions = sessions_by_prescription.get(prescription.prescription_id, [])
                for session in prescription_sessions:
                    session._prescription = prescription  # Restore backref
                    patient.sessions.append(session)

        return patients

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