import random
import uuid
from datetime import datetime
from collections import defaultdict


# =====================================================
# PARÁMETROS POR OBJETIVO
# =====================================================

GOAL_PARAMS = {

    "ganar_musculo": {
        "focus":        {"sets": 4, "reps": (8, 12),  "intensity": 0.75},
        "compensation": {"sets": 3, "reps": (12,15),  "intensity": 0.60},
        "metabolic":    {"sets": 3, "reps": (15,20),  "intensity": 0.55},
    },

    "perder_grasa": {
        "focus":        {"sets": 4, "reps": (10,15),  "intensity": 0.70},
        "compensation": {"sets": 3, "reps": (15,20),  "intensity": 0.55},
        "metabolic":    {"sets": 4, "reps": (20,30),  "intensity": 0.50},
    },

    "resistencia": {
        "focus":        {"sets": 4, "reps": (15,25),  "intensity": 0.60},
        "compensation": {"sets": 3, "reps": (20,30),  "intensity": 0.50},
        "metabolic":    {"sets": 4, "reps": (25,40),  "intensity": 0.45},
    },

    "tonificar": {
        "focus":        {"sets": 3, "reps": (10,15),  "intensity": 0.65},
        "compensation": {"sets": 3, "reps": (15,20),  "intensity": 0.55},
        "metabolic":    {"sets": 4, "reps": (18,25),  "intensity": 0.50},
    },

    "movilidad": {
        "focus":        {"sets": 3, "reps": (8,12),   "intensity": 0.40},
        "compensation": {"sets": 3, "reps": (10,15),  "intensity": 0.35},
        "metabolic":    {"sets": 3, "reps": (12,20),  "intensity": 0.30},
    }
}


# =====================================================
# MOTOR PRO DINÁMICO
# =====================================================

class RoutineEngineDynamic:

    def __init__(self, exercises):
        self.exercises = exercises
        self.used_exercises = set()
        self.fatigue_score = 0.0
        self.training_days = 7


    # =====================================================
    # CONSTRUCCIÓN DINÁMICA DE LA SEMANA
    # =====================================================

    def build_week_structure(self, training_days):

        focus_days = max(2, round(training_days * 0.4))
        compensation_days = max(1, round(training_days * 0.2))
        metabolic_days = training_days - focus_days - compensation_days

        structure = (
            ["focus"] * focus_days +
            ["compensation"] * compensation_days +
            ["metabolic"] * metabolic_days
        )

        random.shuffle(structure)
        return structure


    # =====================================================
    # MODELO DE FATIGA AGRESIVO
    # =====================================================

    def adjust_intensity(self, base_intensity):

        if self.fatigue_score > 0.75:
            return base_intensity * 0.75
        elif self.fatigue_score > 0.50:
            return base_intensity * 0.85
        elif self.fatigue_score > 0.30:
            return base_intensity * 0.90
        elif self.fatigue_score > 0.15:
            return base_intensity * 0.95
        else:
            return base_intensity


    # =====================================================
    # SCORING PROBABILÍSTICO
    # =====================================================

    def score_exercise(self, exercise, goal, day_type):

        score = 1.0

        # Peso por objetivo
        if goal == "ganar_musculo":
            if exercise["exerciseType"] == "fuerza":
                score *= 3
        elif goal == "perder_grasa":
            if exercise["exerciseType"] in ["cardio", "pliometría"]:
                score *= 3
        elif goal == "resistencia":
            if exercise["exerciseType"] in ["cardio", "core/abdomen"]:
                score *= 3
        elif goal == "tonificar":
            if exercise["exerciseType"] in ["fuerza", "core/abdomen"]:
                score *= 2
        elif goal == "movilidad":
            if exercise["exerciseType"] == "movilidad":
                score *= 4

        # Ajustes por tipo de día
        if day_type == "compensation":
            if exercise["exerciseType"] in ["movilidad", "core/abdomen", "equilibrio"]:
                score *= 3
            else:
                score *= 0.5

        if day_type == "metabolic":
            if exercise["exerciseType"] in ["cardio", "pliometría"]:
                score *= 4
            else:
                score *= 0.7

        # Penalización por fatiga
        score *= max(0.3, 1 - self.fatigue_score)

        return score


    # =====================================================
    # PRESCRIPCIÓN CON VOLUMEN ADAPTATIVO
    # =====================================================

    def prescribe(self, goal, day_type):

        params = GOAL_PARAMS[goal][day_type]

        # Ajustar volumen según días entrenados
        volume_modifier = 7 / self.training_days

        sets = max(2, int(params["sets"] * volume_modifier))
        reps = random.randint(params["reps"][0], params["reps"][1])

        intensity = self.adjust_intensity(params["intensity"])

        if goal == "movilidad":
            return {
                "sets": sets,
                "reps": reps,
                "intensity_percent": None,
                "tempo": "controlado"
            }

        return {
            "sets": sets,
            "reps": reps,
            "intensity_percent": round(intensity * 100)
        }


    # =====================================================
    # GENERAR DÍA
    # =====================================================

    def generate_day(self, goal, day_type, day_number):

        exercises_for_day = []
        available = [e for e in self.exercises if e["id"] not in self.used_exercises]
        bodyparts_today = set()

        attempts = 0
        exercise_order = 1

        while len(exercises_for_day) < 5 and attempts < 50:

            if not available:
                available = self.exercises.copy()

            weights = [self.score_exercise(e, goal, day_type) for e in available]
            exercise = random.choices(available, weights=weights, k=1)[0]

            if exercise["bodyPart"] in bodyparts_today and attempts < 25:
                attempts += 1
                continue

            prescription = self.prescribe(goal, day_type)

            # Asegurar que exerciseBenefit sea lista
            benefit = exercise.get("exerciseBenefit", [])
            if isinstance(benefit, str):
                benefit = [benefit]

            exercise_instance = {
                "exercise_instance_id": str(uuid.uuid4()),
                "order": exercise_order,  # 🔥 NUEVO
                "exercise_id": exercise["id"],
                "name": exercise["name"],
                "img_static": exercise.get("img_static"),
                "img_animated": exercise.get("img_animated"),
                "bodyPart": exercise["bodyPart"],
                "exerciseType": exercise["exerciseType"],
                "instructions": exercise.get("instructions", []),
                "exerciseBenefit": benefit,
                "prescription": prescription,

                "status": "pending",
                "liked": None,
                "completed_at": None
            }

            exercises_for_day.append(exercise_instance)

            self.used_exercises.add(exercise["id"])
            bodyparts_today.add(exercise["bodyPart"])
            available.remove(exercise)

            exercise_order += 1
            attempts += 1

        self.fatigue_score += 0.15 + (self.training_days * 0.01)
        self.fatigue_score = min(self.fatigue_score, 1.0)

        # 🔥 Determinar focus_area automáticamente
        if day_type == "focus":
            focus_area = random.choice(["upper", "lower"])
        else:
            focus_area = "full_body"

        day_object = {
            "day_number": day_number,
            "type": day_type,
            "focus_area": focus_area,  # 🔥 NUEVO
            "status": "pending",
            "completed_at": None,
            "exercises": exercises_for_day
        }

        return day_object


    # =====================================================
    # GENERAR SEMANA COMPLETA
    # =====================================================
    def generate_week(self, goal, training_days=4, year=None, week=None, year_week=None):

        if training_days < 4 or training_days > 7:
            raise ValueError("training_days debe estar entre 4 y 7")

        self.training_days = training_days
        self.used_exercises = set()
        self.fatigue_score = 0.0

        week_structure = self.build_week_structure(training_days)

        week_days = []

        for i, day_type in enumerate(week_structure):
            day = self.generate_day(goal, day_type, i + 1)
            week_days.append(day)

        week_object = {
            "days": week_days
        }

        return week_object