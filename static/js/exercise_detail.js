document.addEventListener("DOMContentLoaded", function () {

    const favoriteBtn = document.querySelector(".favorite-btn");

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

            } catch (error) {
                console.error("Error favorito:", error);
            }

        });
    }

});