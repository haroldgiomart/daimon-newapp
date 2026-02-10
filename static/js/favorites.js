function toggleFavorite(event, button) {
  event.stopPropagation();
  event.preventDefault();

  const icon = button.querySelector("i");
  const isActive = button.classList.toggle("active");

  // Cambiar icono 🤍 / ❤️
  icon.classList.toggle("fa-solid", isActive);
  icon.classList.toggle("fa-regular", !isActive);

  // Animación
  button.classList.add("pop");
  setTimeout(() => button.classList.remove("pop"), 300);

  const exerciseId = button.dataset.id;

  // TODO: conectar backend
  console.log("Favorite toggled:", exerciseId, isActive);
}