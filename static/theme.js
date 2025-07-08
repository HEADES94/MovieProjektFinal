// Theme Management System
class ThemeManager {
    constructor() {
        this.init();
    }

    async init() {
        // Lade Theme vom Backend wenn eingeloggt, sonst lokaler Storage
        let savedTheme = 'system';

        try {
            // Versuche Theme vom Backend zu laden
            const response = await fetch('/api/theme');
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    savedTheme = data.theme;
                }
            }
        } catch (error) {
            // Fallback zu localStorage wenn Backend nicht verfügbar
            savedTheme = localStorage.getItem('theme') || 'system';
        }

        this.setTheme(savedTheme);

        // Event Listener für Theme-Änderungen
        this.setupEventListeners();

        // Überwache System-Theme-Änderungen
        this.watchSystemTheme();
    }

    async setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);

        // Update Theme-Selector if it exists
        const themeSelector = document.querySelector('select[name="theme"]');
        if (themeSelector) {
            themeSelector.value = theme;
        }

        // Update any theme toggle buttons
        this.updateThemeButtons(theme);

        // Speichere Theme im Backend wenn eingeloggt
        try {
            await fetch('/api/theme', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ theme })
            });
        } catch (error) {
            console.log('Theme could not be saved to backend:', error);
        }
    }

    getTheme() {
        return localStorage.getItem('theme') || 'system';
    }

    setupEventListeners() {
        // Listen for theme selector changes
        document.addEventListener('change', (e) => {
            if (e.target.name === 'theme') {
                this.setTheme(e.target.value);
            }
        });

        // Listen for theme toggle buttons
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('theme-toggle')) {
                const newTheme = e.target.dataset.theme;
                this.setTheme(newTheme);

                // Show notification
                if (window.toastManager) {
                    toastManager.show(`Theme auf ${newTheme === 'light' ? 'Hell' : newTheme === 'dark' ? 'Dunkel' : 'System'} geändert`, 'info', 2000);
                }
            }
        });
    }

    watchSystemTheme() {
        // Watch for system theme changes
        if (window.matchMedia) {
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
                if (this.getTheme() === 'system') {
                    // Trigger re-evaluation of system theme
                    this.setTheme('system');
                }
            });
        }
    }

    updateThemeButtons(currentTheme) {
        const themeButtons = document.querySelectorAll('.theme-toggle');
        themeButtons.forEach(button => {
            button.classList.remove('active');
            if (button.dataset.theme === currentTheme) {
                button.classList.add('active');
            }
        });
    }

    // Utility method to get effective theme (resolves 'system' to actual theme)
    getEffectiveTheme() {
        const theme = this.getTheme();
        if (theme === 'system') {
            return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
        }
        return theme;
    }
}

// Initialize Theme Manager
const themeManager = new ThemeManager();

// Export for use in other scripts
window.themeManager = themeManager;

// Enhanced Interactive Features
document.addEventListener('DOMContentLoaded', function() {
    // Add smooth scrolling to all anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Add cosmic particles animation
    createCosmicParticles();

    // Add shooting stars
    createShootingStars();

    // Add interactive card effects
    addCardInteractions();

    // Add form enhancements
    enhanceForms();
});

// Create animated cosmic particles
function createCosmicParticles() {
    const particleContainer = document.createElement('div');
    particleContainer.className = 'background-particles';
    document.body.appendChild(particleContainer);

    // Create stars
    const starsContainer = document.createElement('div');
    starsContainer.className = 'stars';

    for (let i = 0; i < 10; i++) {
        const star = document.createElement('div');
        star.className = 'star';
        starsContainer.appendChild(star);
    }

    document.body.appendChild(starsContainer);
}

// Create shooting stars animation
function createShootingStars() {
    setInterval(() => {
        if (Math.random() < 0.1) { // 10% chance every interval
            const shootingStar = document.createElement('div');
            shootingStar.className = 'shooting-star';

            // Random starting position
            shootingStar.style.left = Math.random() * 100 + '%';
            shootingStar.style.top = Math.random() * 100 + '%';

            document.body.appendChild(shootingStar);

            // Remove after animation
            setTimeout(() => {
                shootingStar.remove();
            }, 3000);
        }
    }, 2000);
}

// Add interactive effects to cards
function addCardInteractions() {
    const cards = document.querySelectorAll('.card, .movie-card, .profile-card');

    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-8px) scale(1.02)';
        });

        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });
}

// Enhance forms with better UX
function enhanceForms() {
    const inputs = document.querySelectorAll('.form-input');

    inputs.forEach(input => {
        // Add floating label effect
        const label = input.previousElementSibling;
        if (label && label.classList.contains('form-label')) {
            input.addEventListener('focus', () => {
                label.style.transform = 'translateY(-20px) scale(0.9)';
                label.style.color = 'var(--primary)';
            });

            input.addEventListener('blur', () => {
                if (!input.value) {
                    label.style.transform = 'translateY(0) scale(1)';
                    label.style.color = 'var(--text-secondary)';
                }
            });
        }

        // Add input validation styling
        input.addEventListener('input', function() {
            if (this.validity.valid) {
                this.style.borderColor = 'var(--success)';
            } else {
                this.style.borderColor = 'var(--error)';
            }
        });
    });
}

// Toast notification system
class ToastManager {
    constructor() {
        this.container = this.createContainer();
    }

    createContainer() {
        const container = document.createElement('div');
        container.className = 'toast-container';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            pointer-events: none;
        `;
        document.body.appendChild(container);
        return container;
    }

    show(message, type = 'info', duration = 5000) {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        toast.style.pointerEvents = 'auto';

        // Add close button
        const closeBtn = document.createElement('button');
        closeBtn.innerHTML = '×';
        closeBtn.style.cssText = `
            background: none;
            border: none;
            color: white;
            font-size: 20px;
            margin-left: 10px;
            cursor: pointer;
        `;
        closeBtn.onclick = () => this.remove(toast);
        toast.appendChild(closeBtn);

        this.container.appendChild(toast);

        // Auto-remove after duration
        setTimeout(() => {
            this.remove(toast);
        }, duration);
    }

    remove(toast) {
        toast.style.transform = 'translateX(100%)';
        toast.style.opacity = '0';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }
}

// Initialize Toast Manager
const toastManager = new ToastManager();
window.toastManager = toastManager;

// Enhanced Search functionality
class SearchManager {
    constructor() {
        this.searchInput = document.querySelector('.search-input');
        this.debounceTimer = null;
        this.init();
    }

    init() {
        if (this.searchInput) {
            this.searchInput.addEventListener('input', (e) => {
                clearTimeout(this.debounceTimer);
                this.debounceTimer = setTimeout(() => {
                    this.performSearch(e.target.value);
                }, 300);
            });
        }
    }

    performSearch(query) {
        // Add loading state
        const searchIcon = document.querySelector('.search-icon');
        if (searchIcon) {
            searchIcon.innerHTML = '<div class="loading-spinner"></div>';
        }

        // Perform search (this would typically make an API call)
        // For now, we'll just filter visible elements
        this.filterMovies(query);

        // Reset search icon
        setTimeout(() => {
            if (searchIcon) {
                searchIcon.innerHTML = '🔍';
            }
        }, 500);
    }

    filterMovies(query) {
        const movieCards = document.querySelectorAll('.movie-card');
        const lowerQuery = query.toLowerCase();

        movieCards.forEach(card => {
            const title = card.querySelector('.movie-title')?.textContent.toLowerCase();
            const year = card.querySelector('.movie-year')?.textContent.toLowerCase();

            if (title?.includes(lowerQuery) || year?.includes(lowerQuery) || !query) {
                card.style.display = 'block';
                card.style.animation = 'fadeIn 0.3s ease-in-out';
            } else {
                card.style.display = 'none';
            }
        });
    }
}

// Initialize Search Manager
const searchManager = new SearchManager();

// Add fade-in animation keyframes
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
`;
document.head.appendChild(style);

// Performance optimization: Lazy loading for images
function initLazyLoading() {
    const images = document.querySelectorAll('img[data-src]');

    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                observer.unobserve(img);
            }
        });
    });

    images.forEach(img => imageObserver.observe(img));
}

// Initialize lazy loading when DOM is ready
document.addEventListener('DOMContentLoaded', initLazyLoading);

// Handle flash messages with enhanced styling
document.addEventListener('DOMContentLoaded', function() {
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(msg => {
        const type = msg.classList.contains('success') ? 'success' :
                    msg.classList.contains('error') ? 'error' :
                    msg.classList.contains('warning') ? 'warning' : 'info';

        toastManager.show(msg.textContent, type);
        msg.remove(); // Remove the original flash message
    });
});

// Add keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Theme toggle with Ctrl+Shift+T
    if (e.ctrlKey && e.shiftKey && e.key === 'T') {
        e.preventDefault();
        const currentTheme = themeManager.getTheme();
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        themeManager.setTheme(newTheme);
        toastManager.show(`Theme changed to ${newTheme}`, 'info');
    }

    // Search focus with Ctrl+K
    if (e.ctrlKey && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.querySelector('.search-input');
        if (searchInput) {
            searchInput.focus();
        }
    }
});

// Add smooth page transitions
function addPageTransitions() {
    const links = document.querySelectorAll('a:not([href^="#"]):not([href^="javascript:"]):not([target="_blank"])');

    links.forEach(link => {
        link.addEventListener('click', function(e) {
            if (this.hostname === window.location.hostname) {
                e.preventDefault();
                document.body.style.opacity = '0.8';
                document.body.style.transform = 'scale(0.98)';

                setTimeout(() => {
                    window.location.href = this.href;
                }, 150);
            }
        });
    });
}

// Initialize page transitions
document.addEventListener('DOMContentLoaded', addPageTransitions);

// Add scroll-based animations
function addScrollAnimations() {
    const animatedElements = document.querySelectorAll('.card, .movie-card, .stat-card');

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.animation = 'fadeInUp 0.6s ease-out';
            }
        });
    }, {
        threshold: 0.1
    });

    animatedElements.forEach(el => observer.observe(el));
}

// Add fadeInUp animation
const fadeInUpStyle = document.createElement('style');
fadeInUpStyle.textContent = `
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
`;
document.head.appendChild(fadeInUpStyle);

// Initialize scroll animations
document.addEventListener('DOMContentLoaded', addScrollAnimations);
