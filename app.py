from flask import Flask, request, abort, render_template
from services.redeem_service import redeem_benefit
from services.recent_benefits import get_recent_benefits
from services.benefits_service import get_benefits_by_subcategory
from services.benefit_details import get_benefit_details

app = Flask(__name__, template_folder="templates")


@app.route("/")
def landing():
    return render_template("landing.html")

@app.route("/home")
def home():
    # MOCK DATA para home

    data = get_recent_benefits()
    data = data['data']

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
        recomendados=data
        #recomendados=[mock_benefit, mock_benefit]

    )


@app.route("/cupones")
def cupones():

    data = get_benefits_by_subcategory()
    print(f"Subcategorías: {len(data)}")

    return render_template(
        "cupones.html",
        benefits_by_subcategory=data
    )

@app.route("/beneficio/<benefit_code>/<benefit_id>")
def beneficio_detalle(benefit_code, benefit_id):

    benefit = get_benefit_details(benefit_code, benefit_id)

    if not benefit:
        return "Beneficio no encontrado", 404

    return render_template(
        "beneficio_detalle.html",
        benefit=benefit
    )

@app.route("/beneficio/<benefit_id>/redimir", methods=["GET"])
def beneficio_redimir(benefit_id):

    benefit_code = request.args.get("benefitCode")
    benefit_code = benefit_code[1:]
    print(f"El Código del Beneficio es: {benefit_code}")

    if not benefit_code:
        abort(400, description="benefitCode es requerido")

    try:
        response = redeem_benefit(benefit_code)

        # Validación básica de respuesta
        if not response or "success" not in response:
            abort(404, description="No fue posible redimir el beneficio")

        redeem_data = response["success"]

        return render_template(
            "beneficio_redencion.html",
            redeem=redeem_data
        )

    except Exception as e:
        print("Error en redención:", e)
        abort(500, description="Error interno al redimir el beneficio")



# --------------------------------------------------------- Handlers de Error
@app.errorhandler(400)
def bad_request(error):
    return render_template(
        "error.html",
        message=str(error)
    ), 400


@app.errorhandler(404)
def not_found(error):
    return render_template(
        "error.html",
        message=str(error)
    ), 404


@app.errorhandler(500)
def server_error(error):
    return render_template(
        "error.html",
        message="Ocurrió un error procesando la redención"
    ), 500


if __name__ == "__main__":
    app.run(debug=True)