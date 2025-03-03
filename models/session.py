from pydantic import BaseModel, Field, computed_field
from typing import List, Dict, Optional
from datetime import datetime, date

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
