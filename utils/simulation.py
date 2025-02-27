# simulation.py
from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel
import numpy as np
from models.patient import Patient, ClinicalScores
from models.protocol import Protocol

class SessionOutcome(BaseModel):
    timestamp: datetime
    protocol_id: str
    completion_rate: float
    performance_score: float
    fatigue_level: float
    adherence: float
    notes: Optional[str] = None

class SessionSimulator:
    def __init__(self, patient: Patient):
        self.patient = patient
        self.base_adherence = patient.recovery_profile.expected_adherence
        self.motor_capacity = 1 - (1 - self.patient.clinical_scores.arat.total / 57)
        self.cognitive_capacity = 1 - (1 - self.patient.clinical_scores.moca.total / 30)

    def simulate_session(self, protocol: Protocol, current_fatigue: float = 0.0) -> SessionOutcome:
        # Calculate base performance probability
        motor_match = self._calculate_motor_match(protocol)
        cognitive_match = self._calculate_cognitive_match(protocol)

        # Apply fatigue effect
        effective_motor = max(0, motor_match * (1 - current_fatigue))
        effective_cognitive = max(0, cognitive_match * (1 - current_fatigue * 0.7))

        # Calculate performance metrics
        completion_rate = np.random.beta(
            effective_motor * 10,
            (1 - effective_motor) * 10
        )

        performance_score = np.random.beta(
            effective_cognitive * 10,
            (1 - effective_cognitive) * 10
        )

        # Calculate adherence with some randomness
        base_adherence = self.base_adherence * (1 - current_fatigue * 0.5)
        adherence = np.random.normal(base_adherence, 0.1)
        adherence = max(0, min(1, adherence))

        # Calculate new fatigue level
        new_fatigue = self._calculate_fatigue_increase(
            protocol, completion_rate, current_fatigue
        )

        return SessionOutcome(
            timestamp=datetime.now(),
            protocol_id=protocol.id,
            completion_rate=completion_rate,
            performance_score=performance_score,
            fatigue_level=new_fatigue,
            adherence=adherence
        )

    def _calculate_motor_match(self, protocol: Protocol) -> float:
        difficulty_map = {'low': 0.3, 'medium': 0.6, 'high': 0.9}
        protocol_difficulty = difficulty_map[protocol.difficulty_motor]

        if protocol_difficulty > self.motor_capacity:
            return max(0, 1 - (protocol_difficulty - self.motor_capacity) * 2)
        return 1.0

    def _calculate_cognitive_match(self, protocol: Protocol) -> float:
        difficulty_map = {'low': 0.3, 'medium': 0.6, 'high': 0.9}
        protocol_difficulty = difficulty_map[protocol.difficulty_cognitive]

        if protocol_difficulty > self.cognitive_capacity:
            return max(0, 1 - (protocol_difficulty - self.cognitive_capacity) * 2)
        return 1.0

    def _calculate_fatigue_increase(self, protocol: Protocol, completion_rate: float, current_fatigue: float) -> float:
        base_increase = protocol.safety_constraints.max_duration / 60.0  # Normalize to hours
        intensity_factor = {
            'low': 0.5,
            'medium': 0.75,
            'high': 1.0
        }[protocol.difficulty_motor]

        fatigue_increase = (
            base_increase * intensity_factor * completion_rate * (1 + current_fatigue)
        )

        return min(1.0, current_fatigue + fatigue_increase)