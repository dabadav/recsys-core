# Patient Clinical Subscales
# - ARAT: GRASP, GRIP, PINCH, GROSS_MOVEMENT (higher scores = better function)
# - MoCA: VISUOSPATIAL, MEMORY, ATTENTION, LANGUAGE (higher scores = better cognition)

# Protocol Features
# - Motor: GRASPING, PINCHING, REACHING (0 or 1)
# - Cognitive: VISUALSPATIAL_PROCESSING, MEMORY_WM, ATTENTION, LANGUAGE (0 or 1)

# Scoring Logic
# - Motor Similarity: Sum of (deficit * relevance) for each motor subscale.
# - Cognitive Similarity: Sum of (deficit * relevance) for each cognitive subscale.
# - Total Score: Motor Similarity + Cognitive Similarity.
from models.patient import Patient
from models.protocol import Protocol
from typing import Callable, Tuple, Dict, List, Optional, Any

class ProtocolScorer:
    def __init__(self, patient: Patient, protocols: List[Protocol]):
        self.patient = patient
        self.protocols = filter_protocols(protocols, patient)

    def score_all_protocols(self, motor_weight: float, cognitive_weight: float) -> List[Dict]:
        """Score all protocols for the patient"""
        scored_protocols = []
        for protocol in self.protocols:
            # Compute motor similarity and contributions
            motor_similarity, motor_contributions = self._calculate_motor_similarity(protocol)
            motor_score = motor_similarity * motor_weight

            # Compute cognitive similarity and contributions
            cognitive_similarity, cognitive_contributions = self._calculate_cognitive_similarity(protocol)
            cognitive_score = cognitive_similarity * cognitive_weight

            # Total score
            total_score = motor_score + cognitive_score

            # Store results
            scored_protocols.append({
                **protocol.dict(),
                "score": total_score,
                "motor_contributions": motor_contributions,
                "cognitive_contributions": cognitive_contributions
            })

        # Sort by score (descending)
        return sorted(scored_protocols, key=lambda x: x["score"], reverse=True)

    def _calculate_motor_similarity(self, protocol: Protocol) -> Tuple[float, Dict]:
        """Calculate motor similarity and feature contributions using dot product"""
        arat_deficit = self.patient.clinical_scores.ARAT.deficit()
        motor_features = protocol.motor_features

        # Combine ARAT deficits and motor features into a single dictionary
        patient_motor_scores = {
            "grasp": arat_deficit["grasp"],
            "grip": arat_deficit["grip"],
            "pinch": arat_deficit["pinch"],
            "gross_movement": arat_deficit["gross_movement"]
        }

        # Protocol motor features (assuming protocol has a similar structure)
        protocol_motor_features = {
            "grasp": motor_features.grasping,
            "grip": motor_features.pronation_supination,
            "pinch": motor_features.pinching,
            "gross_movement": motor_features.reaching,
        }

        # Compute dot product (similarity) and feature contributions
        similarity = 0
        contributions = {}
        for feature in patient_motor_scores:
            patient_value = patient_motor_scores[feature]
            protocol_value = protocol_motor_features[feature]
            feature_contribution = patient_value * protocol_value
            similarity += feature_contribution
            contributions[feature] = feature_contribution

        return similarity, contributions

    def _calculate_cognitive_similarity(self, protocol: Protocol) -> Tuple[float, Dict]:
        """Calculate cognitive similarity and feature contributions using dot product"""
        moca_deficit = self.patient.clinical_scores.MoCA.deficit()
        cognitive_features = protocol.cognitive_features

        # Combine MoCA deficits and cognitive features into a single dictionary
        patient_cognitive_scores = {
            "memory": moca_deficit["memory"],
            "attention": moca_deficit["attention"],
            "language": moca_deficit["language"],
            "naming": moca_deficit["naming"],
            "abstraction": moca_deficit["abstraction"],
            "visuospatial": moca_deficit["visuospatial"],
            "delayed_recall": moca_deficit["delayed_recall"],
            "orientation": moca_deficit["orientation"]
        }

        # Protocol cognitive features (assuming protocol has a similar structure)
        protocol_cognitive_features = {
            "memory": cognitive_features.memory_wm,
            "attention": cognitive_features.attention,
            "language": cognitive_features.semantic_processing,
            "naming": cognitive_features.memory_semantic,
            "abstraction": cognitive_features.symbolic_understanding,
            "visuospatial": cognitive_features.visual_language,
            "delayed_recall": cognitive_features.daily_living_activity,
            "orientation": cognitive_features.visualspatial_processing_awareness_neglect
        }

        # Compute dot product (similarity) and feature contributions
        similarity = 0
        contributions = {}
        for feature in patient_cognitive_scores:
            patient_value = patient_cognitive_scores[feature]
            protocol_value = protocol_cognitive_features[feature]
            feature_contribution = patient_value * protocol_value
            similarity += feature_contribution
            contributions[feature] = feature_contribution

        return similarity, contributions

def filter_protocols(protocols: List[Protocol], patient: Patient) -> List[Protocol]:
    """Filter protocols based on patient tags and contraindications."""
    filtered_protocols = []
    for protocol in protocols:
        # Check if any contraindication matches a patient tag
        contraindicated = any(
            tag in protocol.safety_constraints.contraindications
            for tag in patient.tags
        )
        if not contraindicated:
            filtered_protocols.append(protocol)
    return filtered_protocols