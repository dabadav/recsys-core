# tests/test_scoring.py
from services.data_service import PatientRepository

def test_motor_scoring():
    patient = PatientRepository().get_patient("P001")
    # protocol = ProtocolRepository().get_protocol("PR200")
    # scorer = ProtocolScorer(patient, protocol)
    # assert 15 <= scorer.calculate_deficit_match() <= 20