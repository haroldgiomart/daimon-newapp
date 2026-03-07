function toggleFavorite(event, button) {
  event.preventDefault();
  event.stopPropagation();

  const icon = button.querySelector("i");

  // 🔥 Alternar estado visual
  const isActive = button.classList.toggle("active");

  // Siempre usamos fa-solid (el color lo controla CSS)
  icon.classList.remove("fa-regular");
  icon.classList.add("fa-solid");

  // Animación tipo pop
  button.classList.add("pop");
  setTimeout(() => {
    button.classList.remove("pop");
  }, 300);

  const itemId = button.dataset.id;
  const itemType = button.dataset.type;

  // 🔥 Enviar al backend
  fetch("/toggle-favorite", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      item_id: itemId,
      item_type: itemType,
      is_active: isActive
    }),
  })
  .then(response => response.json())
  .then(data => {
    console.log("Backend response:", data);
  })
  .catch(error => {
    console.error("Error:", error);

    // ❗ Si falla el backend, revertimos el estado visual
    button.classList.toggle("active");
  });
}