from typing import Dict, Any
from datetime import datetime, date, timedelta
from pydantic import BaseModel, Field, field_validator, computed_field
from typing import List, Dict, Optional, Any
import pandas as pd
import numpy as np
from models.session import Prescription, Session
from models.protocol import Protocol

#########################
###### AGGREGATORS ######
#########################

class WeeklyPrescription(BaseModel):
    """Aggregates prescription data by week"""
    patient_id: str
    weekly_data: Dict[date, Dict[str, Any]] = Field(default_factory=dict)

    # @computed_field
    # def adherence_rate(self) -> Dict[date, float]:
    #     """Weekly adherence to prescribed sessions"""
    #     return {
    #         week: min(
    #             len(sessions) / prescriptions[0].target_sessions_per_week,
    #             1.0
    #         )
    #         for week, (prescriptions, sessions) in self.weekly_data.items()
    #     }

    def add_data(self, prescription: Prescription, sessions: List[Session]):
        """Group prescriptions and sessions by week"""
        current_date = prescription.start_date
        while current_date <= prescription.end_date:
            week_start = current_date - timedelta(days=current_date.weekday())
            self.weekly_data.setdefault(week_start, {
                'prescriptions': [],
                'sessions': []
            })
            self.weekly_data[week_start]['prescriptions'].append(prescription)
            current_date += timedelta(weeks=1)

        for session in sessions:
            week_start = session.timestamp.date() - timedelta(
                days=session.timestamp.date().weekday()
            )
            if week_start in self.weekly_data:
                self.weekly_data[week_start]['sessions'].append(session)

class ProtocolSessions(BaseModel):
    """Aggregates protocol performance for a single patient"""
    patient_id: str
    protocol_stats: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

    @computed_field
    def protocol_scores(self) -> Dict[str, float]:
        """Average performance scores per protocol"""
        return {
            proto_id: self.get_ewma_metrics(proto_id)
            for proto_id, stats in self.protocol_stats.items()
            if stats['sessions']
        }

    def get_ewma_metrics(self, protocol_id: str, alpha: float = 0.3) -> Optional[Dict[str, float]]:
        """
        Compute Exponential Weighted Moving Average (EWMA) for adherence, performance, and difficulty modulator change.

        Args:
            protocol_id (str): The protocol ID to filter sessions.
            alpha (float): The smoothing factor for EWMA (0 < alpha <= 1). Default is 0.3.

        Returns:
            Dict[str, float]: EWMA values for adherence, performance, and difficulty modulator change.
        """
        if protocol_id not in self.protocol_stats or not self.protocol_stats[protocol_id]['sessions']:
            return None  # No data for this protocol

        # Extract sessions for the given protocol
        sessions = sorted(self.protocol_stats[protocol_id]['sessions'], key=lambda s: s.timestamp)

        # Create a DataFrame for EWMA calculation
        df = pd.DataFrame({
            "timestamp": [s.timestamp for s in sessions],
            "adherence": [s.adherence for s in sessions],
            "performance_score": [s.performance_score for s in sessions],
            "difficulty_modulator": [s.difficulty_modulator for s in sessions]
        })

        # Compute EWMA
        df["ewma_adherence"] = df["adherence"].ewm(alpha=alpha).mean()
        df["ewma_performance"] = df["performance_score"].ewm(alpha=alpha).mean()

        # Compute difficulty modulator change
        df["difficulty_modulator_change"] = df["difficulty_modulator"].diff().fillna(0)
        df["ewma_difficulty_change"] = df["difficulty_modulator_change"].ewm(alpha=alpha).mean()

        # Return the latest EWMA values
        latest_values = df.iloc[-1][["ewma_adherence", "ewma_performance", "ewma_difficulty_change"]].to_dict()

        return {
            "ewma_adherence": latest_values["ewma_adherence"],
            "ewma_performance": latest_values["ewma_performance"],
            "ewma_difficulty_modulator_change": latest_values["ewma_difficulty_change"]
        }

    def add_sessions(self, sessions: List[Session]):
        """Update statistics with new sessions"""
        for session in sessions:
            proto_stats = self.protocol_stats.setdefault(session.protocol_id, {
                'sessions': [],
            })
            proto_stats['sessions'].append(session)

class PatientSessions(BaseModel):
    """Aggregates patient data across protocols"""
    protocol_id: str
    patient_stats: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

    @computed_field
    def average_performance(self) -> float:
        """Cross-patient average for this protocol"""
        total = sum(
            sum(s.performance_score for s in stats['sessions'])
            for stats in self.patient_stats.values()
        )
        count = sum(len(stats['sessions']) for stats in self.patient_stats.values())
        return total / count if count else 0.0

    @computed_field
    def average_adherence(self) -> float:
        """Cross-patient average for this protocol"""
        total = sum(
            sum(s.adherence for s in stats['sessions'])
            for stats in self.patient_stats.values()
        )
        count = sum(len(stats['sessions']) for stats in self.patient_stats.values())
        return total / count if count else 0.0

    def add_patient_sessions(self, patient_id: str, sessions: List[Session]):
        """Add patient's sessions to the aggregator"""
        relevant = [s for s in sessions if s.protocol_id == self.protocol_id]
        self.patient_stats[patient_id] = {
            'num_sessions': len(relevant),
            'total_duration': sum(s.duration for s in relevant),
            'sessions': relevant
        }

#########################
##### PATIENT MODEL #####
#########################

class StrokeInfo(BaseModel):
    # type: str
    # location: str
    heminegligence: int
    paretic_side: str
    onset_date: datetime  # Ensure this is a datetime object

    @field_validator('onset_date', mode='before')
    def parse_onset_date(cls, value):
        if isinstance(value, str):
            return datetime.fromisoformat(value)  # Parse ISO format strings
        return value

class ARAT(BaseModel):
    """Model for Action Research Arm Test (ARAT) scores."""
    grasp: float = Field(ge=0, le=18)          # 0-18
    grip: float = Field(ge=0, le=12)           # 0-12
    pinch: float = Field(ge=0, le=18)          # 0-18
    gross_movement: float = Field(ge=0, le=9)  # 0-9

    @property
    def total_score(self) -> float:
        """Calculate the total ARAT score."""
        return self.grasp + self.grip + self.pinch + self.gross_movement

    def deficit(self) -> Dict[str, float]:
        """Calculate deficits for each subscale."""
        return {
            "grasp": (18 - self.grasp) / 18,
            "grip": (12 - self.grip) / 12,
            "pinch": (18 - self.pinch) / 18,
            "gross_movement": (9 - self.gross_movement) / 9
        }

class MoCA(BaseModel):
    """Model for Montreal Cognitive Assessment (MoCA) scores."""
    visuospatial: float = Field(alias="VISUOSPATIAL", ge=0, le=5)  # 0-5
    naming: float = Field(alias="NAMING", ge=0, le=3)              # 0-3
    memory: float = Field(alias="MEMORY", ge=0, le=5)              # 0-5
    attention: float = Field(alias="ATTENTION", ge=0, le=6)        # 0-6
    language: float = Field(alias="LANGUAGE", ge=0, le=3)          # 0-3
    abstraction: float = Field(alias="ABSTRACTION", ge=0, le=2)    # 0-2
    delayed_recall: float = Field(alias="DELAYED_RECALL", ge=0, le=5)  # 0-5
    orientation: float = Field(alias="ORIENTATION", ge=0, le=6)    # 0-6

    class Config:
        populate_by_name = True

    @property
    def total_score(self) -> float:
        """Calculate the total MoCA score."""
        return (
            self.visuospatial +
            self.naming +
            self.memory +
            self.attention +
            self.language +
            self.abstraction +
            self.delayed_recall +
            self.orientation
        )

    def deficit(self) -> Dict[str, float]:
        """Calculate deficits for each subscale."""
        return {
            "visuospatial": (5 - self.visuospatial) / 5,
            "naming": (3 - self.naming) / 3,
            "memory": (5 - self.memory) / 5,
            "attention": (6 - self.attention) / 6,
            "language": (3 - self.language) / 3,
            "abstraction": (2 - self.abstraction) / 2,
            "delayed_recall": (5 - self.delayed_recall) / 5,
            "orientation": (6 - self.orientation) / 6
        }

class ClinicalScores(BaseModel):
    ARAT: ARAT
    MoCA: MoCA

class RecoveryProfile(BaseModel):
    group: str
    expected_adherence: float
    motor_trajectory: Dict[str, float]
    affective_baseline: Dict[str, float]

class Patient(BaseModel):
    """Realistic Patient Model"""
    patient_id: str
    demographics: Dict[str, Any]
    stroke_info: StrokeInfo
    clinical_scores: ClinicalScores
    recovery_profile: RecoveryProfile
    gaming_profile: Dict[str, Any]
    clinician_notes: Optional[str] = Field(
        default=None,
        description="Additional notes from the clinician about the patient"
    )
    tags: Optional[List[str]] = Field(
        default_factory=list,
        description="Tags for filtering protocols (e.g., 'severe_neglect', 'low_motivation')"
    )
    prescriptions: List[Prescription] = Field(default_factory=list)
    sessions: List[Session] = Field(default_factory=list)

    @computed_field
    def weekly_aggregator(self) -> WeeklyPrescription:
        aggregator = WeeklyPrescription(patient_id=self.patient_id)
        for prescription in self.prescriptions:  # Ensure handling multiple prescriptions
            aggregator.add_data(prescription, self.sessions)
        return aggregator

    @computed_field
    def protocol_aggregator(self) -> ProtocolSessions:
        aggregator = ProtocolSessions(patient_id=self.patient_id)
        aggregator.add_sessions(self.sessions)
        return aggregator

#########################
###### GLOBAL DATA ######
#########################

class ProtocolRegistry(BaseModel):
    """Global protocol registry with cross-patient stats"""
    protocols: Dict[str, Protocol] = Field(default_factory=dict)
    patient_aggregators: Dict[str, PatientSessions] = Field(default_factory=dict)

    def update_aggregators(self, patients: List[Patient]):
        """Refresh all cross-patient statistics"""
        for protocol in self.protocols.values():
            agg = self.patient_aggregators.setdefault(
                protocol.protocol_id,
                PatientSessions(protocol_id=protocol.protocol_id)
            )
            for patient in patients:
                if patient.sessions:
                    agg.add_patient_sessions(patient.patient_id, patient.sessions)
