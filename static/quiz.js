document.addEventListener('DOMContentLoaded', function() {
    // Quiz-Elemente
    const quizContainer = document.querySelector('.quiz-container');
    const quizContent = document.getElementById('quizContent');
    const questionSection = document.querySelector('.question-section');
    const progressBar = document.querySelector('.progress');
    const questionCounter = document.querySelector('.question-counter');
    const currentScore = document.querySelector('.current-score');
    const prevButton = document.getElementById('prevQuestion');
    const nextButton = document.getElementById('nextQuestion');
    const submitButton = document.getElementById('submitQuiz');
    const resultsSection = document.getElementById('results');

    // Quiz-Variablen
    let currentQuestionIndex = 0;
    let score = 0;
    let userAnswers = {};
    const questions = document.querySelectorAll('.question-container');
    const totalQuestions = questions.length;
    const difficulty = document.getElementById('selectedDifficulty')?.value || 'mittel';

    // Show first question
    if (questions.length > 0) {
        questions[0].style.display = 'block';
    }

    function updateProgress() {
        const progress = ((currentQuestionIndex + 1) / totalQuestions) * 100;
        progressBar.style.width = `${progress}%`;
        questionCounter.textContent = `Frage ${currentQuestionIndex + 1} von ${totalQuestions}`;

        // Aktualisiere die Punktzahl sofort nach jeder Antwort
        updateScore();

        questions.forEach((q, index) => {
            q.style.display = index === currentQuestionIndex ? 'block' : 'none';
        });

        // Verbesserte Button-Steuerung
        prevButton.disabled = currentQuestionIndex === 0;
        if (currentQuestionIndex === totalQuestions - 1) {
            nextButton.style.display = 'none';
            submitButton.style.display = 'block';
            submitButton.disabled = !questions[currentQuestionIndex].querySelector('.option.selected');
        } else {
            nextButton.style.display = 'block';
            submitButton.style.display = 'none';
        }
    }

    function updateScore() {
        const correctAnswers = Object.values(userAnswers).filter(answer => {
            const questionId = Object.keys(userAnswers).find(key => userAnswers[key] === answer);
            const questionElement = document.querySelector(`[data-question-index="${questionId.split('_')[1]}"]`);
            return questionElement && answer === questionElement.dataset.correctAnswer;
        }).length;

        score = correctAnswers * (difficulty === 'schwer' ? 200 : 100);
        currentScore.textContent = `Punktzahl: ${score}`;
    }

    // Funktion zum Abrufen des CSRF-Tokens
    function getCsrfToken() {
        return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    }

    // Event-Listener für Navigation
    if (prevButton) {
        prevButton.addEventListener('click', () => {
            if (currentQuestionIndex > 0) {
                currentQuestionIndex--;
                updateProgress();
            }
        });
    }

    if (nextButton) {
        nextButton.addEventListener('click', () => {
            const currentQuestion = questions[currentQuestionIndex];
            const selectedOption = currentQuestion.querySelector('.option.selected');

            if (selectedOption) {
                if (currentQuestionIndex < totalQuestions - 1) {
                    currentQuestionIndex++;
                    updateProgress();
                }
            } else {
                alert('Bitte wähle eine Antwort aus!');
            }
        });
    }

    // Event-Listener für Antworten
    questions.forEach((question) => {
        const options = question.querySelectorAll('.option');
        const questionIndex = question.dataset.questionIndex;

        options.forEach(option => {
            option.addEventListener('click', function() {
                options.forEach(opt => opt.classList.remove('selected'));
                this.classList.add('selected');
                userAnswers[`question_${questionIndex}`] = this.dataset.value;

                if (currentQuestionIndex === totalQuestions - 1) {
                    submitButton.disabled = false;
                }

                updateProgress();
            });
        });
    });

    // Quiz-Einreichung
    if (submitButton) {
        submitButton.addEventListener('click', function() {
            const formData = {
                answers: {},
                difficulty: difficulty
            };

            questions.forEach((question) => {
                const selectedOption = question.querySelector('.option.selected');
                const questionId = question.getAttribute('data-question-id');
                if (selectedOption && questionId) {
                    formData.answers[questionId] = selectedOption.dataset.value;
                }
            });

            const movieId = window.location.pathname.split('/')[2];

            fetch(`/quiz/${movieId}/submit`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Verstecke den Quiz-Inhalt
                    questionSection.style.display = 'none';

                    // ACHIEVEMENTS-BANNER
                    let achievementsBanner = '';
                    if (data.achievements && data.achievements.length > 0) {
                        achievementsBanner = `
                        <div class="achievement-banner" style="background: #10b98122; border-left: 6px solid #10b981; padding: 1.5rem; margin-bottom: 2rem; border-radius: 8px; animation: fadeIn 1s;">
                            <h2 style="color: #10b981; margin-bottom: 0.5rem;">🎉 Neuer Erfolg freigeschaltet!</h2>
                            ${data.achievements.map(a => `
                                <div style="margin-bottom: 1rem;">
                                    <span style="font-size:2rem;">${a.title.split(' ')[0]}</span>
                                    <span style="font-weight:bold; color:#10b981;">${a.title}</span><br>
                                    <span style="color:#222;">${a.description}</span>
                                </div>
                            `).join('')}
                        </div>`;
                    }

                    // Erstelle die Zusammenfassung der Fragen
                    const questionsHtml = data.answered_questions.map((q, index) => `
                        <div class="question-result ${q.is_correct ? 'correct' : 'incorrect'}">
                            <h4>Frage ${index + 1}</h4>
                            <p>${q.question}</p>
                            <p class="user-answer">
                                Deine Antwort: <span class="${q.is_correct ? 'text-success' : 'text-danger'}">${q.user_answer}</span>
                            </p>
                            ${!q.is_correct ? `
                                <p class="correct-answer">
                                    Richtige Antwort: <span class="text-success">${q.correct_answer}</span>
                                </p>
                            ` : ''}
                        </div>
                    `).join('');

                    // Erstelle die Ergebnisanzeige
                    resultsSection.innerHTML = `
                        <div class="quiz-results">
                            <h2>Quiz abgeschlossen! 🎉</h2>
                            <div class="score-info">
                                <div class="score-circle">
                                    <span class="score-number">${data.score}</span>
                                    <span class="score-label">Punkte</span>
                                </div>
                            </div>
                            <div class="quiz-stats">
                                <p>Richtige Antworten: <strong>${data.correct_count}</strong> von <strong>${data.total_questions}</strong></p>
                                <div class="progress-bar">
                                    <div class="progress" style="width: ${(data.correct_count / data.total_questions) * 100}%"></div>
                                </div>
                            </div>
                            ${achievementsBanner}
                            <div class="questions-summary">
                                <h3>Zusammenfassung</h3>
                                ${questionsHtml}
                            </div>
                            <div class="quiz-actions">
                                <a href="/quiz" class="btn btn-primary">Zurück zur Quiz-Übersicht</a>
                                <a href="/quiz/${movieId}?difficulty=${difficulty}" class="btn btn-secondary">Erneut versuchen</a>
                            </div>
                        </div>
                    `;

                    // Zeige die Ergebnisse an
                    resultsSection.style.display = 'block';
                    resultsSection.scrollIntoView({ behavior: 'smooth' });
                } else {
                    alert('Fehler beim Speichern der Antworten: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Fehler:', error);
                alert('Ein Fehler ist aufgetreten. Bitte versuche es später erneut.');
            });
        });
    }

    // Initial Update
    updateProgress();
});
