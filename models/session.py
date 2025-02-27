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

    duration: float = Field(..., ge=0, description="Time spent in session (minutes)")
    difficulty_modulator: float = Field(..., ge=0, le=1, description="DM value for this session (0-1 scale)")
    performance_score: float = Field(..., ge=0, le=1, description="Performance metric")

    # Relationship
    _prescription: Optional['Prescription'] = None  # Backref

    @computed_field
    def prescribed_duration(self) -> float:
        """Get target duration from linked prescription"""
        return self._prescription.target_duration if self._prescription else 0.0

    @computed_field
    def adherence(self) -> float:
        """Session-specific duration adherence"""
        if self.prescribed_duration == 0:
            return 0.0
        return min(self.actual_duration / self.prescribed_duration, 1.0)

class Prescription(BaseModel):
    """Protocol planned for a weekly schedule"""
    prescription_id: str
    patient_id: str
    protocol_id: str
    start_date: date
    end_date: date
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

class ProtocolProgress(BaseModel):
    """Temporal metrics for a specific protocol"""
    protocol_id: str
    sessions: List[SessionMetrics] = Field(default_factory=list)

    @computed_field
    def ewma_dm(self, alpha: float = 0.3) -> float:
        """Exponentially weighted moving average of difficulty modulators"""
        if not self.sessions:
            return 0.0
        ewma = self.sessions[0].difficulty_modulator
        for session in self.sessions[1:]:
            ewma = alpha * session.difficulty_modulator + (1 - alpha) * ewma
        return ewma

    @computed_field
    def total_adherence(self) -> float:
        """Average adherence across all sessions"""
        if not self.sessions:
            return 0.0
        return sum(s.adherence for s in self.sessions) / len(self.sessions)

class WeeklyPlanQuality(BaseModel):
    """Computed metrics about plan effectiveness"""
    average_adherence: float = Field(..., ge=0, le=1)
    difficulty_effectiveness: Dict[str, float] = Field(
        default_factory=dict,
        description="Correlation between difficulty modulators and performance"
    )
    protocol_effectiveness: Dict[str, float] = Field(
        default_factory=dict,
        description="Performance improvement per protocol"
    )
    time_deviation: float = Field(
        ...,
        description="Percentage deviation from prescribed time"
    )

class WeeklyPlan(BaseModel):
    """Complete weekly plan with prescriptions and outcomes"""
    week_start: date
    prescriptions: List[PrescribedProtocol] = Field(
        default_factory=list,
        description="Planned protocol prescriptions"
    )
    quality_metrics: Optional[WeeklyPlanQuality] = Field(
        None,
        description="Computed after week completion"
    )

    @computed_field
    def total_prescribed_time(self) -> float:
        """Total minutes prescribed for all protocols"""
        return sum(p.target_duration * p.target_sessions for p in self.prescriptions)

    @computed_field
    def total_performed_time(self) -> float:
        """Total minutes actually performed"""
        return sum(s.actual_duration for p in self.prescriptions for s in p.sessions)

    def calculate_quality(self) -> WeeklyPlanQuality:
        """Compute quality metrics for the weekly plan"""
        # Implementation example
        total_adherence = sum(
            s.adherence for p in self.prescriptions for s in p.sessions
        ) / len(self.prescriptions) if self.prescriptions else 0.0

        return WeeklyPlanQuality(
            average_adherence=total_adherence,
            time_deviation=(self.total_performed_time - self.total_prescribed_time)
                            / self.total_prescribed_time,
            # Additional metrics calculations would go here
        )