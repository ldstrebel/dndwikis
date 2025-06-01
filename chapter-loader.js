window.addEventListener('DOMContentLoaded', () => {
    const overlay = document.getElementById('globalLoadingOverlay');
    if (overlay) {
        overlay.classList.remove('visually-hidden');
    }
    // Hide the overlay after everything is loaded/rendered
    window.addEventListener('load', () => {
        if (overlay) overlay.classList.add('visually-hidden');
    });
});