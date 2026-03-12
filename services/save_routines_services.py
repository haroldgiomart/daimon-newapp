import boto3
import os
from datetime import datetime
from services.RoutineDynamicPro_IG import RoutineEngineDynamic
from services.dynamodb_service import get_dynamodb_table
from decimal import Decimal


# ==========================================================
# PROFILE - LOAD FROM DYNAMODB
# ==========================================================

def get_user_exercise_profile(user_id):

    main_objective, level, location = None, None, None

    dynamodb = get_dynamodb_table()
    table = dynamodb.Table("daimon_exercise_profile")

    response = table.get_item(
        Key={
            "user_id": user_id
        }
    )

    print(f"Trayecto Perfil de Ejercicio del Usuario: {response}")

    if response.get("Item"):
        main_objective = response['Item']['goal']
        level = response['Item']['level']
        location = response['Item']['location']

    return main_objective, level, location

# ==========================================================
# EXERCISES - LOAD FROM DYNAMODB
# ==========================================================

def get_all_exercises():
    dynamodb = get_dynamodb_table()
    table = dynamodb.Table("daimon_physical_activity")

    exercises = []
    scan_kwargs = {}

    while True:
        response = table.scan(**scan_kwargs)

        exercises.extend(response.get("Items", []))

        if "LastEvaluatedKey" not in response:
            break

        scan_kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]

    return exercises


# ==========================================================
# FILTERS
# ==========================================================

CASA_SIN_EQUIPO = [
    "mancuerna", "cable", "máquina de palanca", "kettlebell",
    "balón de estabilidad", "máquina smith", "máquina de trineo",
    "macuerna ez", "ponderado", "balón medicional", "balón bosu",
    "bicicleta estática", "máquina elíptica", "máquina de step",
    "barra olímpica", "rodillo"
]

CASA_CON_MANCUERNAS = [
    "cable", "máquina de palanca", "kettlebell",
    "balón de estabilidad", "máquina smith", "máquina de trineo",
    "ponderado", "balón medicional", "balón bosu",
    "bicicleta estática", "máquina elíptica", "máquina de step",
    "barra olímpica", "rodillo"
]

GIMNASIO = ["peso corporal", "asistido"]


def filter_per_equipment_and_level(exercises, equipment, level):

    # -------- Filtrado por equipo --------
    if equipment == "casa_sin_equipo":
        exercises = [
            e for e in exercises
            if e['equipment'] not in CASA_SIN_EQUIPO
        ]

    elif equipment == "casa_con_mancuernas":
        exercises = [
            e for e in exercises
            if e['equipment'] not in CASA_CON_MANCUERNAS
        ]

    elif equipment == "gimnasio":
        exercises = [
            e for e in exercises
            if e['equipment'] not in GIMNASIO
        ]

    # -------- Filtrado por nivel --------
    if level == "bajo":
        allowed_levels = ["bajo", "medio"]

    elif level == "medio":
        allowed_levels = ["medio", "alto"]

    elif level == "alto":
        allowed_levels = ["medio", "alto"]

    else:
        allowed_levels = ["bajo", "medio", "alto"]

    exercises = [
        e for e in exercises
        if e.get("difficultyLevel") in allowed_levels
    ]

    return exercises


# ==========================================================
# WEEK HELPERS
# ==========================================================

def get_current_year_week():
    now = datetime.utcnow()
    year = now.year
    week = now.isocalendar()[1]
    year_week = f"{year}-W{week:02d}"
    return year, week, year_week


# ==========================================================
# SAVE ROUTINE
# ==========================================================

def save_week_routine(user_preferences: dict, routines: dict):

    dynamodb = get_dynamodb_table()
    table = dynamodb.Table("daimon_exercise_routines")

    year, week, year_week = get_current_year_week()

    item = {
        "user_id": user_preferences['user_id'],
        "year_week": year_week,
        "year": year,
        "week": week,
        "goal": user_preferences['goal'],

        "status": "in_progress",
        "created_at": datetime.utcnow().isoformat(),
        "completed_at": None,

        "routines": routines['days'],
        "status_routine": "ACTIVE",
        "training_days": len(routines['days'])
    }

    table.put_item(Item=item)

    return item


# ==========================================================
# MAIN HANDLER (AWS LAMBDA)
# ==========================================================

def generate_routine(user_id):

    # ------------------------------------------------------
    # 0. Traer información del usuario
    # ------------------------------------------------------
    main_objective, level, location = get_user_exercise_profile(user_id)
    if level == "None":
        return {"Error": "No se encontró el perfil de ejercicio del usuario"}

    # ------------------------------------------------------
    # 1. Load exercises
    # ------------------------------------------------------
    exercises = get_all_exercises()
    print(f"Total ejercicios: {len(exercises)}")

    # ------------------------------------------------------
    # 2. Filter exercises
    # ------------------------------------------------------
    exercises = filter_per_equipment_and_level(
        exercises,
        location,
        level
    )
    print(f"Ejercicios filtrados: {len(exercises)}")

    # ------------------------------------------------------
    # 3. Training days based on level
    # ------------------------------------------------------
    if level == "bajo":
        training_days = 4
    elif level == "medio":
        training_days = 6
    elif level == "alto":
        training_days = 7
    else:
        training_days = 4

    # ------------------------------------------------------
    # 4. Initialize Engine
    # ------------------------------------------------------
    engine = RoutineEngineDynamic(exercises)

    # ------------------------------------------------------
    # 5. Generate weekly routine
    # ------------------------------------------------------
    routines = engine.generate_week(main_objective, training_days)

    print(f"Rutinas generadas: {len(routines)}")

    # ------------------------------------------------------
    # 6. Save routine
    # ------------------------------------------------------
    user_preferences = {
        "user_id": user_id,
        "goal": main_objective
    }

    saved_item = save_week_routine(user_preferences, routines)

    return {
        "statusCode": 200,
        "body": {
            "message": "Routine generated successfully",
            "routine": saved_item
        }
    }

# ==========================================================
# CONSULTAR RUTINA
# ==========================================================

def convert_decimals(obj):
    """
    Convierte Decimal a int o float recursivamente
    """
    if isinstance(obj, list):
        return [convert_decimals(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        if obj % 1 == 0:
            return int(obj)
        else:
            return float(obj)
    else:
        return obj
def get_routines_by_status(user_id: str, status_routine: str):

    routine = []

    dynamodb = get_dynamodb_table()
    table = dynamodb.Table("daimon_exercise_routines")

    response = table.query(
        IndexName="user-status-index",  # 🔥 Nombre del GSI
        KeyConditionExpression="user_id = :uid AND status_routine = :status",
        ExpressionAttributeValues={
            ":uid": user_id,
            ":status": status_routine
        }
    )

    routines = response.get("Items", [])
    if routines:
        routine = routines[0]
        routine = convert_decimals(routine)

    return routine

def get_routine(user_id, year_week, day_number):

    day_data = []

    dynamodb = get_dynamodb_table()
    table = dynamodb.Table("daimon_exercise_routines")

    response = table.get_item(
        Key={
            "user_id": user_id,
            "year_week": year_week
        }
    )

    routine = response.get("Item", [])
    if routine:
        for r in routine['routines']:
            if r['day_number'] == day_number:
                day_data = r
                day_data = convert_decimals(day_data)

    return day_data


def complete_exercise(user_id: str,year_week: str,day_number: int,exercise_order: int) -> dict:

    try:

        dynamodb = get_dynamodb_table()
        table = dynamodb.Table("daimon_exercise_routines")

        now = datetime.utcnow().isoformat()

        day_index = day_number - 1
        exercise_index = exercise_order - 1
        print(f"day_index: {day_index}, day_number: {exercise_index}, year_week: {year_week}")

        # --------------------------------------------------
        # 1️⃣ Marcar ejercicio como completed
        # --------------------------------------------------
        update_expression = f"""
        SET routines[{day_index}].exercises[{exercise_index}].#s = :completed,
            routines[{day_index}].exercises[{exercise_index}].completed_at = :now
        """

        print(f"Update Expression: {update_expression}")

        response = table.update_item(
            Key={
                "user_id": user_id,
                "year_week": year_week
            },
            UpdateExpression=update_expression,
            ExpressionAttributeNames={
                "#s": "status"
            },
            ExpressionAttributeValues={
                ":completed": "completed",
                ":now": now
            }
        )

        print(f"Response: {response}")

        # --------------------------------------------------
        # 2️⃣ Revisar si el día quedó completo
        # --------------------------------------------------
        check_and_complete_day(
            user_id,
            year_week,
            day_index,
            now
        )

        # --------------------------------------------------
        # 3️⃣ Revisar si la rutina completa quedó terminada
        # --------------------------------------------------
        update_routine_progress(
            user_id,
            year_week,
            now
        )

        return {"success": True}

    except Exception as Error:
        print(f"Comple Exercise: {Error}")


def check_and_complete_day(user_id: str,year_week: str,day_index: int,now: str):
    try:
        dynamodb = get_dynamodb_table()
        table = dynamodb.Table("daimon_exercise_routines")

        response = table.get_item(
            Key={
                "user_id": user_id,
                "year_week": year_week
            }
        )

        item = response.get("Item")

        if not item:
            return

        day = item["routines"][day_index]

        all_completed = all(
            ex["status"] == "completed"
            for ex in day["exercises"]
        )

        if not all_completed:
            return

        # --------------------------------------------------
        # Marcar el día como completed
        # --------------------------------------------------
        update_expression = f"""
        SET routines[{day_index}].#s = :completed,
            routines[{day_index}].completed_at = :now
        """

        table.update_item(
            Key={
                "user_id": user_id,
                "year_week": year_week
            },
            UpdateExpression=update_expression,
            ExpressionAttributeNames={
                "#s": "status"
            },
            ExpressionAttributeValues={
                ":completed": "completed",
                ":now": now
            }
        )

    except Exception as Error:
        print(f"check_and_complete_day Error: {Error}")

def check_and_complete_routine(user_id: str,year_week: str,now: str):
    dynamodb = get_dynamodb_table()
    table = dynamodb.Table("daimon_exercise_routines")

    try:
        response = table.get_item(
            Key={
                "user_id": user_id,
                "year_week": year_week
            }
        )

        item = response.get("Item")

        if not item:
            return

        all_days_completed = all(
            day["status"] == "completed"
            for day in item["routines"]
        )

        if not all_days_completed:
            return

        # --------------------------------------------------
        # Marcar rutina completa
        # --------------------------------------------------
        table.update_item(
            Key={
                "user_id": user_id,
                "year_week": year_week
            },
            UpdateExpression="""
            SET #sr = :completed,
                completed_at = :now
            """,
            ExpressionAttributeNames={
                "#sr": "status_routine"
            },
            ExpressionAttributeValues={
                ":completed": "COMPLETED",
                ":now": now
            }
        )

    except Exception as Error:
        print(f"check_and_complete_routine Error: {Error}")

def update_routine_progress(user_id: str,year_week: str,now: str):

    dynamodb = get_dynamodb_table()
    table = dynamodb.Table("daimon_exercise_routines")

    try:
        response = table.get_item(
            Key={
                "user_id": user_id,
                "year_week": year_week
            }
        )

        item = response.get("Item")
        if not item:
            return

        total_exercises = 0
        completed_exercises = 0

        for day in item["routines"]:
            for ex in day["exercises"]:
                total_exercises += 1
                if ex.get("status") == "completed":
                    completed_exercises += 1

        progress = int((completed_exercises / total_exercises) * 100) if total_exercises > 0 else 0

        # --------------------------------------------------
        # Construcción dinámica del update
        # --------------------------------------------------

        update_expression = "SET progress_percentage = :progress"
        expression_values = {
            ":progress": progress
        }

        expression_names = {}

        # Si llegó a 100 → marcar rutina como COMPLETED
        if progress == 100:
            update_expression += ", #sr = :completed, completed_at = :now"
            expression_values[":completed"] = "COMPLETED"
            expression_values[":now"] = now
            expression_names["#sr"] = "status_routine"

        update_params = {
            "Key": {
                "user_id": user_id,
                "year_week": year_week
            },
            "UpdateExpression": update_expression,
            "ExpressionAttributeValues": expression_values
        }

        if expression_names:
            update_params["ExpressionAttributeNames"] = expression_names

        table.update_item(**update_params)

    except Exception as Error:
        print(f"update_routine_progress Error: {Error}")

if __name__ == '__main__':
    #response = get_routines_by_status("e306fbfa-3d2e-488b-8e59-b58ed5c7485e", "ACTIVE")
    day_data = get_routine("e306fbfa-3d2e-488b-8e59-b58ed5c7485e", "2026-W08", 1)
    print(f"Response: {day_data}")
