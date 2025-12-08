const k5Controller = {
    lessonPositions: {
        1: { left: '50%', bottom: '3%' },
        2: { left: '42%', bottom: '33%' },
        3: { left: '53%', bottom: '63%' }
    },

    init() {
        this.updateCaterpillarPosition();
    },

    updateCaterpillarPosition() {
        const caterpillar = document.getElementById('caterpillar-indicator');
        if (!caterpillar) return;

        const lesson = app.state.currentLesson || 1;
        const position = this.lessonPositions[lesson];
        
        if (position) {
            caterpillar.style.left = position.left;
            if (position.bottom !== undefined) {
                caterpillar.style.bottom = position.bottom;
                caterpillar.style.top = 'auto';
            } else if (position.top !== undefined) {
                caterpillar.style.top = position.top;
                caterpillar.style.bottom = 'auto';
            }
            caterpillar.setAttribute('data-current-lesson', lesson);
        }
    },

    setCurrentLesson(lessonNumber) {
        if (lessonNumber >= 1 && lessonNumber <= 3) {
            app.state.currentLesson = lessonNumber;
            this.updateCaterpillarPosition();
        }
    },

    onViewEnter() {
        setTimeout(() => {
            this.init();
        }, 100);
    }
};

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('view-k5') && document.getElementById('view-k5').classList.contains('active')) {
        k5Controller.init();
    }
});

