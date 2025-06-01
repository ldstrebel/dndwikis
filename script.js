document.addEventListener('DOMContentLoaded', () => {
    // Always hide the global loading overlay on page load
    const globalLoadingOverlay = document.getElementById('globalLoadingOverlay');
    if (globalLoadingOverlay) {
        globalLoadingOverlay.classList.add('visually-hidden');
    }
    
    const campaignCards = document.querySelectorAll('.campaign-card');
    const modal = document.getElementById('campaignModal');
    const modalCloseBtn = modal.querySelector('.modal-close-btn');

    const modalImage = modal.querySelector('#modalImage');
    const modalTitle = modal.querySelector('#modalTitle');
    const modalSynopsis = modal.querySelector('#modalSynopsis');
    const modalChapterList = modal.querySelector('#modalChapterList');
    const modalGenreTagsContainer = modal.querySelector('.modal-genre-tags');
    const modalLoadingSpinner = document.getElementById('modalLoadingSpinner');
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
                    // Show global loading overlay on chapter click
                    link.addEventListener('click', function(e) {
                        e.preventDefault();
                        if (globalLoadingOverlay) {
                            globalLoadingOverlay.classList.remove('visually-hidden');
                            // Force a reflow so the overlay is rendered before navigation
                            globalLoadingOverlay.offsetHeight;
                            // Delay navigation to allow the overlay to render
                            setTimeout(() => {
                                window.location.href = chapter.url;
                            }, 150);
                        } else {
                            window.location.href = chapter.url;
                        }
                    });
                    listItem.appendChild(link);
                    modalChapterList.appendChild(listItem);
                });
                modal.querySelector('.modal-chapters-section').style.display = 'block';
            } else {
                modal.querySelector('.modal-chapters-section').style.display = 'none';
                if (modalLoadingSpinner) modalLoadingSpinner.classList.add('visually-hidden');
            }

            // 3. Display the modal
            modal.style.display = 'flex';
            setTimeout(() => modal.classList.add('active'), 10);
            modal.setAttribute('aria-hidden', 'false');
            document.body.style.overflow = 'hidden';
            // Move focus to close button for accessibility
            modalCloseBtn.focus();
            // Hide spinner if it was left visible
            if (modalLoadingSpinner) modalLoadingSpinner.classList.add('visually-hidden');
            modalChapterList.style.opacity = '1';
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
            // Hide spinner and restore opacity
            if (modalLoadingSpinner) modalLoadingSpinner.classList.add('visually-hidden');
            modalChapterList.style.opacity = '1';
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

    // --- DICE ROLLER ---
    const rollDiceBtn = document.getElementById('rollDiceBtn');
    const diceResult = document.getElementById('diceResult');
    if (rollDiceBtn && diceResult) {
        diceResult.textContent = '🎲';

        rollDiceBtn.addEventListener('click', () => {
            let frame = 0;
            let maxFrames = 24 + Math.floor(Math.random() * 8);
            let lastNum = 1;
            diceResult.classList.add('dice-rolling');
            function animateRoll() {
                if (frame < maxFrames) {
                    let num = Math.floor(Math.random() * 20) + 1;
                    lastNum = num;
                    diceResult.textContent = num;
                    frame++;
                    let delay = frame < maxFrames - 10 ? 40 : 80 + frame * 2;
                    setTimeout(animateRoll, delay);
                } else {
                    let roll = Math.floor(Math.random() * 20) + 1;
                    diceResult.textContent = roll;
                    diceResult.classList.remove('dice-rolling');
                }
            }
            animateRoll();
        });
    }
});