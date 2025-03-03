from sqlmodel import SQLModel, Field, Session, create_engine, select
from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, Field, field_validator, computed_field
from typing import List, Dict, Optional, Any
import pandas as pd
import numpy as np

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

# Define the SQLModel (which also acts as a Pydantic model)
class PatientSQL(SQLModel, table=True):
    __tablename__ = "patient"

    patient_id: int = Field(default=None, primary_key=True)
    hospital_id: int
    patient_user: str
    password: str
    creation_time: datetime
    delete_time: Optional[datetime] = None
    name: str
    surname1: str
    surname2: str
    paretic_side: str
    upper_extremity_to_train: str
    hand_raising_capacity: str
    cognitive_function_level: str
    has_heminegligence: int
    gender: str
    skin_color: str
    birth_date: str
    videogame_exp: int
    computer_exp: int
    comments: Optional[str] = None
    ptn_height_cm: int
    arm_size_cm: int
    demo: int
    version: int

class Session(BaseModel):
    """Metrics collected during a single therapy session"""
    session_id: str
    patient_id: str
    protocol_id: str
    prescription_id: str
    timestamp: datetime

    duration: float = Field(..., ge=0, description="Time spent in session (seconds)")
    difficulty_modulator: float = Field(..., ge=0, le=1, description="DM value for this session (0-1 scale)")
    performance_score: float = Field(..., ge=0, le=1, description="Performance metric")

    # Relationship
    _prescription: Optional['Prescription'] = None  # Backref

    @computed_field
    def prescribed_duration(self) -> float:
        """Get target duration from linked prescription"""
        return self._prescription.prescribed_duration if self._prescription else 0.0

    @computed_field
    def adherence(self) -> float:
        """Session-specific duration adherence"""
        if self.prescribed_duration == 0:
            return 0.0
        return min(self.duration / self.prescribed_duration, 1.0)

class Prescription(BaseModel):
    """Protocol planned for a weekly schedule"""
    prescription_id: str
    patient_id: str
    protocol_id: str
    start_date: date
    end_date: date
    weekday: str
    prescribed_duration: int

    # Prescription transparency
    decision_scores: Dict[str, float] = Field(
        default_factory=dict,
        description="Scores that influenced this prescription (e.g., motor_score=0.8)"
    )
    explanation: str = Field(
        default="",
        description="Clinical reasoning for this prescription"
    )

    # Recommended difficulty
    prescribed_difficulty: Optional[float] = Field(None, ge=0, le=1)

class StrokeInfo(BaseModel):
    type: str
    location: str
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

# PatientRepository class to handle patient-related operations
class PatientRepository:
    def __init__(self, engine):
        self.engine = engine

    def get_patient_by_id(self, patient_id: int) -> Optional[PatientSQL]:
        """Retrieve a patient by their ID."""
        with Session(self.engine) as session:
            patient = session.exec(select(PatientSQL).where(PatientSQL.patient_id == patient_id)).first()
            return patient

    def get_all_patients(self) -> List[PatientSQL]:
        """Retrieve all patients."""
        with Session(self.engine) as session:
            patients = session.exec(select(PatientSQL)).all()
            return patients

    def get_patients_by_id_list(self, patient_ids: List[int]) -> List[PatientSQL]:
        """Retrieve multiple patients by a list of IDs."""
        with Session(self.engine) as session:
            patients = session.exec(select(PatientSQL).where(PatientSQL.patient_id.in_(patient_ids))).all()
            return patients

    def transform_to_realistic_patient(db_patient: PatientSQL) -> Patient:
        """Transform a database Patient object into a RealisticPatient model."""

        # Map demographics
        demographics = {
            "gender": db_patient.gender,
            "skin_color": db_patient.skin_color,
            "birth_date": db_patient.birth_date,
            "height_cm": db_patient.ptn_height_cm,
            "arm_size_cm": db_patient.arm_size_cm,
        }

        # Map stroke info
        stroke_info = StrokeInfo(
            upper_extremity_to_train=db_patient.upper_extremity_to_train,
            hand_raising_capacity=db_patient.hand_raising_capacity,
            cognitive_function_level=db_patient.cognitive_function_level,
            heminegligence=bool(db_patient.has_heminegligence),
            paretic_side=db_patient.paretic_side,
        )

        # Initialize clinical scores
        clinical_scores = ClinicalScores()

        # Initialize recovery profile
        recovery_profile = RecoveryProfile()

        # Map gaming profile
        gaming_profile = {
            "videogame_experience": bool(db_patient.videogame_exp),
            "computer_experience": bool(db_patient.computer_exp),
        }

        # Create the RealisticPatient object
        realistic_patient = Patient(
            patient_id=str(db_patient.patient_id),
            demographics=demographics,
            stroke_info=stroke_info,
            clinical_scores=clinical_scores,
            recovery_profile=recovery_profile,
            gaming_profile=gaming_profile,
            clinician_notes=db_patient.comments,
            tags=[],  # Populated later
            prescriptions=[],  #
            sessions=[],  #
        )

        return realistic_patient

# Test
db_user = "db_readOnly_prod"
db_password = "12345aA."
db_host = "rgsweb.eodyne.com"
db_name = "global_prod"

# Create the engine
connection_string = f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}"
engine = create_engine(connection_string)

# Create the tables
SQLModel.metadata.create_all(engine)

# Example usage
if __name__ == "__main__":
    # Initialize the repository
    repository = PatientRepository(engine)
