document.addEventListener('DOMContentLoaded', function() {
    // Wenn wir auf einer Film-Detailseite sind
    const movieId = document.querySelector('[data-movie-id]')?.dataset.movieId;
    if (movieId) {
        loadSimilarMovies(movieId);
    }

    // Lade ähnliche Filme
    async function loadSimilarMovies(movieId) {
        try {
            const response = await fetch(`/movies/${movieId}/similar`);
            const data = await response.json();

            if (data.recommendation) {
                displayRecommendation(data.recommendation);
            }
        } catch (error) {
            console.error('Fehler beim Laden der Empfehlungen:', error);
        }
    }

    // Zeige Empfehlung an
    function displayRecommendation(recommendation) {
        const container = document.createElement('div');
        container.className = 'recommendation-container glass-card fade-in';

        const content = `
            <h3 class="gradient-text">Ähnlicher Film</h3>
            <div class="recommendation-content">
                <h4>${recommendation.title} (${recommendation.year})</h4>
                <p class="director">Regie: ${recommendation.director}</p>
                <p class="reasoning">${recommendation.reasoning}</p>
                <div class="similarity-aspects">
                    <h5>Warum dieser Film?</h5>
                    <ul>
                        ${recommendation.similarity_aspects.map(aspect =>
                            `<li>${aspect}</li>`
                        ).join('')}
                    </ul>
                </div>
                ${recommendation.movie_id ?
                    `<a href="/movies/${recommendation.movie_id}" class="btn-primary">Zum Film</a>` :
                    ''}
            </div>
        `;

        container.innerHTML = content;

        // Füge die Empfehlung zur Seite hinzu
        const targetElement = document.querySelector('.movie-details') || document.body;
        targetElement.appendChild(container);
    }

    // Formular für personalisierte Empfehlungen
    const preferenceForm = document.getElementById('preferenceForm');
    if (preferenceForm) {
        preferenceForm.addEventListener('submit', async function(e) {
            e.preventDefault();

            const formData = new FormData(this);
            try {
                const response = await fetch('/recommend', {
                    method: 'POST',
                    body: formData
                });

                // Aktualisiere die Seite mit der Antwort
                const html = await response.text();
                document.documentElement.innerHTML = html;

                // Initialisiere Event-Listener neu
                initializeEventListeners();
            } catch (error) {
                console.error('Fehler beim Senden der Vorlieben:', error);
            }
        });
    }
});
