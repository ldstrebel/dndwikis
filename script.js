document.addEventListener('DOMContentLoaded', () => {
    const campaignCards = document.querySelectorAll('.campaign-card');
    const modal = document.getElementById('campaignModal');
    const modalCloseBtn = modal.querySelector('.modal-close-btn');

    const modalImage = modal.querySelector('#modalImage');
    const modalTitle = modal.querySelector('#modalTitle');
    const modalSynopsis = modal.querySelector('#modalSynopsis');
    const modalChapterList = modal.querySelector('#modalChapterList');
    const modalGenreTagsContainer = modal.querySelector('.modal-genre-tags');

    // Accessibility: Make cards focusable and act as buttons
    campaignCards.forEach(card => {
        card.setAttribute('tabindex', '0');
        card.setAttribute('role', 'button');
    });

    let lastFocusedElement = null;

    campaignCards.forEach(card => {
        card.addEventListener('click', () => {
            lastFocusedElement = document.activeElement;
            // 1. Get data from the clicked card
            const title = card.dataset.campaignTitle;
            const posterImage = card.dataset.posterImage;
            const fullSynopsis = card.dataset.fullSynopsis;
            const chapters = JSON.parse(card.dataset.chapters || '[]');
            const genres = card.dataset.genre.split(' ');

            // 2. Populate the modal
            modalImage.src = posterImage;
            modalImage.alt = `Artwork for ${title}`;
            modalTitle.textContent = title;
            modalSynopsis.textContent = fullSynopsis;

            // Populate genre tags
            modalGenreTagsContainer.innerHTML = '';
            genres.forEach(genreText => {
                if (genreText) {
                    const genreTagElement = document.createElement('span');
                    genreTagElement.classList.add('genre-tag');
                    genreTagElement.textContent = genreText.charAt(0).toUpperCase() + genreText.slice(1);
                    modalGenreTagsContainer.appendChild(genreTagElement);
                }
            });

            modalChapterList.innerHTML = '';
            if (chapters.length > 0) {
                chapters.forEach(chapter => {
                    const listItem = document.createElement('li');
                    const link = document.createElement('a');
                    link.href = chapter.url;
                    link.textContent = chapter.title;
                    listItem.appendChild(link);
                    modalChapterList.appendChild(listItem);
                });
                modal.querySelector('.modal-chapters-section').style.display = 'block';
            } else {
                modal.querySelector('.modal-chapters-section').style.display = 'none';
            }

            // 3. Display the modal
            modal.style.display = 'flex';
            setTimeout(() => modal.classList.add('active'), 10);
            modal.setAttribute('aria-hidden', 'false');
            document.body.style.overflow = 'hidden';
            // Move focus to close button for accessibility
            modalCloseBtn.focus();
        });

        // Keyboard accessibility: open modal with Enter or Space
        card.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                card.click();
            }
        });
    });

    // Close modal functionality
    function closeModal() {
        modal.classList.remove('active');
        setTimeout(() => {
            modal.style.display = 'none';
            modal.setAttribute('aria-hidden', 'true');
            document.body.style.overflow = '';
            if (lastFocusedElement) lastFocusedElement.focus();
        }, 300);
    }

    modalCloseBtn.addEventListener('click', closeModal);

    // Close modal if clicking on the overlay
    modal.addEventListener('click', (event) => {
        if (event.target === modal) {
            closeModal();
        }
    });

    // Close modal with Escape key
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && modal.classList.contains('active')) {
            closeModal();
        }
    });

    // Trap focus inside modal when open
    modal.addEventListener('keydown', (e) => {
        if (e.key === 'Tab' && modal.classList.contains('active')) {
            const focusable = modal.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
            if (focusable.length === 0) return;
            const first = focusable[0];
            const last = focusable[focusable.length - 1];
            if (e.shiftKey) {
                if (document.activeElement === first) {
                    e.preventDefault();
                    last.focus();
                }
            } else {
                if (document.activeElement === last) {
                    e.preventDefault();
                    first.focus();
                }
            }
        }
    });

    // --- FILTER LOGIC ---
    const genreFilter = document.getElementById('genre-filter');
    if (genreFilter) {
        genreFilter.addEventListener('change', function() {
            const selectedGenre = this.value;
            document.querySelectorAll('.campaign-card').forEach(card => {
                const cardGenres = card.dataset.genre || "";
                if (selectedGenre === 'all' || cardGenres.includes(selectedGenre)) {
                    card.style.display = 'flex';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    }
});