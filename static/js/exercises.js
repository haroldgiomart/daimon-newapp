// --------------------------------------------------
// Toggle Favorite (ejercicios)
// --------------------------------------------------

async function toggleFavorite(event, exerciseId) {
  event.preventDefault();
  event.stopPropagation();

  const button = event.currentTarget;
  const img = button.querySelector("img");

  const isActive = button.classList.contains("active");

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

    // Toggle visual state
    button.classList.toggle("active");

    img.src = button.classList.contains("active")
      ? "/assets/icons/heart-filled.svg"
      : "/assets/icons/heart-outline.svg";

  } catch (error) {
    console.error("Error:", error);
  }
}