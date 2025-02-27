from pydantic import BaseModel, computed_field
from typing import Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Optional
from session import WeeklyPlan

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
            "grasp": 18 - self.grasp,
            "grip": 12 - self.grip,
            "pinch": 18 - self.pinch,
            "gross_movement": 9 - self.gross_movement
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
        allow_population_by_field_name = True  # Allow aliases for field names

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
            "visuospatial": 5 - self.visuospatial,
            "naming": 3 - self.naming,
            "memory": 5 - self.memory,
            "attention": 6 - self.attention,
            "language": 3 - self.language,
            "abstraction": 2 - self.abstraction,
            "delayed_recall": 5 - self.delayed_recall,
            "orientation": 6 - self.orientation
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
    patient_id: str
    demographics: Dict[str, Any]
    stroke_info: StrokeInfo
    clinical_scores: ClinicalScores
    recovery_profile: RecoveryProfile
    gaming_profile: Dict[str, Any]
    clinician_notes: Optional[str] = Field(
        default=None,
        description="Free-text notes from the clinician about the patient"
    )
    tags: Optional[List[str]] = Field(
        default_factory=list,
        description="Tags for filtering protocols (e.g., 'severe_neglect', 'low_motivation')"
    )
    treatment_history: List[WeeklyPlan] = Field(
        default_factory=list,
        description="Historical weekly plans with prescriptions and outcomes"
    )

    @computed_field
    def current_plan(self) -> Optional[WeeklyPlan]:
        """Get the active weekly plan"""
        return self.treatment_history[-1] if self.treatment_history else None