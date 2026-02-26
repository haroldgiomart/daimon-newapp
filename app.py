import os
import logging
import uuid

from flask import (
    Flask,
    request,
    abort,
    render_template,
    session,
    redirect,
    url_for,
    jsonify
)

from cachetools import TTLCache, cached

from services.redeem_service import redeem_benefit
from services.recent_benefits import get_recent_benefits
from services.benefits_service import get_benefits_by_subcategory
from services.benefit_details import get_benefit_details
from services.wellness_videos import get_videos
from services.user_profile import build_user_profile
from services.search_service import search_benefits_from_text
from services.semantic_search import semantic_intent_search
from services.exercise_service import (
    get_exercise_by_id,
    all_items
)

from services.user_data_service import (
    save_profile,
    add_favorite,
    remove_favorite,
    get_user_items,
    get_user_favorites
)

from services.user_data_service import add_disliked, remove_disliked
from services.exercise_profile import get_exercise_profile, save_exercise_profile
from services.save_routines_services import generate_routine, get_routines_by_status, get_routine, complete_exercise

# ---------------------------------------------------------
# App configuration
# ---------------------------------------------------------

app = Flask(__name__, template_folder="templates")
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "unsafe-dev-key")

# ---------------------------------------------------------
# Logging
# ---------------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------
# Ensure anon or logged user
# ---------------------------------------------------------

@app.before_request
def ensure_user():
    if "user_id" not in session and "anon_id" not in session:
        session["anon_id"] = str(uuid.uuid4())


def get_current_user_id():
    return session.get("user_id") or session.get("anon_id")


# ---------------------------------------------------------
# Cache configuration (24h)
# ---------------------------------------------------------

cupones_cache = TTLCache(
    maxsize=5,
    ttl=60 * 60 * 24
)


@cached(cupones_cache)
def get_cupones_cached(category: str):
    logger.info("Cargando cupones desde API (no cache)")
    data = get_benefits_by_subcategory(category)

    if not data:
        raise ValueError("No se cachean resultados vacíos")

    return data


# ---------------------------------------------------------
# Landing
# ---------------------------------------------------------

@app.route("/")
def landing():
    return render_template("landing.html")


# ---------------------------------------------------------
# Home
# ---------------------------------------------------------

@app.route("/home")
def home():

    user_id = get_current_user_id()
    items = get_user_items(user_id)

    # PROFILE
    profile_item = next(
        (item for item in items if item["SK"] == "PROFILE"),
        None
    )

    if not profile_item:
        return redirect(url_for("survey"))

    user_tags = profile_item.get("user_tags", [])
    logger.info("User tags desde Dynamo: %s", user_tags)

    # FAVORITOS (benefits y exercises)
    favorite_ids = []

    for item in items:
        if item["SK"].startswith("FAVORITE#"):
            favorite_ids.append(item.get("item_id"))

    response = get_recent_benefits()
    recomendados = response.get("data", []) if isinstance(response, dict) else []

    return render_template(
        "home.html",
        favoritos=favorite_ids,
        recomendados=recomendados
    )


# ---------------------------------------------------------
# Intent Search
# ---------------------------------------------------------

@app.route("/intent/<intent>")
def intent_search(intent):

    user_id = get_current_user_id()
    items = get_user_items(user_id)

    profile_item = next(
        (item for item in items if item["SK"] == "PROFILE"),
        None
    )

    user_tags = profile_item.get("user_tags", []) if profile_item else []

    results = semantic_intent_search(
        intent=intent,
        user_profile_text="",
        user_tags=user_tags
    )

    return render_template(
        "search_results.html",
        title=f"Planes de {intent}",
        subtitle="Recomendado para ti",
        benefits=results
    )


# ---------------------------------------------------------
# Search
# ---------------------------------------------------------

@app.route("/search")
def search():
    q = request.args.get("q", "").strip()

    if not q:
        return redirect(url_for("home"))

    benefits = search_benefits_from_text(
        user_query=q,
        user_profile_text="",
        user_tags=[]
    )

    return render_template(
        "search_results.html",
        benefits=benefits
    )


# ---------------------------------------------------------
# Survey
# ---------------------------------------------------------

@app.route("/survey", methods=["GET", "POST"])
def survey():

    if request.method == "POST":
        data = {
            "situation": request.form.get("situation"),
            "stress_level": request.form.get("stress_level"),
            "improvement": request.form.getlist("improvement"),
            "has_kids": request.form.get("has_kids"),
            "free_time": request.form.getlist("free_time")
        }

        user_tags = build_user_profile(data)
        user_id = get_current_user_id()

        save_profile(user_id, data, list(user_tags))

        return redirect(url_for("home"))

    return render_template("survey.html")


# ---------------------------------------------------------
# Toggle Favorite (ARQUITECTURA CORRECTA)
# ---------------------------------------------------------
@app.route("/toggle-favorite", methods=["POST"])
def toggle_favorite():

    user_id = get_current_user_id()

    data = request.json
    item_id = data.get("item_id")
    item_type = data.get("item_type")  # "exercise" o "benefit"
    is_active = data.get("is_active")

    if not item_id or not item_type:
        return jsonify({"error": "Missing data"}), 400

    try:
        if is_active:
            add_favorite(
                user_id=user_id,
                item_id=item_id,
                item_type=item_type
            )
        else:
            remove_favorite(
                user_id=user_id,
                item_id=item_id,
                item_type=item_type
            )

        return jsonify({"success": True})

    except Exception as Error:
        print(f"Error toggle: {Error}")
        logger.exception("Error toggling favorite")
        return jsonify({"error": "Server error"}), 500

# ---------------------------------------------------------
# Toggle Dislike (ARQUITECTURA CORRECTA)
# ---------------------------------------------------------
@app.route("/toggle-dislike", methods=["POST"])
def toggle_dislike():

    user_id = get_current_user_id()

    data = request.json

    if not data:
        return jsonify({"error": "No JSON"}), 400

    item_id = data.get("item_id")
    is_active = data.get("is_active")

    # 🔥 Validación correcta
    if item_id is None or is_active is None:
        return jsonify({"error": "Missing data"}), 400

    try:
        if is_active:
            add_disliked(
                user_id=user_id,
                item_id=item_id,
                item_type="exercise"
            )
        else:
            remove_disliked(
                user_id=user_id,
                item_id=item_id,
                item_type="exercise"
            )

        return jsonify({"success": True})

    except Exception as error:
        print(f"Error toggle dislike: {error}")
        logger.exception("Error toggling dislike")
        return jsonify({"error": "Server error"}), 500

# ---------------------------------------------------------
# Cupones
# ---------------------------------------------------------

@app.route("/cupones")
def cupones():
    try:
        data = get_cupones_cached("cupones")
    except Exception:
        data = get_benefits_by_subcategory("cupones") or {}

    # 🔥 NUEVO: traer favoritos del usuario
    user_id = get_current_user_id()
    favorites = get_user_favorites(user_id, item_type="benefit")
    favorite_ids = [item["item_id"] for item in favorites]

    return render_template(
        "cupones.html",
        benefits_by_subcategory=data,
        favoritos=favorite_ids  # 🔥 enviar al template
    )


# ---------------------------------------------------------
# Detalle Beneficio
# ---------------------------------------------------------

@app.route("/beneficio/<benefit_code>/<benefit_id>")
def beneficio_detalle(benefit_code, benefit_id):

    benefit = get_benefit_details(benefit_code, benefit_id)

    if not benefit:
        abort(404, description="Beneficio no encontrado")

    return render_template(
        "beneficio_detalle.html",
        benefit=benefit
    )


# ---------------------------------------------------------
# Redención
# ---------------------------------------------------------

@app.route("/beneficio/<benefit_id>/redimir", methods=["GET"])
def beneficio_redimir(benefit_id):

    benefit_code = request.args.get("benefitCode")

    if not benefit_code:
        abort(400, description="benefitCode es requerido")

    benefit_code = benefit_code.lstrip("#")

    try:
        response = redeem_benefit(benefit_code[1:])

        if not response or "success" not in response:
            abort(404, description="No fue posible redimir el beneficio")

        return render_template(
            "beneficio_redencion.html",
            redeem=response["success"],
            benefit_id=benefit_id,
            benefit_code=benefit_code
        )

    except Exception:
        logger.exception("Error en redención")
        abort(500)


# ---------------------------------------------------------
# Ejercicios
# ---------------------------------------------------------

@app.route("/ejercicios")
def ejercicios():
    user_id = get_current_user_id()

    profile = None
    if user_id:
        profile = get_exercise_profile(user_id)
        print(f"Exercise Profile: {profile}")

    show_survey = profile is None

    data = all_items()

    favorites = []
    if user_id:
        favorites = get_user_favorites(user_id, item_type="exercise")

    favorite_ids = [item["item_id"] for item in favorites]

    return render_template(
        "ejercicios.html",
        exercises_by_target=data,
        favoritos=favorite_ids,
        show_survey=show_survey
    )


@app.route("/exercise/<exercise_id>")
def exercise_detail(exercise_id):

    exercise = get_exercise_by_id(exercise_id)
    print(f"Exercise Detail: {exercise}")

    if not exercise:
        return render_template("404.html"), 404

    return render_template(
        "exercise_detail.html",
        exercise=exercise
    )

@app.route("/exercise-entry")
def exercise_entry():
    return render_template("exercises_entry.html")
@app.route("/exercise-survey")
def exercise_survey():
    return render_template("exercise_survey.html")

@app.route("/exercise-survey/", methods=["POST"])
def save_exercise_survey():

    user_id = get_current_user_id()

    user_data = {
        "user_id": user_id,
        "goal": request.form.get("goal"),
        "level": request.form.get("level"),
        "duration": request.form.get("duration"),
        "location": request.form.get("location"),
        "focus": request.form.get("focus"),
        "injury": request.form.get("injury"),
    }

    save_exercise_profile(user_id, user_data)
    routine = generate_routine(user_data)
    print(f"La rutina generada es: {routine}")


    return redirect("/ejercicios")

@app.route("/mis-rutinas")
def mis_rutinas():

    user_id = get_current_user_id()
    routine = get_routines_by_status(user_id, "ACTIVE")

    if routine and "routines" in routine:
        for day in routine["routines"]:
            total = len(day.get("exercises", []))
            completed = sum(
                1 for ex in day.get("exercises", [])
                if ex.get("status") == "completed"
            )

            if total > 0:
                day["progress_percentage"] = int((completed / total) * 100)
            else:
                day["progress_percentage"] = 0

    return render_template(
        "routines.html",
        routine=routine
    )

@app.route("/routine/<user_id>/<year_week>/<int:day_number>")
def view_routine_day(user_id, year_week, day_number):

    day_data = get_routine(user_id, year_week, day_number)

    if not day_data or not day_data.get("exercises"):
        return render_template(
            "routine_workout.html",
            day_data=None,
            year_week=year_week
        )

    # 1 Ordenar ejercicios
    exercises = sorted(day_data["exercises"], key=lambda x: x["order"])
    day_data["exercises"] = exercises

    # 2 Encontrar primer ejercicio no completado
    current_index = next(
        (i for i, ex in enumerate(exercises) if ex.get("status") != "completed"),
        len(exercises) - 1
    )

    # 3 Verificar si todos están completados
    all_completed = all(
        ex.get("status") == "completed" for ex in exercises
    )

    #  Si la rutina está completa se muesta routine_completed
    if all_completed:

        total_exercises = len(exercises)
        total_sets = sum(ex["prescription"]["sets"] for ex in exercises)
        total_reps = sum(ex["prescription"]["reps"] for ex in exercises)

        avg_intensity = round(
            sum(ex["prescription"]["intensity_percent"] for ex in exercises)
            / total_exercises
        )

        return render_template(
            "routine_completed.html",
            day_data=day_data,
            total_exercises=total_exercises,
            total_sets=total_sets,
            total_reps=total_reps,
            avg_intensity=avg_intensity
        )

    # Si no está completa entonces se muestra la rutina normal
    return render_template(
        "routine_workout.html",
        day_data=day_data,
        year_week=year_week,
        current_index=current_index,
        all_completed=all_completed
    )

@app.route("/complete-exercise", methods=["POST"])
def complete_exercise_endpoint():

    data = request.get_json()

    result = complete_exercise(
        user_id = get_current_user_id(),
        year_week=data["year_week"],
        day_number=data["day_number"],
        exercise_order=data["exercise_order"]
    )

    return jsonify(result)

# ---------------------------------------------------------
# Videos
# ---------------------------------------------------------

@app.route("/salud")
def videos():
    data = get_videos()
    return render_template("videos.html", data=data)


# ---------------------------------------------------------
# Error handlers
# ---------------------------------------------------------

@app.errorhandler(400)
def bad_request(error):
    return render_template(
        "error.html",
        message=str(error.description)
    ), 400


@app.errorhandler(404)
def not_found(error):
    return render_template(
        "error.html",
        message=str(error.description)
    ), 404


@app.errorhandler(500)
def server_error(error):
    return render_template(
        "error.html",
        message="Ocurrió un error procesando la solicitud"
    ), 500


# ---------------------------------------------------------
# Run
# ---------------------------------------------------------

if __name__ == "__main__":
    app.run(
        debug=os.environ.get("FLASK_ENV") == "development"
    )