import random
import uuid
from collections import defaultdict


# =====================================================
# PARÁMETROS BASE POR OBJETIVO
# =====================================================

GOAL_PARAMS = {
    "ganar_musculo": {
        "focus":        {"sets": (3, 4), "reps": (6, 12),  "intensity": (68, 82)},
        "compensation": {"sets": (2, 3), "reps": (10, 15), "intensity": (55, 70)},
        "metabolic":    {"sets": (2, 3), "reps": (12, 20), "intensity": (50, 65)},
    },
    "perder_grasa": {
        "focus":        {"sets": (3, 4), "reps": (8, 15),  "intensity": (60, 75)},
        "compensation": {"sets": (2, 3), "reps": (12, 20), "intensity": (50, 65)},
        "metabolic":    {"sets": (3, 4), "reps": (15, 30), "intensity": (45, 60)},
    },
    "resistencia": {
        "focus":        {"sets": (3, 4), "reps": (12, 20), "intensity": (55, 70)},
        "compensation": {"sets": (2, 3), "reps": (15, 25), "intensity": (45, 60)},
        "metabolic":    {"sets": (3, 4), "reps": (20, 35), "intensity": (40, 55)},
    },
    "tonificar": {
        "focus":        {"sets": (3, 4), "reps": (8, 15),  "intensity": (60, 75)},
        "compensation": {"sets": (2, 3), "reps": (12, 18), "intensity": (50, 65)},
        "metabolic":    {"sets": (3, 4), "reps": (15, 25), "intensity": (45, 60)},
    },
    "movilidad": {
        "focus":        {"sets": (2, 3), "reps": (8, 12),  "intensity": None},
        "compensation": {"sets": (2, 3), "reps": (10, 15), "intensity": None},
        "metabolic":    {"sets": (2, 3), "reps": (12, 20), "intensity": None},
    }
}


# =====================================================
# OBJETIVOS DE VOLUMEN SEMANAL APROXIMADO
# =====================================================

WEEKLY_SET_TARGETS = {
    "principiante": {"primary": (8, 12), "secondary": (6, 10)},
    "medio":        {"primary": (10, 16), "secondary": (6, 10)},
    "avanzado":     {"primary": (12, 20), "secondary": (8, 12)},
}
WEEKLY_SET_TARGETS["intermedio"] = WEEKLY_SET_TARGETS["medio"]


# =====================================================
# MAPEO SIMPLE DE PATRONES
# =====================================================

BODY_PART_TO_PATTERN = {
    "pecho": "push_upper",
    "espalda": "pull_upper",
    "hombros": "push_upper",
    "biceps": "arm_flexion",
    "triceps": "arm_extension",
    "antebrazos": "arm_flexion",
    "cuadriceps": "knee_dominant",
    "gluteos": "hip_dominant",
    "glúteos": "hip_dominant",
    "isquiotibiales": "hip_dominant",
    "femoral": "hip_dominant",
    "pantorrillas": "calves",
    "gemelos": "calves",
    "core": "core",
    "abdomen": "core",
    "core/abdomen": "core",
    "lumbar": "core",
    "aductores": "lower_accessory",
    "abductores": "lower_accessory",
    "movilidad": "mobility",
}

FULL_BODY_PRIMARY_PARTS = {
    "pecho", "espalda", "cuadriceps", "gluteos", "glúteos", "isquiotibiales", "femoral", "hombros"
}

PATTERN_SET_TARGETS_HYPERTROPHY = {
    "knee_dominant": (6, 12),
    "hip_dominant": (6, 12),
    "push_upper": (8, 14),
    "pull_upper": (8, 14),
}


# =====================================================
# MOTOR DINÁMICO
# =====================================================

class RoutineEngineDynamic:

    def __init__(self, exercises):
        self.exercises = exercises
        self.used_exercises = set()

        self.training_days = 4
        self.fatigue_score = 0.0

        self.local_fatigue = defaultdict(float)
        self.weekly_volume_tracker = defaultdict(int)
        self.weekly_pattern_tracker = defaultdict(int)
        self.exercise_frequency_tracker = defaultdict(int)

        self.current_goal = None
        self.current_level = "medio"
        self.current_focus = "full_body"
        self.current_location = "gimnasio"
        self.current_injury = "no"
        self.current_duration = 60

    # =====================================================
    # NORMALIZADORES
    # =====================================================

    def normalize_text(self, value):
        if value is None:
            return ""
        return str(value).strip().lower()

    def normalize_level(self, level):
        level = self.normalize_text(level)
        if level in ("principiante", "beginner", "novato"):
            return "principiante"
        if level in ("medio", "intermedio", "intermediate"):
            return "medio"
        if level in ("avanzado", "advanced"):
            return "avanzado"
        return "medio"

    def normalize_bodypart(self, exercise):
        return self.normalize_text(exercise.get("bodyPart", ""))

    def normalize_exercise_type(self, exercise):
        return self.normalize_text(exercise.get("exerciseType", ""))

    # =====================================================
    # CLASIFICACIÓN
    # =====================================================

    def infer_pattern(self, exercise):
        body_part = self.normalize_bodypart(exercise)
        if body_part in BODY_PART_TO_PATTERN:
            return BODY_PART_TO_PATTERN[body_part]

        ex_type = self.normalize_exercise_type(exercise)

        if ex_type == "movilidad":
            return "mobility"
        if ex_type in ("core/abdomen", "core"):
            return "core"
        if ex_type == "cardio":
            return "conditioning"
        if ex_type in ("pliometría", "pliometria"):
            return "power"

        return "general"

    def infer_compound(self, exercise):
        ex_type = self.normalize_exercise_type(exercise)
        pattern = self.infer_pattern(exercise)
        body_part = self.normalize_bodypart(exercise)
        name = self.normalize_text(exercise.get("name", ""))

        if ex_type in ("movilidad", "cardio", "equilibrio", "core/abdomen", "core"):
            return False

        compound_keywords = [
            "sentadilla", "squat", "press", "remo", "row", "peso muerto",
            "deadlift", "zancada", "lunge", "dominada", "pull up", "pull-up",
            "jalon", "jalón", "lat pulldown", "hip thrust", "prensa", "bench"
        ]
        if any(k in name for k in compound_keywords):
            return True

        if pattern in ("push_upper", "pull_upper", "knee_dominant", "hip_dominant"):
            if body_part not in ("biceps", "triceps", "pantorrillas", "gemelos", "antebrazos"):
                return True

        return False

    def is_mobility_exercise(self, exercise):
        return self.normalize_exercise_type(exercise) == "movilidad"

    def is_cardio_like(self, exercise):
        return self.normalize_exercise_type(exercise) in ("cardio", "pliometría", "pliometria")

    def is_core_exercise(self, exercise):
        return self.normalize_exercise_type(exercise) in ("core/abdomen", "core")

    def get_exercise_slot(self, exercise):
        pattern = self.infer_pattern(exercise)
        is_compound = self.infer_compound(exercise)

        if is_compound and pattern in ("knee_dominant", "hip_dominant"):
            return "lower_compound"
        if is_compound and pattern == "push_upper":
            return "upper_push_compound"
        if is_compound and pattern == "pull_upper":
            return "upper_pull_compound"
        if self.is_core_exercise(exercise):
            return "core"
        if self.is_mobility_exercise(exercise):
            return "mobility"
        return "isolation"

    # =====================================================
    # COMPATIBILIDAD CON PERFIL
    # =====================================================

    def is_compatible_with_profile(self, exercise):
        if self.current_location == "gimnasio":
            compatible = True
        else:
            compatible = True

        if self.current_injury == "si":
            if self.is_cardio_like(exercise):
                return False

        return compatible

    # =====================================================
    # ESTRUCTURA SEMANAL
    # =====================================================

    def build_week_structure(self, training_days, goal=None, focus=None):
        goal = goal or self.current_goal
        focus = focus or self.current_focus

        if goal == "ganar_musculo" and focus == "full_body":
            if training_days == 4:
                return ["focus", "focus", "focus", "compensation"]
            if training_days == 5:
                return ["focus", "focus", "focus", "focus", "compensation"]
            if training_days == 6:
                return ["focus", "focus", "focus", "focus", "compensation", "compensation"]
            if training_days == 7:
                return ["focus", "focus", "focus", "focus", "focus", "compensation", "compensation"]

        focus_days = max(2, round(training_days * 0.4))
        compensation_days = max(1, round(training_days * 0.2))
        metabolic_days = max(0, training_days - focus_days - compensation_days)

        structure = (
            ["focus"] * focus_days +
            ["compensation"] * compensation_days +
            ["metabolic"] * metabolic_days
        )

        random.shuffle(structure)
        return structure[:training_days]

    # =====================================================
    # FATIGA
    # =====================================================

    def decay_fatigue(self):
        for bp in list(self.local_fatigue.keys()):
            self.local_fatigue[bp] *= 0.65
            if self.local_fatigue[bp] < 0.05:
                del self.local_fatigue[bp]

        self.fatigue_score *= 0.75

    def adjust_intensity_percent(self, base_percent, body_part):
        local = self.local_fatigue[self.normalize_text(body_part)]
        adjusted = base_percent

        if local > 0.80:
            adjusted -= 10
        elif local > 0.55:
            adjusted -= 7
        elif local > 0.30:
            adjusted -= 4

        if self.fatigue_score > 0.75:
            adjusted -= 5
        elif self.fatigue_score > 0.50:
            adjusted -= 3

        return max(40, min(90, adjusted))

    # =====================================================
    # OBJETIVOS DE VOLUMEN
    # =====================================================

    def get_set_target_for_bodypart(self, body_part):
        level_cfg = WEEKLY_SET_TARGETS.get(self.current_level, WEEKLY_SET_TARGETS["medio"])

        if self.current_goal == "ganar_musculo":
            if body_part in FULL_BODY_PRIMARY_PARTS:
                return level_cfg["primary"]
            return level_cfg["secondary"]

        return (4, 10)

    def get_required_patterns_for_day(self, goal, day_type):
        if goal == "ganar_musculo" and self.current_focus == "full_body":
            if day_type == "focus":
                return ["knee_dominant", "push_upper", "pull_upper", "hip_dominant"]
            if day_type == "compensation":
                return ["core", "mobility"]
            return ["conditioning", "core"]

        if day_type == "compensation":
            return ["core", "mobility"]
        if day_type == "metabolic":
            return ["conditioning"]

        return ["push_upper", "pull_upper", "knee_dominant"]

    # =====================================================
    # SCORING
    # =====================================================

    def score_exercise(self, exercise, goal, day_type, bodyparts_today, patterns_today):
        score = 1.0

        if not self.is_compatible_with_profile(exercise):
            return 0.0

        ex_type = self.normalize_exercise_type(exercise)
        body_part = self.normalize_bodypart(exercise)
        pattern = self.infer_pattern(exercise)
        is_compound = self.infer_compound(exercise)

        # Evitar movilidad y cardio en días focus de hipertrofia
        if goal == "ganar_musculo" and day_type == "focus":
            if self.is_mobility_exercise(exercise) or self.is_cardio_like(exercise):
                return 0.0

        # 1) Peso por objetivo
        if goal == "ganar_musculo":
            if day_type == "focus":
                if is_compound:
                    score *= 3.0
                elif ex_type == "fuerza":
                    score *= 2.2
                elif self.is_core_exercise(exercise):
                    score *= 0.7
                else:
                    score *= 0.8

            elif day_type == "compensation":
                if self.is_mobility_exercise(exercise):
                    score *= 2.0
                elif self.is_core_exercise(exercise):
                    score *= 1.8
                elif not is_compound:
                    score *= 1.3
                else:
                    score *= 0.9

            elif day_type == "metabolic":
                if self.is_cardio_like(exercise):
                    score *= 2.5
                else:
                    score *= 0.6

        elif goal == "perder_grasa":
            if self.is_cardio_like(exercise):
                score *= 3.0
            elif ex_type == "fuerza":
                score *= 1.8

        elif goal == "resistencia":
            if self.is_cardio_like(exercise) or self.is_core_exercise(exercise):
                score *= 2.5

        elif goal == "tonificar":
            if ex_type == "fuerza":
                score *= 2.0
            elif self.is_core_exercise(exercise):
                score *= 1.5

        elif goal == "movilidad":
            if self.is_mobility_exercise(exercise):
                score *= 4.0
            else:
                score *= 0.3

        # 2) Control de volumen por músculo
        current_sets = self.weekly_volume_tracker[body_part]
        target_min, target_max = self.get_set_target_for_bodypart(body_part)

        if current_sets < target_min:
            score *= 1.8
        elif current_sets > target_max:
            score *= 0.45

        # 3) Control por patrón semanal
        if goal == "ganar_musculo" and pattern in PATTERN_SET_TARGETS_HYPERTROPHY:
            pmin, pmax = PATTERN_SET_TARGETS_HYPERTROPHY[pattern]
            current_pattern_sets = self.weekly_pattern_tracker[pattern]

            if current_pattern_sets < pmin:
                score *= 1.7
            elif current_pattern_sets > pmax:
                score *= 0.6

        # 4) Cobertura de patrones del día
        required_patterns = self.get_required_patterns_for_day(goal, day_type)
        if pattern in required_patterns and pattern not in patterns_today:
            score *= 2.2

        # 5) Evitar exceso del mismo bodyPart en el día
        if body_part in bodyparts_today:
            score *= 0.30

        # 6) Fatiga local
        local = self.local_fatigue[body_part]
        score *= max(0.35, 1 - local)

        # 7) Penalización por repetición exacta del mismo ejercicio
        times_used = self.exercise_frequency_tracker[exercise["id"]]
        if times_used == 1:
            score *= 0.55
        elif times_used >= 2:
            score *= 0.20

        # 8) Sesgo para músculos principales en full body hipertrofia
        if goal == "ganar_musculo" and self.current_focus == "full_body" and day_type == "focus":
            if body_part in FULL_BODY_PRIMARY_PARTS:
                score *= 1.35

        return max(score, 0.0)

    # =====================================================
    # PRESCRIPCIÓN
    # Mantiene la misma salida
    # =====================================================

    def prescribe(self, goal, day_type, exercise):
        params = GOAL_PARAMS[goal][day_type]

        body_part = self.normalize_bodypart(exercise)
        is_compound = self.infer_compound(exercise)

        if goal == "movilidad" or self.is_mobility_exercise(exercise):
            sets = random.randint(2, 3)
            reps = random.randint(8, 15)
            return {
                "sets": sets,
                "reps": reps,
                "intensity_percent": None,
                "tempo": "controlado"
            }

        volume_modifier = 4 / max(4, self.training_days)

        base_sets_min, base_sets_max = params["sets"]
        base_reps_min, base_reps_max = params["reps"]
        intensity_min, intensity_max = params["intensity"]

        if goal == "ganar_musculo":
            if day_type == "focus":
                if is_compound:
                    sets = random.randint(3, 4)
                    reps = random.randint(6, 10)
                    intensity = random.randint(70, 82)
                elif self.is_core_exercise(exercise):
                    sets = random.randint(2, 3)
                    reps = random.randint(10, 15)
                    intensity = random.randint(50, 65)
                else:
                    sets = random.randint(2, 4)
                    reps = random.randint(10, 15)
                    intensity = random.randint(60, 75)

            elif day_type == "compensation":
                if self.is_core_exercise(exercise):
                    sets = random.randint(2, 3)
                    reps = random.randint(10, 18)
                    intensity = random.randint(50, 65)
                elif is_compound:
                    sets = random.randint(2, 3)
                    reps = random.randint(8, 12)
                    intensity = random.randint(60, 72)
                else:
                    sets = random.randint(2, 3)
                    reps = random.randint(12, 18)
                    intensity = random.randint(55, 68)

            else:
                sets = random.randint(2, 3)
                reps = random.randint(12, 20)
                intensity = random.randint(50, 65)

        else:
            raw_sets = random.randint(base_sets_min, base_sets_max)
            sets = max(2, int(round(raw_sets * volume_modifier)))
            reps = random.randint(base_reps_min, base_reps_max)
            intensity = random.randint(intensity_min, intensity_max)

        intensity = self.adjust_intensity_percent(intensity, body_part)

        return {
            "sets": sets,
            "reps": reps,
            "intensity_percent": int(round(intensity))
        }

    # =====================================================
    # FOCUS AREA
    # =====================================================

    def determine_focus_area(self, day_type, day_number):
        if self.current_focus == "full_body":
            return "full_body"

        if day_type == "focus":
            return "upper" if day_number % 2 == 1 else "lower"

        return "full_body"

    # =====================================================
    # HELPERS DE CONSTRUCCIÓN
    # =====================================================

    def build_exercise_instance(self, exercise, prescription, order):
        benefit = exercise.get("exerciseBenefit", [])
        if isinstance(benefit, str):
            benefit = [benefit]

        return {
            "exercise_instance_id": str(uuid.uuid4()),
            "order": order,
            "exercise_id": exercise["id"],
            "name": exercise["name"],
            "img_static": exercise.get("img_static"),
            "img_animated": exercise.get("img_animated"),
            "bodyPart": exercise.get("bodyPart"),
            "exerciseType": exercise.get("exerciseType"),
            "instructions": exercise.get("instructions", []),
            "exerciseBenefit": benefit,
            "prescription": prescription,
            "status": "pending",
            "liked": None,
            "completed_at": None
        }

    def register_selected_exercise(self, exercise, prescription):
        body_part = self.normalize_bodypart(exercise)
        pattern = self.infer_pattern(exercise)

        self.weekly_volume_tracker[body_part] += prescription["sets"]
        self.weekly_pattern_tracker[pattern] += prescription["sets"]
        self.local_fatigue[body_part] += 0.22 if self.infer_compound(exercise) else 0.14
        self.used_exercises.add(exercise["id"])
        self.exercise_frequency_tracker[exercise["id"]] += 1

    # =====================================================
    # DÍA ESPECIAL: HIPERTROFIA FULL BODY
    # =====================================================

    def generate_hypertrophy_full_body_day(self, day_number):
        exercises_for_day = []
        exercise_order = 1

        self.decay_fatigue()

        slots = [
            "lower_compound",
            "upper_push_compound",
            "upper_pull_compound",
            "lower_compound",
            "isolation"
        ]

        bodyparts_today = set()
        patterns_today = set()

        for slot in slots:
            candidates = [
                e for e in self.exercises
                if self.is_compatible_with_profile(e)
            ]

            if slot == "lower_compound":
                candidates = [e for e in candidates if self.get_exercise_slot(e) == "lower_compound"]

                if "knee_dominant" in patterns_today:
                    alt = [e for e in candidates if self.infer_pattern(e) == "hip_dominant"]
                    if alt:
                        candidates = alt
                elif "hip_dominant" in patterns_today:
                    alt = [e for e in candidates if self.infer_pattern(e) == "knee_dominant"]
                    if alt:
                        candidates = alt

            elif slot == "upper_push_compound":
                candidates = [e for e in candidates if self.get_exercise_slot(e) == "upper_push_compound"]

            elif slot == "upper_pull_compound":
                candidates = [e for e in candidates if self.get_exercise_slot(e) == "upper_pull_compound"]

            elif slot == "isolation":
                candidates = [
                    e for e in candidates
                    if self.get_exercise_slot(e) == "isolation"
                    and not self.is_mobility_exercise(e)
                    and not self.is_cardio_like(e)
                ]

            if not candidates:
                continue

            weights = [
                self.score_exercise(e, "ganar_musculo", "focus", bodyparts_today, patterns_today)
                for e in candidates
            ]

            if not any(w > 0 for w in weights):
                continue

            exercise = random.choices(candidates, weights=weights, k=1)[0]
            prescription = self.prescribe("ganar_musculo", "focus", exercise)

            exercise_instance = self.build_exercise_instance(
                exercise=exercise,
                prescription=prescription,
                order=exercise_order
            )
            exercises_for_day.append(exercise_instance)

            self.register_selected_exercise(exercise, prescription)

            bodyparts_today.add(self.normalize_bodypart(exercise))
            patterns_today.add(self.infer_pattern(exercise))

            exercise_order += 1

        # Relleno de seguridad si por dataset pequeño faltan ejercicios
        if len(exercises_for_day) < 5:
            fallback_candidates = [
                e for e in self.exercises
                if self.is_compatible_with_profile(e)
                and not self.is_mobility_exercise(e)
                and not self.is_cardio_like(e)
            ]

            attempts = 0
            while len(exercises_for_day) < 5 and attempts < 50 and fallback_candidates:
                weights = [
                    self.score_exercise(e, "ganar_musculo", "focus", bodyparts_today, patterns_today)
                    for e in fallback_candidates
                ]

                if not any(w > 0 for w in weights):
                    break

                exercise = random.choices(fallback_candidates, weights=weights, k=1)[0]
                prescription = self.prescribe("ganar_musculo", "focus", exercise)

                exercise_instance = self.build_exercise_instance(
                    exercise=exercise,
                    prescription=prescription,
                    order=exercise_order
                )
                exercises_for_day.append(exercise_instance)

                self.register_selected_exercise(exercise, prescription)

                bodyparts_today.add(self.normalize_bodypart(exercise))
                patterns_today.add(self.infer_pattern(exercise))

                fallback_candidates.remove(exercise)
                exercise_order += 1
                attempts += 1

        self.fatigue_score += 0.08 + (0.01 * self.training_days)
        self.fatigue_score = min(self.fatigue_score, 1.0)

        return {
            "day_number": day_number,
            "type": "focus",
            "focus_area": "full_body",
            "status": "pending",
            "completed_at": None,
            "exercises": exercises_for_day
        }

    # =====================================================
    # GENERAR DÍA GENERAL
    # =====================================================

    def generate_day(self, goal, day_type, day_number):
        if goal == "ganar_musculo" and self.current_focus == "full_body" and day_type == "focus":
            return self.generate_hypertrophy_full_body_day(day_number)

        exercises_for_day = []

        available = [e for e in self.exercises if self.is_compatible_with_profile(e)]
        if not available:
            available = self.exercises.copy()

        bodyparts_today = set()
        patterns_today = set()

        attempts = 0
        exercise_order = 1
        max_exercises = 5

        self.decay_fatigue()

        while len(exercises_for_day) < max_exercises and attempts < 80:
            if not available:
                available = [e for e in self.exercises if self.is_compatible_with_profile(e)]
                if not available:
                    available = self.exercises.copy()

            weights = [
                self.score_exercise(e, goal, day_type, bodyparts_today, patterns_today)
                for e in available
            ]

            if not any(w > 0 for w in weights):
                break

            exercise = random.choices(available, weights=weights, k=1)[0]
            body_part = self.normalize_bodypart(exercise)

            if body_part in bodyparts_today and attempts < 35:
                attempts += 1
                available.remove(exercise)
                continue

            prescription = self.prescribe(goal, day_type, exercise)
            exercise_instance = self.build_exercise_instance(
                exercise=exercise,
                prescription=prescription,
                order=exercise_order
            )
            exercises_for_day.append(exercise_instance)

            self.register_selected_exercise(exercise, prescription)

            bodyparts_today.add(body_part)
            patterns_today.add(self.infer_pattern(exercise))

            available.remove(exercise)
            exercise_order += 1
            attempts += 1

        self.fatigue_score += 0.08 + (0.01 * self.training_days)
        self.fatigue_score = min(self.fatigue_score, 1.0)

        return {
            "day_number": day_number,
            "type": day_type,
            "focus_area": self.determine_focus_area(day_type, day_number),
            "status": "pending",
            "completed_at": None,
            "exercises": exercises_for_day
        }

    # =====================================================
    # GENERAR SEMANA
    # =====================================================

    def generate_week(
        self,
        goal,
        training_days=4,
        year=None,
        week=None,
        year_week=None,
        level="medio",
        focus="full_body",
        duration=60,
        location="gimnasio",
        injury="no"
    ):
        if training_days < 4 or training_days > 7:
            raise ValueError("training_days debe estar entre 4 y 7")

        self.current_goal = goal
        self.current_level = self.normalize_level(level)
        self.current_focus = self.normalize_text(focus) or "full_body"
        self.current_location = self.normalize_text(location) or "gimnasio"
        self.current_injury = self.normalize_text(injury) or "no"

        try:
            self.current_duration = int(duration)
        except Exception:
            self.current_duration = 60

        self.training_days = training_days
        self.used_exercises = set()
        self.fatigue_score = 0.0
        self.local_fatigue = defaultdict(float)
        self.weekly_volume_tracker = defaultdict(int)
        self.weekly_pattern_tracker = defaultdict(int)
        self.exercise_frequency_tracker = defaultdict(int)

        week_structure = self.build_week_structure(training_days, goal=goal, focus=self.current_focus)

        week_days = []
        for i, day_type in enumerate(week_structure):
            day = self.generate_day(goal, day_type, i + 1)
            week_days.append(day)

        return {
            "days": week_days
        }


# =====================================================
# PRUEBA LOCAL
# =====================================================

if __name__ == "__main__":
    random.seed(42)

    exercises = [
        {
            "id": "ex_1",
            "name": "Sentadilla con barra",
            "bodyPart": "cuadriceps",
            "exerciseType": "fuerza",
            "instructions": ["Coloca la barra sobre la espalda", "Baja controlado", "Sube fuerte"],
            "exerciseBenefit": ["Hipertrofia de piernas"],
            "img_static": None,
            "img_animated": None
        },
        {
            "id": "ex_2",
            "name": "Press de banca",
            "bodyPart": "pecho",
            "exerciseType": "fuerza",
            "instructions": ["Baja la barra al pecho", "Empuja hacia arriba"],
            "exerciseBenefit": ["Hipertrofia de pecho"],
            "img_static": None,
            "img_animated": None
        },
        {
            "id": "ex_3",
            "name": "Remo con barra",
            "bodyPart": "espalda",
            "exerciseType": "fuerza",
            "instructions": ["Inclina el torso", "Lleva la barra al abdomen"],
            "exerciseBenefit": ["Hipertrofia de espalda"],
            "img_static": None,
            "img_animated": None
        },
        {
            "id": "ex_4",
            "name": "Peso muerto rumano",
            "bodyPart": "isquiotibiales",
            "exerciseType": "fuerza",
            "instructions": ["Baja la barra rozando las piernas", "Sube apretando glúteos"],
            "exerciseBenefit": ["Cadena posterior"],
            "img_static": None,
            "img_animated": None
        },
        {
            "id": "ex_5",
            "name": "Press militar con mancuernas",
            "bodyPart": "hombros",
            "exerciseType": "fuerza",
            "instructions": ["Empuja las mancuernas hacia arriba"],
            "exerciseBenefit": ["Hipertrofia de hombros"],
            "img_static": None,
            "img_animated": None
        },
        {
            "id": "ex_6",
            "name": "Curl de bíceps con mancuerna",
            "bodyPart": "biceps",
            "exerciseType": "fuerza",
            "instructions": ["Flexiona el codo sin balancearte"],
            "exerciseBenefit": ["Aislamiento de bíceps"],
            "img_static": None,
            "img_animated": None
        },
        {
            "id": "ex_7",
            "name": "Extensión de tríceps en polea",
            "bodyPart": "triceps",
            "exerciseType": "fuerza",
            "instructions": ["Empuja hacia abajo controlado"],
            "exerciseBenefit": ["Aislamiento de tríceps"],
            "img_static": None,
            "img_animated": None
        },
        {
            "id": "ex_8",
            "name": "Crunch abdominal",
            "bodyPart": "core/abdomen",
            "exerciseType": "core/abdomen",
            "instructions": ["Eleva el tronco suavemente"],
            "exerciseBenefit": ["Fortalecimiento abdominal"],
            "img_static": None,
            "img_animated": None
        },
        {
            "id": "ex_9",
            "name": "Plancha frontal",
            "bodyPart": "core",
            "exerciseType": "core/abdomen",
            "instructions": ["Mantén el cuerpo alineado"],
            "exerciseBenefit": ["Estabilidad del core"],
            "img_static": None,
            "img_animated": None
        },
        {
            "id": "ex_10",
            "name": "Movilidad de cadera",
            "bodyPart": "movilidad",
            "exerciseType": "movilidad",
            "instructions": ["Haz círculos controlados de cadera"],
            "exerciseBenefit": ["Mejora de movilidad"],
            "img_static": None,
            "img_animated": None
        }
    ]

    profile = {
        "duration": "60",
        "goal": "ganar_musculo",
        "user_id": "user_3AE5yTdcD52kbDgk4Pq5zA1RTNU",
        "level": "medio",
        "focus": "full_body",
        "created_at": "2026-03-05T15:55:53.916559",
        "location": "gimnasio",
        "injury": "no"
    }

    engine = RoutineEngineDynamic(exercises)

    week = engine.generate_week(
        goal=profile["goal"],
        training_days=4,
        level=profile["level"],
        focus=profile["focus"],
        duration=profile["duration"],
        location=profile["location"],
        injury=profile["injury"]
    )

    import json
    print(json.dumps(week, indent=2, ensure_ascii=False))