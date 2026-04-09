// Demo Modal
const demoBtn = document.getElementById('demo-btn');
const demoModal = document.getElementById('demo-modal');
const modalOverlay = document.querySelector('.modal-overlay');
const modalClose = document.querySelector('.modal-close');
const demoVideo = document.getElementById('demo-video');

const YOUTUBE_URL = 'https://www.youtube.com/embed/dQw4w9WgXcQ';

// Open modal
if (demoBtn) {
    demoBtn.addEventListener('click', function() {
        demoModal.classList.add('active');
        demoVideo.src = YOUTUBE_URL;
    });
}

// Close modal
function closeModal() {
    demoModal.classList.remove('active');
    demoVideo.src = '';
}

// Close button
if (modalClose) {
    modalClose.addEventListener('click', closeModal);
}

// Close when clicking overlay
if (modalOverlay) {
    modalOverlay.addEventListener('click', closeModal);
}

// Close on Escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && demoModal.classList.contains('active')) {
        closeModal();
    }
});
