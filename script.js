document.addEventListener('DOMContentLoaded', () => {
    // --- MODIFICATION START: Skip initial global loading screen hiding ---
    // // This refers to the globalLoadingOverlay *within index.html itself*.
    // // If index.html has its own initial loading screen, this hides it.
    // // The HTML provided for index.html has this div initially hidden, so this is a safeguard.
    // const globalLoadingOverlay = document.getElementById('globalLoadingOverlay');
    // if (globalLoadingOverlay) {
    //     globalLoadingOverlay.classList.add('visually-hidden');
    // }
    // --- MODIFICATION END ---

    // Mobile Menu Toggle for main-nav
    const menuToggle = document.getElementById('menu-toggle');
    const mainNav = document.getElementById('main-nav');
    if (menuToggle && mainNav) {
        menuToggle.addEventListener('click', () => {
            const isExpanded = menuToggle.getAttribute('aria-expanded') === 'true' || false;
            menuToggle.setAttribute('aria-expanded', String(!isExpanded));
            mainNav.classList.toggle('nav-open'); // Controls nav visibility via CSS
            menuToggle.classList.toggle('menu-open'); // Animates the burger icon
            mainNav.setAttribute('aria-hidden', String(isExpanded)); // Update aria-hidden for nav
        });
    }

    const campaignCards = document.querySelectorAll('.campaign-card');
    const modal = document.getElementById('campaignModal');

    // Ensure modal exists before trying to query its children
    if (!modal) {
        console.error("Campaign modal (#campaignModal) not found in the DOM.");
        return; // Stop further execution if modal isn't present
    }

    const modalCloseBtn = modal.querySelector('.modal-close-btn');
    const modalImage = modal.querySelector('#modalImage');
    const modalTitle = modal.querySelector('#modalTitle');
    const modalSynopsis = modal.querySelector('#modalSynopsis');
    const modalChapterList = modal.querySelector('#modalChapterList');
    const modalGenreTagsContainer = modal.querySelector('.modal-genre-tags');
    const modalLoadingSpinner = document.getElementById('modalLoadingSpinner'); // D20 spinner in modal

    // Accessibility for campaign cards
    campaignCards.forEach(card => {
        card.setAttribute('tabindex', '0');
        card.setAttribute('role', 'button');
        const cardTitleText = card.dataset.campaignTitle || 'campaign details';
        card.setAttribute('aria-label', `View details for ${cardTitleText}`);
    });

    let lastFocusedElement = null; // To return focus when modal closes

    campaignCards.forEach(card => {
        card.addEventListener('click', () => {
            lastFocusedElement = document.activeElement;

            // Get data from the clicked card
            const title = card.dataset.campaignTitle;
            const posterImage = card.dataset.posterImage;
            const fullSynopsis = card.dataset.fullSynopsis;
            const chapters = JSON.parse(card.dataset.chapters || '[]');
            const genres = (card.dataset.genre || "").split(' ');

            // Populate the modal
            if (modalImage) {
                modalImage.src = posterImage;
                modalImage.alt = `Artwork for ${title}`;
            }
            if (modalTitle) modalTitle.textContent = title;
            if (modalSynopsis) modalSynopsis.textContent = fullSynopsis;

            // Populate genre tags
            if (modalGenreTagsContainer) {
                modalGenreTagsContainer.innerHTML = '';
                genres.forEach(genreText => {
                    if (genreText) {
                        const genreTagElement = document.createElement('span');
                        genreTagElement.classList.add('genre-tag');
                        genreTagElement.textContent = genreText.charAt(0).toUpperCase() + genreText.slice(1);
                        modalGenreTagsContainer.appendChild(genreTagElement);
                    }
                });
            }

            // Populate chapter list
            if (modalChapterList) {
                modalChapterList.innerHTML = ''; // Clear previous chapters
                const chaptersSection = modal.querySelector('.modal-chapters-section');

                if (chapters.length > 0) {
                    chapters.forEach(chapter => {
                        const listItem = document.createElement('li');
                        const link = document.createElement('a');
                        link.href = chapter.url;
                        link.textContent = chapter.title;

                        // Event listener for chapter link click (THIS IS THE LOADING YOU WANT FOR CHAPTERS)
                        link.addEventListener('click', function(e) {
                            e.preventDefault(); // Prevent default navigation to handle UX first

                            // Show modal's own D20 spinner for immediate feedback
                            if (modalLoadingSpinner) {
                                modalLoadingSpinner.classList.remove('visually-hidden');
                            }
                            if (modalChapterList) {
                                modalChapterList.style.opacity = '0.3'; // Dim the chapter list
                            }

                            // Navigate after a brief moment to allow spinner to render
                            setTimeout(() => {
                                window.location.href = this.href;
                            }, 70); // Short delay (adjust as needed)
                        });

                        listItem.appendChild(link);
                        modalChapterList.appendChild(listItem);
                    });
                    if (chaptersSection) chaptersSection.style.display = 'block';
                } else {
                    if (chaptersSection) chaptersSection.style.display = 'none';
                }
            }

            // Ensure modal D20 spinner is hidden and list is opaque when modal first opens
            if (modalLoadingSpinner) modalLoadingSpinner.classList.add('visually-hidden');
            if (modalChapterList) modalChapterList.style.opacity = '1';

            // Display the modal using aria-hidden to trigger CSS transitions
            modal.setAttribute('aria-hidden', 'false');
            document.body.style.overflow = 'hidden'; // Prevent background scrolling
            if (modalCloseBtn) modalCloseBtn.focus(); // Set focus to close button
        });

        // Keyboard accessibility for opening modal with Enter or Space
        card.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                card.click();
            }
        });
    });

    // Function to close the modal
    function closeModal() {
        modal.setAttribute('aria-hidden', 'true');
        document.body.style.overflow = ''; // Restore background scrolling
        if (lastFocusedElement) {
            lastFocusedElement.focus(); // Return focus to the element that opened the modal
        }
        // Reset modal spinner and chapter list appearance
        if (modalLoadingSpinner) modalLoadingSpinner.classList.add('visually-hidden');
        if (modalChapterList) modalChapterList.style.opacity = '1';
    }

    if (modalCloseBtn) modalCloseBtn.addEventListener('click', closeModal);

    // Close modal if clicking on the overlay backdrop
    modal.addEventListener('click', (event) => {
        if (event.target === modal) {
            closeModal();
        }
    });

    // Close modal with Escape key
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && modal.getAttribute('aria-hidden') === 'false') {
            closeModal();
        }
    });

    // Trap focus inside the modal when open
    modal.addEventListener('keydown', (e) => {
        if (e.key === 'Tab' && modal.getAttribute('aria-hidden') === 'false') {
            const focusableElements = modal.querySelectorAll(
                'button, [href], input:not([type="hidden"]), select, textarea, [tabindex]:not([tabindex="-1"])'
            );
            const visibleFocusableElements = Array.from(focusableElements).filter(
                el => el.offsetParent !== null && !el.disabled && el.getAttribute('aria-hidden') !== 'true'
            );

            if (visibleFocusableElements.length === 0) return;

            const firstFocusableElement = visibleFocusableElements[0];
            const lastFocusableElement = visibleFocusableElements[visibleFocusableElements.length - 1];

            if (e.shiftKey) { // Shift + Tab
                if (document.activeElement === firstFocusableElement) {
                    e.preventDefault();
                    lastFocusableElement.focus();
                }
            } else { // Tab
                if (document.activeElement === lastFocusableElement) {
                    e.preventDefault();
                    firstFocusableElement.focus();
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
                if (selectedGenre === 'all' || cardGenres.toLowerCase().includes(selectedGenre.toLowerCase())) {
                    card.style.display = 'flex'; // Or 'block', depending on your card styling
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
        diceResult.textContent = '🎲'; // Initial dice symbol

        rollDiceBtn.addEventListener('click', () => {
            let frame = 0;
            const maxFrames = 15 + Math.floor(Math.random() * 10); // Duration of spin
            diceResult.classList.add('dice-rolling');

            function animateRoll() {
                if (frame < maxFrames) {
                    diceResult.textContent = String(Math.floor(Math.random() * 20) + 1);
                    frame++;
                    // Animation speed: faster at start, slower at end
                    let delay = 25 + frame * (50 / maxFrames);
                    setTimeout(animateRoll, delay);
                } else {
                    diceResult.textContent = String(Math.floor(Math.random() * 20) + 1); // Final result
                    diceResult.classList.remove('dice-rolling');
                }
            }
            animateRoll();
        });
    }
});