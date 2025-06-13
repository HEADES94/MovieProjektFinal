document.addEventListener('DOMContentLoaded', function() {
    const questionContainer = document.getElementById('questionContainer');
    const quizResults = document.getElementById('quizResults');
    const progressBar = document.querySelector('.progress');
    const questionCounter = document.querySelector('.question-counter');
    const currentScore = document.querySelector('.current-score');
    const finalScore = document.querySelector('.final-score');
    const correctAnswers = document.querySelector('.correct-answers');
    const accuracyDisplay = document.querySelector('.accuracy');
    const startButton = document.getElementById('startQuiz');
    const difficultySelect = document.getElementById('difficulty');
    const questionSection = document.querySelector('.question-section');

    let currentQuestionIndex = 0;
    let score = 0;
    let correctCount = 0;
    let pointsPerQuestion = 10; // Standardwert für leicht
    const totalQuestions = document.querySelectorAll('.question').length;
    const answers = {};
    let userAnswers = [];
    let questions = [];

    // Sammle alle Fragen
    document.querySelectorAll('.question').forEach(questionElement => {
        const questionText = questionElement.querySelector('.question-text').textContent;
        const correctButton = questionElement.querySelector('.answer-btn[data-correct="true"]');
        const correctAnswer = correctButton ? correctButton.textContent.trim() : '';

        questions.push({
            text: questionText,
            correctAnswer: correctAnswer
        });
    });

    // Start-Button Event-Handler
    startButton.addEventListener('click', function() {
        const difficulty = difficultySelect.value;
        switch(difficulty) {
            case 'easy':
                pointsPerQuestion = 10;
                break;
            case 'medium':
                pointsPerQuestion = 50;
                break;
            case 'hard':
                pointsPerQuestion = 100;
                break;
        }
        startButton.style.display = 'none';
        difficultySelect.disabled = true;
        questionSection.style.display = 'block';
        showQuestion(0);
    });

    // Event-Handler für alle Antwort-Buttons
    document.querySelectorAll('.answer-btn').forEach(button => {
        button.addEventListener('click', handleAnswer);
    });

    function handleAnswer(event) {
        const button = event.target;
        const currentQuestionDiv = document.querySelector(`.question[data-question-id="${currentQuestionIndex}"]`);
        const buttons = currentQuestionDiv.querySelectorAll('.answer-btn');
        const correctAnswer = Array.from(buttons).find(btn => btn.getAttribute('data-correct') === 'true');
        const questionText = currentQuestionDiv.querySelector('.question-text').textContent;

        // Buttons deaktivieren
        buttons.forEach(btn => btn.disabled = true);

        // Antwort speichern
        const selectedAnswer = button.textContent.trim();
        const isCorrect = button.getAttribute('data-correct') === 'true';

        userAnswers.push({
            questionText: questionText,
            selectedAnswer: selectedAnswer,
            correctAnswer: correctAnswer.textContent.trim(),
            isCorrect: isCorrect
        });

        if (isCorrect) {
            button.classList.add('correct');
            score += pointsPerQuestion;
            correctCount++;
            currentScore.textContent = score + ' Punkte';
        } else {
            button.classList.add('wrong');
            correctAnswer.classList.add('correct');
        }

        // Zur nächsten Frage oder zu den Ergebnissen
        if (currentQuestionIndex < totalQuestions - 1) {
            setTimeout(() => {
                currentQuestionIndex++;
                showQuestion(currentQuestionIndex);
                updateProgress();
            }, 1000);
        } else {
            setTimeout(submitQuiz, 1000);
        }
    }

    function showQuestion(index) {
        // Aktuelle Frage ausblenden
        document.querySelectorAll('.question').forEach(q => q.style.display = 'none');

        // Neue Frage einblenden
        const nextQuestion = document.querySelector(`.question[data-question-id="${index}"]`);
        if (nextQuestion) {
            nextQuestion.style.display = 'block';
            // Buttons der neuen Frage aktivieren
            nextQuestion.querySelectorAll('.answer-btn').forEach(btn => btn.disabled = false);
        }

        // Fortschritt aktualisieren
        questionCounter.textContent = `Frage ${index + 1}/${totalQuestions}`;
    }

    function updateProgress() {
        const progress = ((currentQuestionIndex + 1) / totalQuestions) * 100;
        progressBar.style.width = `${progress}%`;
    }

    function submitQuiz() {
        const movieId = window.location.pathname.split('/')[2];

        fetch(`/movies/${movieId}/quiz/submit`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                answers: userAnswers,
                score: score,
                correctCount: correctCount,
                totalQuestions: totalQuestions
            })
        })
        .then(response => response.json())
        .then(data => {
            showResults({
                score: score,
                correct_count: correctCount,
                total_questions: totalQuestions,
                earned_achievements: data.earned_achievements
            });
        })
        .catch(error => {
            console.error('Error:', error);
        });
    }

    function showResults(data) {
        // Quiz-Bereich ausblenden
        document.querySelector('.question-section').style.display = 'none';

        // Ergebnisse anzeigen
        finalScore.textContent = data.score;
        correctAnswers.textContent = `${data.correct_count}/${totalQuestions}`;
        accuracyDisplay.textContent = `${Math.round((data.correct_count / totalQuestions) * 100)}%`;

        // Detaillierte Analyse erstellen
        const analysisContainer = document.createElement('div');
        analysisContainer.className = 'question-analysis glass-card';
        analysisContainer.innerHTML = `
            <h3>Detaillierte Analyse</h3>
            <div class="analysis-list">
                ${userAnswers.map((answer, index) => `
                    <div class="analysis-item ${answer.isCorrect ? 'correct-answer' : 'wrong-answer'}">
                        <div class="question-info">
                            <span class="question-number">Frage ${index + 1}</span>
                            <p class="question-text">${answer.questionText}</p>
                        </div>
                        <div class="answer-info">
                            <p>Deine Antwort: ${answer.selectedAnswer}</p>
                            ${!answer.isCorrect ? `<p>Richtige Antwort: ${answer.correctAnswer}</p>` : ''}
                        </div>
                    </div>
                `).join('')}
            </div>
        `;

        // Füge die Analyse vor den Action-Buttons ein
        const actionButtons = document.querySelector('.action-buttons');
        actionButtons.parentNode.insertBefore(analysisContainer, actionButtons);

        // Achievements anzeigen, falls vorhanden
        if (data.earned_achievements && data.earned_achievements.length > 0) {
            const achievementsGrid = document.querySelector('.achievements-grid');
            achievementsGrid.innerHTML = data.earned_achievements.map(achievement => `
                <div class="achievement-item glass-card-inner">
                    <img src="${achievement.icon_url}" alt="${achievement.title}">
                    <div class="achievement-info">
                        <h4>${achievement.title}</h4>
                        <p>${achievement.description}</p>
                    </div>
                </div>
            `).join('');
            document.querySelector('.achievements-earned').style.display = 'block';
        }

        quizResults.style.display = 'block';
    }

    // Initial Setup
    updateProgress();
});
