document.addEventListener("DOMContentLoaded", function () {

  const modal = document.getElementById("exerciseSurveyModal");
  if (!modal) return;

  // 🔥 Forzar que el modal viva directamente en <body>
  document.body.appendChild(modal);

  const steps = modal.querySelectorAll(".step");
  const dots = modal.querySelectorAll(".dot");
  const form = document.getElementById("exerciseSurveyForm");
  const skipBtn = document.getElementById("skipSurvey");

  let currentStep = 0;

  // 🔥 Aplicar blur solo al contenido principal
  const content = document.querySelector(".app-content");
  if (content) content.classList.add("blur-content");

  // 🔥 Bloquear scroll mientras el modal está activo
  document.body.style.overflow = "hidden";

  // =========================
  // STEPPER
  // =========================
  function updateStepper() {
    dots.forEach(dot => dot.classList.remove("active"));
    if (dots[currentStep]) {
      dots[currentStep].classList.add("active");
    }
  }

  function showStep(index) {
    steps.forEach(step => step.classList.remove("active"));
    if (steps[index]) {
      steps[index].classList.add("active");
      currentStep = index;
      updateStepper();
    }
  }

  // =========================
  // AVANZAR AUTOMÁTICAMENTE
  // =========================
  modal.querySelectorAll("input[type='radio']").forEach(input => {
    input.addEventListener("change", () => {

      if (currentStep < steps.length - 1) {
        showStep(currentStep + 1);
      } else {
        submitSurvey();
      }

    });
  });

  // =========================
  // ENVIAR ENCUESTA
  // =========================
  function submitSurvey() {
    const formData = new FormData(form);

    fetch("/exercise-survey/", {
      method: "POST",
      body: formData
    })
    .then(response => {
      if (!response.ok) {
        throw new Error("Error guardando encuesta");
      }
      closeSurvey();
    })
    .catch(error => {
      console.error("Survey error:", error);
    });
  }

  // =========================
  // CERRAR MODAL
  // =========================
  function closeSurvey() {
    modal.remove();
    if (content) content.classList.remove("blur-content");
    document.body.style.overflow = "auto";
  }

  // =========================
  // BOTÓN SALTAR
  // =========================
  if (skipBtn) {
    skipBtn.addEventListener("click", function(e) {
      e.preventDefault();
      closeSurvey();
    });
  }

});