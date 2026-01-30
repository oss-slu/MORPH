const app = {
    state: {
        currentView: 'landing',
        currentLesson: 1
    },

    init() {
        this.renderView();
    },

    startPath(path) {
        this.state.currentView = path;
        this.renderView();
        
        if (path === 'k5' && typeof k5Controller !== 'undefined') {
            k5Controller.onViewEnter();
        }
    },

    setCurrentLesson(lessonNumber) {
        this.state.currentLesson = lessonNumber;
        if (this.state.currentView === 'k5' && typeof k5Controller !== 'undefined') {
            k5Controller.setCurrentLesson(lessonNumber);
        }
    },

    renderView() {
        document.querySelectorAll('.view-section').forEach(el => {
            el.classList.remove('active');
        });
        
        const viewId = `view-${this.state.currentView}`;
        const viewElement = document.getElementById(viewId);
        if (viewElement) {
            viewElement.classList.add('active');
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    app.init();
});
