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
    data = all_items()

    user_id = get_current_user_id()
    favorites = get_user_favorites(user_id, item_type="exercise")
    favorite_ids = [item["item_id"] for item in favorites]

    return render_template(
        "ejercicios.html",
        exercises_by_target=data,
        favoritos=favorite_ids
    )


@app.route("/exercise/<exercise_id>")
def exercise_detail(exercise_id):

    exercise = get_exercise_by_id(exercise_id)

    if not exercise:
        return render_template("404.html"), 404

    return render_template(
        "exercise_detail.html",
        exercise=exercise
    )


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