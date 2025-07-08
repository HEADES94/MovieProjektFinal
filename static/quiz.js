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
                        <div class="achievement-banner" style="background: linear-gradient(135deg, #10b981, #059669); border-radius: 12px; padding: 1.5rem; margin-bottom: 2rem; color: white; animation: slideInUp 0.6s ease-out;">
                            <h2 style="color: white; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem;">
                                🎉 Achievement freigeschaltet!
                            </h2>
                            ${data.achievements.map(a => `
                                <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 8px; margin-bottom: 0.5rem;">
                                    <div style="font-size: 1.2rem; font-weight: bold; color: #ffd700;">${a.title}</div>
                                    <div style="color: rgba(255,255,255,0.9); margin-top: 0.5rem;">${a.description}</div>
                                </div>
                            `).join('')}
                        </div>`;
                    }

                    // Erstelle die Zusammenfassung der Fragen
                    const questionsHtml = data.question_results.map((q, index) => `
                        <div class="question-result ${q.is_correct ? 'correct' : 'incorrect'}" style="
                            background: ${q.is_correct ? '#dcfce7' : '#fee2e2'};
                            border-left: 4px solid ${q.is_correct ? '#10b981' : '#ef4444'};
                            padding: 1rem;
                            margin-bottom: 1rem;
                            border-radius: 8px;
                        ">
                            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                                <span style="font-size: 1.5rem;">${q.is_correct ? '✅' : '❌'}</span>
                                <h4 style="margin: 0; color: #374151;">Frage ${index + 1}</h4>
                            </div>
                            <p style="margin-bottom: 1rem; font-weight: 500; color: #374151;">${q.question_text}</p>
                            <div style="background: white; padding: 0.75rem; border-radius: 6px; margin-bottom: 0.5rem;">
                                <strong>Deine Antwort:</strong>
                                <span style="color: ${q.is_correct ? '#10b981' : '#ef4444'}; font-weight: bold;">
                                    ${q.user_answer}
                                </span>
                            </div>
                            ${!q.is_correct ? `
                                <div style="background: #f0fdf4; padding: 0.75rem; border-radius: 6px; border: 1px solid #10b981;">
                                    <strong>Richtige Antwort:</strong>
                                    <span style="color: #10b981; font-weight: bold;">${q.correct_answer}</span>
                                </div>
                            ` : ''}
                        </div>
                    `).join('');

                    // Erstelle die Ergebnisanzeige
                    resultsSection.innerHTML = `
                        <div class="quiz-results" style="animation: fadeInUp 0.8s ease-out;">
                            <div style="text-align: center; margin-bottom: 2rem;">
                                <h2 style="color: #10b981; margin-bottom: 1rem; font-size: 2.5rem;">
                                    🎉 Quiz abgeschlossen!
                                </h2>
                                <div class="score-display" style="
                                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                    color: white;
                                    padding: 2rem;
                                    border-radius: 20px;
                                    display: inline-block;
                                    margin-bottom: 1rem;
                                    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                                ">
                                    <div style="font-size: 3rem; font-weight: bold; margin-bottom: 0.5rem;">
                                        ${data.score}
                                    </div>
                                    <div style="font-size: 1.2rem; opacity: 0.9;">Punkte</div>
                                </div>
                            </div>

                            <div class="quiz-stats" style="
                                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                                color: white;
                                padding: 1.5rem;
                                border-radius: 12px;
                                margin-bottom: 2rem;
                                text-align: center;
                            ">
                                <div style="font-size: 1.5rem; margin-bottom: 1rem;">
                                    <strong>${data.correct_count}</strong> von <strong>${data.total_questions}</strong> richtig
                                </div>
                                <div style="background: rgba(255,255,255,0.2); border-radius: 10px; height: 20px; overflow: hidden;">
                                    <div style="
                                        background: rgba(255,255,255,0.8);
                                        height: 100%;
                                        width: ${(data.correct_count / data.total_questions) * 100}%;
                                        transition: width 1s ease-out;
                                        border-radius: 10px;
                                    "></div>
                                </div>
                                <div style="margin-top: 0.5rem; font-size: 1.1rem;">
                                    ${Math.round((data.correct_count / data.total_questions) * 100)}% richtig
                                </div>
                            </div>

                            ${achievementsBanner}

                            <div class="questions-summary" style="margin-bottom: 2rem;">
                                <h3 style="color: #374151; margin-bottom: 1rem; font-size: 1.8rem; text-align: center;">
                                    📋 Detaillierte Zusammenfassung
                                </h3>
                                ${questionsHtml}
                            </div>

                            <div class="quiz-actions" style="
                                display: flex;
                                gap: 1rem;
                                justify-content: center;
                                flex-wrap: wrap;
                                margin-top: 2rem;
                            ">
                                <a href="/quiz" class="btn btn-primary" style="
                                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                    color: white;
                                    padding: 0.75rem 1.5rem;
                                    border-radius: 8px;
                                    text-decoration: none;
                                    font-weight: bold;
                                    transition: transform 0.2s;
                                " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                                    🏠 Zurück zur Quiz-Übersicht
                                </a>
                                <a href="/quiz/${movieId}?difficulty=${difficulty}" class="btn btn-secondary" style="
                                    background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
                                    color: #8b4513;
                                    padding: 0.75rem 1.5rem;
                                    border-radius: 8px;
                                    text-decoration: none;
                                    font-weight: bold;
                                    transition: transform 0.2s;
                                " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                                    🔄 Erneut versuchen
                                </a>
                            </div>
                        </div>
                    `;

                    // Zeige die Ergebnisse an
                    resultsSection.style.display = 'block';
                    resultsSection.scrollIntoView({ behavior: 'smooth' });
                } else {
                    alert('Fehler beim Übermitteln des Quiz: ' + (data.error || 'Unbekannter Fehler'));
                }
            })
            .catch(error => {
                console.error('Quiz submission error:', error);
                alert('Ein Fehler ist aufgetreten. Bitte versuche es erneut.');
            });
        });
    }

    // Initial Update
    updateProgress();
});
