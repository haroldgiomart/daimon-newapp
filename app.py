import os
import logging
import requests

from flask import (
    Flask,
    abort,
    request,
    render_template,
    redirect,
    url_for,
    jsonify
)

from functools import wraps
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTError
from cachetools import TTLCache, cached
from dotenv import load_dotenv
from clerk_backend_api import Clerk

# ---------------------------------------------------------
# LOAD ENV
# ---------------------------------------------------------

load_dotenv()

# ---------------------------------------------------------
# SERVICES IMPORTS
# ---------------------------------------------------------

from services.redeem_service import redeem_benefit
from services.recent_benefits import get_recent_benefits
from services.benefits_service import get_benefits_by_subcategory
from services.benefit_details import get_benefit_details
from services.wellness_videos import get_videos
from services.user_profile import build_user_profile
from services.search_service import search_benefits_from_text
from services.semantic_search import semantic_intent_search
from services.exercise_service import get_exercise_by_id, all_items
from services.user_data_service import (
    save_profile,
    add_favorite,
    remove_favorite,
    get_user_items,
    get_user_favorites,
    add_disliked,
    remove_disliked,
    create_user_if_not_exists
)
from services.exercise_profile import get_exercise_profile, save_exercise_profile
from services.save_routines_services import (
    generate_routine,
    get_routines_by_status,
    get_routine,
    complete_exercise
)

# ---------------------------------------------------------
# APP CONFIG
# ---------------------------------------------------------

app = Flask(__name__, template_folder="templates")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------
# CLERK CONFIG (OPTIMIZED)
# ---------------------------------------------------------

clerk = Clerk(bearer_auth=os.environ["CLERK_SECRET_KEY"])
CLERK_ISSUER = os.environ.get("CLERK_ISSUER")
CLERK_JWKS_URL = f"{CLERK_ISSUER}/.well-known/jwks.json"
CLERK_PUBLISHABLE_KEY= os.environ.get("CLERK_PUBLISHABLE_KEY")

jwks_cache = None
clerk_user_cache = TTLCache(maxsize=1000, ttl=600)  # 10 minutos


def get_jwks():
    global jwks_cache
    if jwks_cache is None:
        response = requests.get(CLERK_JWKS_URL)
        jwks_cache = response.json()
    return jwks_cache


def verify_session_token(token):
    jwks = get_jwks()

    unverified_header = jwt.get_unverified_header(token)
    kid = unverified_header["kid"]

    key = next(
        (k for k in jwks["keys"] if k["kid"] == kid),
        None
    )

    if not key:
        raise Exception("Public key not found.")

    return jwt.decode(
        token,
        key,
        algorithms=["RS256"],
        issuer=CLERK_ISSUER,
        options={"verify_aud": False}
    )


def get_or_create_user(user_id):

    if user_id in clerk_user_cache:
        return clerk_user_cache[user_id]

    # Verificar si ya existe en Dynamo
    items = get_user_items(user_id)

    if items:
        user_data = {"sub": user_id}
        clerk_user_cache[user_id] = user_data
        return user_data

    # Usuario nuevo → llamar Clerk una sola vez
    user = clerk.users.get(user_id=user_id)

    email = (
        user.email_addresses[0].email_address
        if user.email_addresses else None
    )

    create_user_if_not_exists(
        user_id=user_id,
        email=email,
        first_name=user.first_name,
        last_name=user.last_name,
        image_url=user.image_url
    )

    user_data = {
        "sub": user_id,
        "email": email,
        "first_name": user.first_name,
        "last_name": user.last_name
    }

    clerk_user_cache[user_id] = user_data
    return user_data


def get_current_user():

    session_token = request.cookies.get("__session")

    if not session_token:
        return None

    try:
        payload = verify_session_token(session_token)
        user_id = payload["sub"]
        return get_or_create_user(user_id)

    except ExpiredSignatureError:
        logger.info("Session expired.")
        return None

    except JWTError:
        logger.warning("Invalid token.")
        return None

    except Exception as e:
        logger.exception(f"Session validation failed: {e}")
        return None

def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):

        user = get_current_user()

        if not user:
            return redirect(url_for("login"))

        request.user = user
        return f(*args, **kwargs)

    return wrapper


def get_current_user_id():
    return request.user["sub"]


@app.route("/logout")
def logout():
    response = redirect(url_for("landing"))
    response.delete_cookie("__session")
    return response


@app.context_processor
def inject_user():
    return dict(current_user=getattr(request, "user", None))

# ---------------------------------------------------------
# CACHE
# ---------------------------------------------------------

cupones_cache = TTLCache(maxsize=5, ttl=60 * 60 * 24)


@cached(cupones_cache)
def get_cupones_cached(category: str):
    data = get_benefits_by_subcategory(category)
    if not data:
        raise ValueError("No se cachean resultados vacíos")
    return data


@app.route("/cupones")
@require_auth
def cupones():
    try:
        data = get_cupones_cached("cupones")
    except Exception:
        data = get_benefits_by_subcategory("cupones") or {}


    user_id = get_current_user_id()
    favorites = get_user_favorites(user_id, item_type="benefit")
    favorite_ids = [item["item_id"] for item in favorites]

    return render_template(
        "cupones.html",
        benefits_by_subcategory=data,
        favoritos=favorite_ids  # 🔥 enviar al template
    )

@app.route("/beneficio/<benefit_code>/<benefit_id>")
@require_auth
def beneficio_detalle(benefit_code, benefit_id):

    benefit = get_benefit_details(benefit_code, benefit_id)

    if not benefit:
        abort(404, description="Beneficio no encontrado")

    return render_template(
        "beneficio_detalle.html",
        benefit=benefit
    )

# ---------------------------------------------------------
# PUBLIC ROUTES
# ---------------------------------------------------------

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/login")
def login():
    return render_template(
        "login.html",
        clerk_publishable_key=CLERK_PUBLISHABLE_KEY
    )

# ---------------------------------------------------------
# PRIVATE ROUTES
# ---------------------------------------------------------

@app.route("/home")
@require_auth
def home():

    user_id = get_current_user_id()
    items = get_user_items(user_id)

    profile_item = next(
        (item for item in items if item["SK"] == "PROFILE"),
        None
    )

    if not profile_item:
        return redirect(url_for("survey"))

    favorite_ids = [
        item.get("item_id")
        for item in items
        if item["SK"].startswith("FAVORITE#")
    ]

    response = get_recent_benefits()
    recomendados = response.get("data", []) if isinstance(response, dict) else []

    return render_template(
        "home.html",
        favoritos=favorite_ids,
        recomendados=recomendados
    )


@app.route("/survey", methods=["GET", "POST"])
@require_auth
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


@app.route("/intent/<intent>")
@require_auth
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
# Ejercicios
# ---------------------------------------------------------
@app.route("/ejercicios")
@require_auth
def ejercicios():
    user_id = get_current_user_id()

    data = all_items()

    favorites = []
    if user_id:
        favorites = get_user_favorites(user_id, item_type="exercise")

    favorite_ids = [item["item_id"] for item in favorites]

    return render_template(
        "ejercicios.html",
        exercises_by_target=data,
        favoritos=favorite_ids
    )

@app.route("/exercise/<exercise_id>")
@require_auth
def exercise_detail(exercise_id):

    exercise = get_exercise_by_id(exercise_id)
    print(f"Exercise Detail: {exercise}")

    if not exercise:
        return render_template("404.html"), 404

    return render_template(
        "exercise_detail.html",
        exercise=exercise
    )

@app.route("/exercise-survey", methods=["GET"])
@require_auth
def exercise_survey_page():
    return render_template("partials/exercise_survey.html")

@app.route("/exercise-survey/", methods=["POST"])
@require_auth
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

    return redirect(url_for("mis_rutinas"))



@app.route("/toggle-favorite", methods=["POST"])
@require_auth
def toggle_favorite():

    user_id = get_current_user_id()
    data = request.json

    item_id = data.get("item_id")
    item_type = data.get("item_type")
    is_active = data.get("is_active")

    if not item_id or not item_type:
        return jsonify({"error": "Missing data"}), 400

    if is_active:
        add_favorite(user_id, item_id, item_type)
    else:
        remove_favorite(user_id, item_id, item_type)

    return jsonify({"success": True})

@app.route("/toggle-dislike", methods=["POST"])
@require_auth
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
# Videos
# ---------------------------------------------------------
@app.route("/salud")
@require_auth
def videos():
    data = get_videos()
    return render_template("videos.html", data=data)

@app.route("/mis-rutinas")
@require_auth
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
            day["progress_percentage"] = int(
                (completed / total) * 100
            ) if total > 0 else 0

    return render_template("routines.html", routine=routine)

@app.route("/routine/<user_id>/<year_week>/<int:day_number>")
@require_auth
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
@require_auth
def complete_exercise_endpoint():

    data = request.get_json()

    result = complete_exercise(
        user_id=get_current_user_id(),
        year_week=data["year_week"],
        day_number=data["day_number"],
        exercise_order=data["exercise_order"]
    )

    return jsonify(result)


@app.route("/search")
@require_auth
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
# ERROR HANDLERS
# ---------------------------------------------------------

@app.errorhandler(400)
def bad_request(error):
    return render_template("error.html", message=str(error.description)), 400


@app.errorhandler(404)
def not_found(error):
    return render_template("error.html", message=str(error.description)), 404


@app.errorhandler(500)
def server_error(error):
    return render_template(
        "error.html",
        message="Ocurrió un error procesando la solicitud"
    ), 500

# ---------------------------------------------------------
# RUN
# ---------------------------------------------------------

if __name__ == "__main__":
    app.run(
        debug=os.environ.get("FLASK_ENV") == "development"
    )