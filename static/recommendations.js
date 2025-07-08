/**
 * Enhanced Movie Recommendations JavaScript
 * Verbesserte AJAX-Funktionalität mit Error Handling und Loading States
 */

class MovieRecommendations {
    constructor() {
        this.init();
    }

    init() {
        this.bindEvents();
        this.setupTooltips();
    }

    bindEvents() {
        // Generate AI Recommendation Button
        const generateBtn = document.getElementById('generate-ai-recommendation');
        if (generateBtn) {
            generateBtn.addEventListener('click', (e) => this.generateRecommendation(e));
        }

        // Similar Movies Load More
        const loadMoreBtn = document.getElementById('load-more-similar');
        if (loadMoreBtn) {
            loadMoreBtn.addEventListener('click', (e) => this.loadMoreSimilar(e));
        }
    }

    async generateRecommendation(event) {
        event.preventDefault();

        const button = event.target;
        const movieId = button.dataset.movieId;
        const container = document.getElementById('ai-recommendation-content');

        if (!movieId || !container) return;

        // Show loading state
        this.showLoading(button, 'Generiere Empfehlung...');
        container.innerHTML = '<div class="loading-spinner">Lade KI-Empfehlung...</div>';

        try {
            const response = await fetch(`/movies/${movieId}/recommendation/generate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (data.recommendation) {
                this.displayRecommendation(container, data.recommendation);
                this.showToast('KI-Empfehlung erfolgreich generiert!', 'success');
            } else {
                throw new Error('Keine Empfehlung erhalten');
            }

        } catch (error) {
            console.error('Fehler beim Generieren der Empfehlung:', error);
            container.innerHTML = `
                <div class="error-message">
                    <i class="fas fa-exclamation-triangle"></i>
                    Fehler beim Laden der Empfehlung: ${error.message}
                </div>
            `;
            this.showToast('Fehler beim Generieren der Empfehlung', 'error');
        } finally {
            this.hideLoading(button, 'Neue Empfehlung generieren');
        }
    }

    displayRecommendation(container, recommendation) {
        const movie = recommendation.movie;
        container.innerHTML = `
            <div class="ai-rec-info fade-in">
                <div class="recommendation-movie">
                    <div class="movie-poster-small">
                        <img src="${movie.poster || '/static/default_poster.jpg'}"
                             alt="${movie.title}"
                             onerror="this.src='/static/default_poster.jpg'">
                    </div>
                    <div class="movie-details">
                        <h4>${this.escapeHtml(movie.title)}</h4>
                        <p><strong>Regisseur:</strong> ${this.escapeHtml(movie.director || 'Unbekannt')}</p>
                        <p><strong>Jahr:</strong> ${movie.year || 'Unbekannt'}</p>
                        <p><strong>Genre:</strong> ${this.escapeHtml(movie.genre || 'Unbekannt')}</p>
                        <p class="movie-plot">${this.escapeHtml(movie.plot || 'Keine Beschreibung verfügbar')}</p>
                    </div>
                </div>
                <div class="ai-explanation">
                    <h5>Warum diese Empfehlung?</h5>
                    <p>${this.escapeHtml(recommendation.reasoning || 'KI-basierte Empfehlung')}</p>
                </div>
            </div>
        `;
    }

    async loadMoreSimilar(event) {
        event.preventDefault();

        const button = event.target;
        const movieId = button.dataset.movieId;
        const container = document.getElementById('similar-movies-container');

        this.showLoading(button, 'Lade weitere Filme...');

        try {
            const response = await fetch(`/movies/${movieId}/similar?limit=8`);
            const data = await response.json();

            if (data.similar_movies && data.similar_movies.length > 0) {
                this.appendSimilarMovies(container, data.similar_movies);
                button.style.display = 'none'; // Hide load more button
            } else {
                this.showToast('Keine weiteren ähnlichen Filme gefunden', 'info');
            }

        } catch (error) {
            console.error('Fehler beim Laden ähnlicher Filme:', error);
            this.showToast('Fehler beim Laden der Filme', 'error');
        } finally {
            this.hideLoading(button, 'Weitere Filme laden');
        }
    }

    appendSimilarMovies(container, movies) {
        movies.forEach(movie => {
            const movieCard = this.createMovieCard(movie);
            container.appendChild(movieCard);
        });
    }

    createMovieCard(movie) {
        const card = document.createElement('div');
        card.className = 'movie-card fade-in';
        card.innerHTML = `
            <div class="movie-poster">
                <img src="${movie.poster_url || '/static/default_poster.jpg'}"
                     alt="${movie.title}"
                     onerror="this.src='/static/default_poster.jpg'">
                <div class="movie-overlay">
                    <h4>${this.escapeHtml(movie.title)}</h4>
                    <p>${movie.release_year || ''} • ${this.escapeHtml(movie.genre || '')}</p>
                    <div class="rating">
                        <i class="fas fa-star"></i>
                        ${movie.rating || 'N/A'}
                    </div>
                </div>
            </div>
        `;

        // Add click event to navigate to movie details
        card.addEventListener('click', () => {
            window.location.href = `/movies/${movie.id}`;
        });

        return card;
    }

    showLoading(button, originalText = 'Laden...') {
        button.disabled = true;
        button.dataset.originalText = button.textContent;
        button.innerHTML = `<div class="loading-spinner"></div> ${originalText}`;
    }

    hideLoading(button, newText = null) {
        button.disabled = false;
        button.innerHTML = newText || button.dataset.originalText || 'Laden';
    }

    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;

        document.body.appendChild(toast);

        // Auto-remove after 3 seconds
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }, 3000);
    }

    setupTooltips() {
        // Simple tooltip implementation
        const tooltipElements = document.querySelectorAll('[data-tooltip]');
        tooltipElements.forEach(element => {
            element.addEventListener('mouseenter', this.showTooltip);
            element.addEventListener('mouseleave', this.hideTooltip);
        });
    }

    showTooltip(event) {
        const tooltip = document.createElement('div');
        tooltip.className = 'tooltip';
        tooltip.textContent = event.target.dataset.tooltip;
        document.body.appendChild(tooltip);

        const rect = event.target.getBoundingClientRect();
        tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
        tooltip.style.top = rect.top - tooltip.offsetHeight - 8 + 'px';
    }

    hideTooltip() {
        const tooltip = document.querySelector('.tooltip');
        if (tooltip) {
            tooltip.remove();
        }
    }

    getCSRFToken() {
        const token = document.querySelector('meta[name=csrf-token]');
        return token ? token.getAttribute('content') : '';
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new MovieRecommendations();
});

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MovieRecommendations;
}
