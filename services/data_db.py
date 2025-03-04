# services/data_db.py
from sqlmodel import SQLModel, Session, Field, Index, create_engine, select, Relationship
from enum import Enum
from datetime import datetime, date
from typing import List, Dict, Optional, Any
from pydantic import computed_field

# from models.patient import ClinicalScores
# import pandas as pd
# import numpy as np

# --------------------------
#  Enums for Validation
# --------------------------
class RecordingKey(str, Enum):
    SCORE = "score"
    TOTAL_ERRORS = "totalErrors"
    TOTAL_SUCCESS = "totalSuccess"
    SESSION_DURATION = "sessionDuration(seconds)"

# --------------------------
#  Core Database Models
# --------------------------
# ----- Patient Model -----
class Patient(SQLModel, table=True):
    __tablename__ = "patient"

    patient_id: int = Field(primary_key=True)
    hospital_id: int
    patient_user: str = Field(max_length=40)
    paretic_side: str = Field(sa_column_kwargs={"comment": "NONE/LEFT/RIGHT"})
    upper_extremity_to_train: str = Field(sa_column_kwargs={"comment": "BOTH/LEFT/RIGHT"})
    hand_raising_capacity: str = Field(sa_column_kwargs={"comment": "NONE/LOW/MEDIUM/HIGH"})
    cognitive_function_level: str
    has_heminegligence: bool
    gender: str = Field(max_length=10)
    skin_color: str = Field(max_length=20)
    birth_date: datetime
    videogame_exp: int
    computer_exp: int
    comments: Optional[str] = Field(max_length=400)
    ptn_height_cm: int
    arm_size_cm: int

    # Relationships
    prescriptions: List["Prescription"] = Relationship(back_populates="patient")

# # ----- Prescription Model -----
class Prescription(SQLModel, table=True):
    __tablename__ = "prescription_plus"

    prescription_id: int = Field(primary_key=True)
    patient_id: int = Field(foreign_key="patient.patient_id")
    protocol_id: int
    starting_date: datetime
    ending_date: Optional[datetime]
    weekday: str = Field(sa_column_kwargs={"comment": "Weekday schedule"})
    session_duration: int
    ar_mode: str

    # Relationships
    patient: Patient = Relationship(back_populates="prescriptions")
    sessions: List["PatientSession"] = Relationship(back_populates="prescription")

# # ----- Session Model -----
class PatientSession(SQLModel, table=True):
    __tablename__ = "session_plus"

    session_id: int = Field(primary_key=True)
    prescription_id: int = Field(foreign_key="prescription_plus.prescription_id")
    starting_date: datetime
    ending_date: datetime
    status: str = Field(max_length=20)
    platform: str = Field(max_length=20)
    device: str = Field(max_length=20)
    session_log_parsed: bool

    # Relationships
    prescription: Prescription = Relationship(back_populates="sessions")
    recordings: List["SessionRecording"] = Relationship(back_populates="session")
    # difficulty_modulators: List["DifficultyModulator"] = Relationship(back_populates="session")
    # performance_estimators: List["PerformanceEstimator"] = Relationship(back_populates="session")

    @computed_field
    @property
    def score(self) -> Optional[int]:
        return next((r.recording_value for r in self.recordings
                   if r.recording_key == RecordingKey.SCORE), None)

    @computed_field
    @property
    def duration(self) -> Optional[int]:
        duration_value = next(
            (r.recording_value for r in self.recordings
            if r.recording_key == RecordingKey.SESSION_DURATION),
            None
        )
        return int(duration_value) if duration_value is not None else None

    @computed_field
    @property
    def adherence(self) -> Optional[int]:
        return self.duration / self.prescription.session_duration

class SessionRecording(SQLModel, table=True):
    __tablename__ = "recording_plus"

    recording_id: int = Field(primary_key=True)
    session_id: int = Field(foreign_key="session_plus.session_id")
    protocol_id: int
    recording_key: str
    recording_value: int

    session: PatientSession = Relationship(back_populates="recordings")

# class DifficultyModulator(SQLModel, table=True):
#     __tablename__ = "difficulty_modulators_plus"

#     difficulty_modulators_id: int = Field(primary_key=True)
#     patient_id: int = Field(foreign_key="patient.patient_id")
#     session_id: int = Field(foreign_key="session_plus.session_id")
#     protocol_id: int
#     game_mode: str
#     seconds_from_start: int
#     parameter_key: str
#     parameter_value: float

#     # session: Optional[Session] = Relationship(back_populates="difficulty_modulators")

# class PerformanceEstimator(SQLModel, table=True):
#     __tablename__ = "performance_estimators_plus"

#     id: int = Field(primary_key=True)
#     session_id: int = Field(foreign_key="session_plus.session_id")
#     protocol_id: int
#     game_mode: str
#     seconds_from_start: int
#     parameter_key: str
#     parameter_value: float

#     session: Optional[Session] = Relationship(back_populates="performance_estimators")

# class EmotionalQuestionPatient(SQLModel, table=True):
#     __tablename__ = "emotional_question_patient"

#     id: int = Field(primary_key=True)
#     patient_id: int = Field(foreign_key="patient.patient_id")

# class EmotionalAnswer(SQLModel, table=True):
#     __tablename__ = "emotional_answer"

#     id: int = Field(primary_key=True)
#     emotional_question_patient_id: int = Field(foreign_key="emotional_question_patient.emotional_question_patient_id")
#     emotional_question_patient: EmotionalQuestionPatient = Relationship()


#     @property
#     def patient_id(self) -> int:
#         return self.emotional_question_patient.patient_id

# class CommitmentQuestionPatient(SQLModel, table=True):
#     __tablename__ = "commitment_question_patient"

#     id: int = Field(primary_key=True)
#     patient_id: int = Field(foreign_key="patient.patient_id")


# class CommitmentAnswer(SQLModel, table=True):
#     __tablename__ = "commitment_answer"
#     id: int = Field(default=None, primary_key=True)
#     patient_id: int = Field(foreign_key="patient.patient_id")
#     value: float  # Example: Commitment score
#     creation_time: date
#     succeed_time: date

#     commitmnent_question_patient_id: int = Field(foreign_key="commitment_question_patient.commitment_question_patient_id")
#     commitmnent_question_patient: CommitmentQuestionPatient = Relationship()
    
#     @property
#     def patient_id(self) -> int:
#         return self.commitmnent_question_patient.patient_id

# --------------------------
#  Aggregators
# --------------------------
# class ProtocolSessions(BaseModel):
#     """Aggregates protocol performance for a single patient"""
#     patient_id: int
#     protocol_dict: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

#     def add_sessions(self, sessions: List[PatientSession]):
#         """Update statistics with new sessions"""
#         for session in sessions:
#             proto_stats = self.protocol_dict.setdefault(session.protocol_id, {
#                 'sessions': [],
#             })
#             proto_stats['sessions'].append(session)

#     @computed_field
#     def get_metrics(self) -> Dict[str, float]:
#         """Average performance scores per protocol"""
#         return {
#             proto_id: self.get_ewma_metrics(proto_id)
#             for proto_id, stats in self.protocol_stats.items()
#             if stats['sessions']
#         }

#     def get_ewma_metrics(self, protocol_id: str, alpha: float = 0.3) -> Optional[Dict[str, float]]:
#         """
#         Compute Exponential Weighted Moving Average (EWMA) for adherence, performance, and difficulty modulator change.

#         Args:
#             protocol_id (str): The protocol ID to filter sessions.
#             alpha (float): The smoothing factor for EWMA (0 < alpha <= 1). Default is 0.3.

#         Returns:
#             Dict[str, float]: EWMA values for adherence, performance, and difficulty modulator change.
#         """
#         if protocol_id not in self.protocol_stats or not self.protocol_stats[protocol_id]['sessions']:
#             return None  # No data for this protocol

#         # Extract sessions for the given protocol
#         sessions = sorted(self.protocol_stats[protocol_id]['sessions'], key=lambda s: s.starting_date)

#         # Create a DataFrame for EWMA calculation
#         df = pd.DataFrame({
#             "timestamp": [s.starting_date for s in sessions],
#             "adherence": [s.adherence for s in sessions],
#             "score": [s.performance_score for s in sessions]
#         })

#         # Compute EWMA
#         df["ewma_adherence"] = df["adherence"].ewm(alpha=alpha).mean()
#         df["ewma_performance"] = df["score"].ewm(alpha=alpha).mean()

#         # Return the latest EWMA values
#         latest_values = df.iloc[-1][["ewma_adherence", "ewma_performance"]].to_dict()

#         return {
#             "ewma_adherence": latest_values["ewma_adherence"],
#             "ewma_performance": latest_values["ewma_performance"]
#         }

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

DB_USER="db_readOnly_prod"
DB_PASS="12345aA."
DB_HOST="rgsweb.eodyne.com"
DB_NAME="global_prod"

# Create the engine
connection_string = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"
engine = create_engine(connection_string, echo=False)

# Example usage
if __name__ == "__main__":
    create_db_and_tables()
    