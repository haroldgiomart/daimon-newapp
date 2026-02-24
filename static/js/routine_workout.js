document.addEventListener("DOMContentLoaded", function () {

    const nextButton = document.getElementById("btn-next");
    const finishButton = document.getElementById("btn-finish");
    const indexInput = document.getElementById("exercise-index");
    const form = document.getElementById("workout-form");

    const favoriteBtn = document.querySelector(".favorite-btn");
    const dislikeBtn = document.querySelector(".dislike-btn");

    // ==================================================
    // 🔥 FINALIZAR EJERCICIO
    // ==================================================
    async function completeExercise(button, goNext = true) {

        const yearWeek = button.dataset.yearWeek;
        const dayNumber = parseInt(button.dataset.dayNumber);
        const exerciseOrder = parseInt(button.dataset.exerciseOrder);

        try {

            const response = await fetch("/complete-exercise", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    year_week: yearWeek,
                    day_number: dayNumber,
                    exercise_order: exerciseOrder
                })
            });

            if (!response.ok) {
                throw new Error("Error completando ejercicio");
            }

            // 🔹 Si hay siguiente ejercicio → avanzar
            if (goNext && nextButton) {
                let current = parseInt(indexInput.value);
                indexInput.value = current + 1;
                form.submit();
            }

            // 🔹 Si es el último → redirigir
            if (!goNext && finishButton) {
                const redirectUrl = finishButton.dataset.redirect;
                window.location.href = redirectUrl;
            }

        } catch (error) {
            console.error("Error completeExercise:", error);
        }
    }

    // --------------------------------------------------
    // Botón siguiente ejercicio
    // --------------------------------------------------
    if (nextButton) {
        nextButton.addEventListener("click", function () {
            completeExercise(this, true);
        });
    }

    // --------------------------------------------------
    // Botón finalizar rutina
    // --------------------------------------------------
    if (finishButton) {
        finishButton.addEventListener("click", function () {
            completeExercise(this, false);
        });
    }

    // ==================================================
    // FAVORITO
    // ==================================================
    if (favoriteBtn) {
        favoriteBtn.addEventListener("click", async function () {

            const exerciseId = this.dataset.exerciseId;
            const isActive = this.classList.contains("active");

            try {
                const response = await fetch("/toggle-favorite", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        item_id: exerciseId,
                        item_type: "exercise",
                        is_active: !isActive
                    })
                });

                if (!response.ok) throw new Error("Error favorito");

                this.classList.toggle("active");

                if (!isActive && dislikeBtn) {
                    dislikeBtn.classList.remove("active");
                }

            } catch (error) {
                console.error("Error favorito:", error);
            }
        });
    }

    // ==================================================
    // DISLIKE
    // ==================================================
    if (dislikeBtn) {
        dislikeBtn.addEventListener("click", async function () {

            const exerciseId = this.dataset.exerciseId;
            const isActive = this.classList.contains("active");

            try {
                const response = await fetch("/toggle-dislike", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        item_id: exerciseId,
                        item_type: "exercise",
                        is_active: !isActive
                    })
                });

                if (!response.ok) throw new Error("Error dislike");

                this.classList.toggle("active");

                if (!isActive && favoriteBtn) {
                    favoriteBtn.classList.remove("active");
                }

            } catch (error) {
                console.error("Error dislike:", error);
            }
        });
    }

});