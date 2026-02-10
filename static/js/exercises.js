<script>
async function loadExercises() {
  const res = await fetch('/api/exercises');
  const exercises = await res.json();

  const grid = document.getElementById('exerciseGrid');
  grid.innerHTML = '';

  exercises.forEach(ex => {

    const difficulty = ex.difficultyLevel.toLowerCase();
    const difficultyLabel =
      difficulty.charAt(0).toUpperCase() + difficulty.slice(1);

    const secondaryTags = ex.secondaryMuscles
      .map(m => `<span class="tag">${m}</span>`)
      .join('');

    const card = document.createElement('div');
    card.className = 'exercise-card';

    card.innerHTML = `
      <a class="exercise-image" href="/exercise-detail.html?id=${ex.id}">
        <img src="${ex.img_static}" alt="${ex.name}">

        <span class="difficulty-badge difficulty-${difficulty}">
          ${difficultyLabel}
        </span>

        <button class="favorite-btn"
                onclick="toggleFavorite(event, '${ex.id}')">
          <!-- AQUÍ VA TU ICONO REAL -->
          <img src="/assets/icons/heart-outline.svg" alt="favorito">
        </button>
      </a>

      <div class="exercise-info">
        <small>Dificultad: <strong>${difficultyLabel}</strong></small>

        <div class="muscle-tags">
          ${secondaryTags}
        </div>
      </div>
    `;

    grid.appendChild(card);
  });
}

function toggleFavorite(e, id) {
  e.preventDefault();
  e.stopPropagation();

  console.log('Favorito:', id);
  // aquí conectas backend o localStorage
}

loadExercises();
</script>