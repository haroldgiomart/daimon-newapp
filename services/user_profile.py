

def build_user_profile(survey_data: dict) -> dict:

    tags = set()
    sentences = []

    # -----------------------------
    # Situación actual
    # -----------------------------
    situation = survey_data.get("situation")

    if situation == "Estudiante":
        tags.add("student")
        sentences.append("Soy estudiante.")

    elif situation == "Trabajador Independiente":
        tags.add("independent_worker")
        sentences.append("Trabajo de manera independiente.")

    elif situation == "Empleado":
        tags.add("employee")
        sentences.append("Trabajo como empleado.")

    elif situation == "Emprendedor":
        tags.add("entrepreneur")
        sentences.append("Soy emprendedor.")

    elif situation == "Padre/Madre":
        tags.add("parent")
        sentences.append("Soy padre o madre.")

    # -----------------------------
    # Nivel de estrés
    # -----------------------------
    stress = survey_data.get("stress_level")

    if stress == "Alto":
        tags.add("high_stress")
        sentences.append("Siento altos niveles de estrés en mi día a día y busco formas de reducirlo.")

    elif stress == "Medio":
        tags.add("medium_stress")
        sentences.append("Tengo un nivel de estrés moderado.")

    elif stress == "Bajo":
        tags.add("low_stress")
        sentences.append("Generalmente tengo bajos niveles de estrés.")

    # -----------------------------
    # En qué quiere mejorar
    # -----------------------------
    improvements = survey_data.get("improvement", [])

    if "Sueño" in improvements:
        tags.add("sleep")
        sentences.append("Quiero mejorar la calidad de mi sueño y descansar mejor.")

    if "Estrés" in improvements:
        tags.add("stress")
        sentences.append("Me interesa encontrar actividades que me ayuden a manejar mejor el estrés.")

    if "Alimentación" in improvements:
        tags.add("nutrition")
        sentences.append("Quiero mejorar mis hábitos de alimentación.")

    if "Energía Física" in improvements:
        tags.add("energy")
        sentences.append("Busco tener más energía física en mi día a día.")

    if "Actividad Física" in improvements:
        tags.add("fitness")
        sentences.append("Quiero ser más activo físicamente.")

    # -----------------------------
    # Hijos
    # -----------------------------
    if survey_data.get("has_kids") == "si":
        tags.update(["family", "kids"])
        sentences.append("Tengo hijos y valoro actividades que pueda disfrutar en familia.")

    # -----------------------------
    # Tiempo libre
    # -----------------------------
    free_time = survey_data.get("free_time", [])

    if "Películas y Series" in free_time:
        tags.add("entertainment")
        sentences.append("En mis tiempos libres me gusta ver películas y series.")

    if "Música" in free_time:
        tags.add("music")
        sentences.append("Disfruto escuchar música en mis momentos de descanso.")

    if "Ejercicio" in free_time:
        tags.add("exercise")
        sentences.append("Me gusta hacer ejercicio en mis tiempos libres.")

    if "Leer" in free_time:
        tags.add("reading")
        sentences.append("Me gusta leer en mis tiempos libres.")

    # -----------------------------
    # Resultado final
    # -----------------------------
    profile_text = " ".join(sentences)

    return {
        "tags": sorted(tags),
        "profile_text": profile_text
    }