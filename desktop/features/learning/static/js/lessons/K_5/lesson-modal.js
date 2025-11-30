const lessonModal = {
    isOpen: false,

    init() {
        this.checkPersistentModal();
        this.setupEventListeners();
    },

    setupEventListeners() {
        const overlay = document.querySelector('.lesson-modal-overlay');
        if (overlay) {
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) {
                    this.close();
                }
            });
        }

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen) {
                this.close();
            }
        });
    },

    checkPersistentModal() {
        const wasOpen = sessionStorage.getItem('lessonModalOpen');
        const lessonNumber = sessionStorage.getItem('lessonModalNumber');
        
        if (wasOpen === 'true' && lessonNumber) {
            setTimeout(() => {
                this.open(parseInt(lessonNumber), false);
            }, 100);
        }
    },

    open(lessonNumber, saveToStorage = true) {
        if (!lessonsData || !lessonsData[lessonNumber]) {
            console.error('Lesson not found:', lessonNumber);
            return;
        }

        const modal = document.getElementById('lesson-modal');
        const modalBody = document.getElementById('lesson-modal-body');
        
        if (!modal || !modalBody) {
            setTimeout(() => this.open(lessonNumber, saveToStorage), 100);
            return;
        }

        const lesson = lessonsData[lessonNumber];
        modalBody.innerHTML = lesson.content;
        
        modal.classList.remove('hidden');
        this.isOpen = true;

        if (saveToStorage) {
            sessionStorage.setItem('lessonModalOpen', 'true');
            sessionStorage.setItem('lessonModalNumber', lessonNumber.toString());
        }

        document.body.style.overflow = 'hidden';
    },

    close() {
        const modal = document.getElementById('lesson-modal');
        if (!modal) return;

        modal.classList.add('hidden');
        this.isOpen = false;
        
        sessionStorage.removeItem('lessonModalOpen');
        sessionStorage.removeItem('lessonModalNumber');
        
        document.body.style.overflow = '';
    }
};

document.addEventListener('DOMContentLoaded', () => {
    lessonModal.init();
});

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        lessonModal.init();
    });
} else {
    lessonModal.init();
}

