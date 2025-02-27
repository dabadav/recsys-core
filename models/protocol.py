# models/protocol.py
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from enum import Enum

class ProtocolType(str, Enum):
    MOTOR = "motor"
    COGNITIVE = "cognitive"
    ASSESSMENT = "assessment"
    BALANCED = "balanced"

class BodyTargets(BaseModel):
    arm: int = 0
    shoulder: int = 0
    wrist: int = 0
    finger: int = 0
    trunk: int = 0

class Gamification(BaseModel):
    type: str  # AR, VR, controller-based, etc.
    feedback_modes: List[str]
    difficulty_scaling: bool = False

class SafetyConstraints(BaseModel):
    """Safety constraints for the protocol."""
    max_duration: int = Field(
        gt=0,
        description="Maximum duration of the protocol in seconds"
    )
    contraindications: List[str] = Field(
        default_factory=list,
        description="Conditions that make this protocol unsuitable"
    )
    max_daily_frequency: int = Field(
        default=1,
        ge=1,
        description="Maximum number of times this protocol can be performed in a day"
    )
    min_rest_period: int = Field(
        default=0,
        ge=0,
        description="Minimum rest period (in days) required after this protocol"
    )

class MotorFeatures(BaseModel):
    reaching: bool
    grasping: bool
    pinching: bool
    pronation_supination: bool
    range_of_motion_h: str = Field(..., pattern='^(low|mid|high)$')
    range_of_motion_v: str = Field(..., pattern='^(low|mid|high)$')

class CognitiveFeatures(BaseModel):
    processing_speed: bool
    attention: bool
    visual_language: bool
    visualspatial_processing_awareness_neglect: bool
    coordination: bool
    memory_wm: bool
    memory_semantic: bool
    math: bool
    daily_living_activity: bool
    symbolic_understanding: bool
    semantic_processing: bool

class Protocol(BaseModel):
    """A RGS rehabilitation protocol."""
    protocol_id: str
    name: str
    description: str = Field(
        default="",
        description="Detailed description of the protocol"
    )
    difficulty_params: Dict[str, float] = Field(default_factory=dict)

    type: ProtocolType
    difficulty_cognitive: str = Field(..., pattern='^(low|mid|high)$')
    difficulty_motor: str = Field(..., pattern='^(low|mid|high)$')
    body_targets: BodyTargets

    motor_features: MotorFeatures
    cognitive_features: CognitiveFeatures

    cognitive_demand: float
    gamification: Optional[Gamification] = None
    safety_constraints: SafetyConstraints

    # Example protocol for documentation
    class Config:
        schema_extra = {
            "example": {
                "protocol_id": "PR200",
                "name": "VR Arm Training",
                "type": "motor",
                "difficulty": "medium",
                "body_targets": {"arm": 1, "shoulder": 1},
                "cognitive_demand": 0.3,
                "gamification": {
                    "type": "AR",
                    "feedback_modes": ["visual", "haptic"]
                },
                "safety_constraints": {
                    "max_duration": 25,
                    "contraindications": ["severe_neglect"]
                },
                "description": "A VR-based protocol for upper limb rehabilitation, focusing on arm and shoulder movements."
            }
        }