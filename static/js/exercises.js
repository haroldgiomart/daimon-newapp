// --------------------------------------------------
// Toggle Favorite (ejercicios)
// --------------------------------------------------

async function toggleFavorite(event) {
  event.preventDefault();
  event.stopPropagation();

  const button = event.currentTarget;
  const exerciseId = button.dataset.id;
  const isActive = button.classList.contains("active");

  if (!exerciseId) {
    console.error("No exercise ID found");
    return;
  }

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

    if (!response.ok) {
      throw new Error("Error actualizando favorito");
    }

    // Toggle visual
    button.classList.toggle("active");

  } catch (error) {
    console.error("Error:", error);
  }
}


// --------------------------------------------------
// Toggle Dislike (ejercicios)
// --------------------------------------------------

async function toggleDislike(event, exerciseId) {
  event.preventDefault();
  event.stopPropagation();

  const button = event.currentTarget;
  const isActive = button.classList.contains("active");

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

    if (!response.ok) {
      throw new Error("Error actualizando dislike");
    }

    // 1️⃣ Toggle visual dislike
    button.classList.toggle("active");

    // 2️⃣ Si activamos dislike → desactivar favorito
    if (!isActive) {
      const favoriteBtn = document.querySelector(
        `.favorite-btn[data-exercise-id="${exerciseId}"]`
      );

      if (favoriteBtn && favoriteBtn.classList.contains("active")) {
        favoriteBtn.classList.remove("active");

        const img = favoriteBtn.querySelector("img");
        if (img) {
          img.src = "/assets/icons/heart-outline.svg";
        }
      }
    }

  } catch (error) {
    console.error("Error:", error);
  }
}