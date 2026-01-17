import os
import logging
from flask import (
    Flask,
    request,
    abort,
    render_template,
    session,
    redirect,
    url_for
)
from cachetools import TTLCache, cached

from services.redeem_service import redeem_benefit
from services.recent_benefits import get_recent_benefits
from services.benefits_service import get_benefits_by_subcategory
from services.benefit_details import get_benefit_details
from services.wellness_videos import get_videos
from services.user_profile import build_user_profile

# ---------------------------------------------------------
# App configuration
# ---------------------------------------------------------

app = Flask(__name__, template_folder="templates")
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "unsafe-dev-key")

# ---------------------------------------------------------
# Logging (producción)
# ---------------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------
# Cache configuration (24 horas)
# ---------------------------------------------------------

cupones_cache = TTLCache(
    maxsize=5,              # permite crecer un poco sin riesgo
    ttl=60 * 60 * 24        # 24 horas
)

@cached(cupones_cache)
def get_cupones_cached(category: str):
    """
    Cachea cupones por categoría.
    IMPORTANTE: nunca cachear funciones sin argumentos.
    """
    logger.info("Cargando cupones desde API (no cache)")
    data = get_benefits_by_subcategory(category)

    # Defensa: no cachear vacío si la API falla
    if not data:
        logger.warning("API devolvió vacío, no se cachea")
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

    if not session.get("survey_completed"):
        return redirect(url_for("survey"))

    user_tags = session.get("user_tags", [])
    logger.info("User tags: %s", user_tags)

    response = get_recent_benefits()
    recomendados = response.get("data", []) if isinstance(response, dict) else []

    # Mock favoritos (placeholder)
    mock_benefit = {
        "name": "Beneficio de prueba",
        "shortDescription": "20% de descuento en servicios",
        "country": "colombia",
        "listImages": [
            {"url": "https://via.placeholder.com/300x200"},
            {"url": "https://via.placeholder.com/300x200"}
        ]
    }

    return render_template(
        "home.html",
        favoritos=[mock_benefit, mock_benefit, mock_benefit],
        recomendados=recomendados
    )

# ---------------------------------------------------------
# Encuesta de recomendaciones
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

        session["survey_completed"] = True
        session["survey_data"] = data
        session["user_tags"] = list(user_tags)

        logger.info("Survey completada")

        return redirect(url_for("home"))

    return render_template("survey.html")

# ---------------------------------------------------------
# Cupones (cache 24h)
# ---------------------------------------------------------

@app.route("/cupones")
def cupones():
    try:
        data = get_cupones_cached("cupones")
    except Exception:
        # fallback si el cache no pudo cargarse
        logger.warning("Fallback sin cache para cupones")
        data = get_benefits_by_subcategory("cupones") or {}

    return render_template(
        "cupones.html",
        benefits_by_subcategory=data
    )

# ---------------------------------------------------------
# Detalle de beneficio
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
        response = redeem_benefit(benefit_code)

        if not response or "success" not in response:
            abort(404, description="No fue posible redimir el beneficio")

        return render_template(
            "beneficio_redencion.html",
            redeem=response["success"]
        )

    except Exception as e:
        logger.exception("Error en redención")
        abort(500)

# ---------------------------------------------------------
# Videos de salud
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