# Mock patient database
patients = {
    "P001": {
        # Demographics
        "ID": "P001",
        "AGE": 58,
        "GENDER": "Male",
        "HANDEDNESS": "Right",

        # Stroke Information
        "STROKE_TYPE": "Ischemic",  # Ischemic or Hemorrhagic
        "STROKE_LOCATION": "Left MCA",  # Affected brain region
        "TIME_SINCE_STROKE": "3 months",  # Time since stroke event

        # Clinical Subscales
        "ARAT": {
            "GRASP": 12,  # Action Research Arm Test (0-18)
            "GRIP": 8,           # (0-12)
            "PINCH": 10,         # (0-18)
            "GROSS_MOVEMENT": 9  # (0-9)
        },
        "MOCA": {
            "VISUOSPATIAL": 4,  # Montreal Cognitive Assessment (0-5)
            "NAMING": 3,         # (0-3)
            "MEMORY": 2,         # (0-5)
            "ATTENTION": 5,      # (0-6)
            "LANGUAGE": 2,       # (0-3)
            "ABSTRACTION": 1,    # (0-2)
            "DELAYED_RECALL": 3, # (0-5)
            "ORIENTATION": 6     # (0-6)
        },

        # Video Game Experience
        "GAME_EXPERIENCE": 3,  # 0-5 scale (0 = none, 5 = expert)

        # Additional Notes (for future use)
        "NOTES": "Prefers gamified activities, mild neglect in left visual field."
    }
}

# Session database
sessions = [
    {
        "SESSION_ID": "S001",
        "PATIENT_ID": "P001",
        "PROTOCOL_ID": 200,
        "DATE": "2023-10-25",
        "DURATION_PRESCRIBED": 300,  # in seconds
        "DURATION_PERFORMED": 300,
        "KINEMATICS": {
            "SMOOTHNESS": 0.8,  # 0-1 scale
            "ACCURACY": 0.7      # 0-1 scale
        },
        "PERFORMANCE": {
            "PERFORMANCE": 0.7,
            "DIFFICULTY_MODULATOR": 0.8,
        },
        "AFFECTIVE_SLIDERS": {
            "MOOD": 4,       # 1-5 scale
            "MOTIVATION": 3  # 1-5 scale
        }
    }
]

# Activity database
activities = [
    {
        "NAME": "Blobs",
        "ID": 214,
        "TYPE": "motor",
        "DIFFICULTY_COGNITIVE": "high",
        "DIFFICULTY_MOTOR": "high",
        "BALANCED": "balanced CM",
        "BODY_PART_FINGER": 1,
        "BODY_PART_WRIST": 0,
        "BODY_PART_ARM": 0,
        "BODY_PART_SHOULDER": 0,
        "BODY_PART_TRUNK": 0,
        "REACHING": 0,
        "GRASPING": 0,
        "PINCHING": 1,
        "PRONATION_SUPINATION": 0,
        "RANGE_OF_MOTION_H": 0,
        "RANGE_OF_MOTION_V": 0,
        "PROCESSING_SPEED": 1,
        "ATTENTION": 1,
        "LANGUAGE": 0,
        "VISUALSPATIAL_PROCESSING": 1,
        "COORDINATION": 1,
        "MEMORY_WM": 1,
        "MEMORY_SEMANTIC": 0,
        "MATH": 1,
        "DAILY_LIVING_ACTIVITY": 1,
        "SYMBOLIC_UNDERSTANDING": 0,
        "SEMANTIC_PROCESSING": 0
    },
    {
        "NAME": "Twister",
        "ID": 223,
        "TYPE": "balanced",
        "DIFFICULTY_COGNITIVE": "high",
        "DIFFICULTY_MOTOR": "high",
        "BALANCED": "balanced CM",
        "BODY_PART_FINGER": 1,
        "BODY_PART_WRIST": 0,
        "BODY_PART_ARM": 0,
        "BODY_PART_SHOULDER": 0,
        "BODY_PART_TRUNK": 0,
        "REACHING": 1,
        "GRASPING": 1,
        "PINCHING": 1,
        "PRONATION_SUPINATION": 0,
        "RANGE_OF_MOTION_H": 0,
        "RANGE_OF_MOTION_V": 0,
        "PROCESSING_SPEED": 1,
        "ATTENTION": 1,
        "LANGUAGE": 0,
        "VISUALSPATIAL_PROCESSING": 1,
        "COORDINATION": 1,
        "MEMORY_WM": 1,
        "MEMORY_SEMANTIC": 0,
        "MATH": 0,
        "DAILY_LIVING_ACTIVITY": 1,
        "SYMBOLIC_UNDERSTANDING": 0,
        "SEMANTIC_PROCESSING": 0
    },
]