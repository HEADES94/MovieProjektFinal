document.addEventListener('DOMContentLoaded', function() {
    // Cache für Poster-URLs
    const posterCache = new Map();
    const defaultPosterUrl = '/static/default_poster.jpg';

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

            if (data.similar_movies) {
                // Verarbeite alle Filme auf einmal
                const container = document.createElement('div');
                container.className = 'similar-movies-grid';

                data.similar_movies.forEach(movie => {
                    const movieElement = createMovieElement(movie);
                    container.appendChild(movieElement);
                });

                // Füge alle Filme auf einmal zum DOM hinzu
                const targetElement = document.querySelector('.similar-movies-section') || document.body;
                targetElement.appendChild(container);
            }
        } catch (error) {
            console.error('Fehler beim Laden der Empfehlungen:', error);
        }
    }

    // Erstelle ein einzelnes Film-Element
    function createMovieElement(movie) {
        const element = document.createElement('div');
        element.className = 'movie-card glass-card';

        // Verwende data-src für Lazy Loading
        const posterUrl = movie.poster_url || defaultPosterUrl;

        element.innerHTML = `
            <img data-src="${posterUrl}"
                 alt="${movie.title}"
                 class="lazy-load movie-poster"
                 loading="lazy">
            <div class="movie-info">
                <h3>${movie.title}</h3>
                <p>${movie.release_year}</p>
            </div>
        `;

        return element;
    }

    // Lazy Loading für Bilder
    function initLazyLoading() {
        const lazyImages = document.querySelectorAll('img.lazy-load');

        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.classList.remove('lazy-load');
                        observer.unobserve(img);
                    }
                });
            });

            lazyImages.forEach(img => imageObserver.observe(img));
        } else {
            // Fallback für ältere Browser
            lazyImages.forEach(img => {
                img.src = img.dataset.src;
                img.classList.remove('lazy-load');
            });
        }
    }

    // Initialisiere Lazy Loading
    initLazyLoading();

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
