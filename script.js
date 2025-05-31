document.addEventListener('DOMContentLoaded', () => {
    const campaignCards = document.querySelectorAll('.campaign-card');
    const modal = document.getElementById('campaignModal');
    const modalCloseBtn = modal.querySelector('.modal-close-btn');

    const modalImage = modal.querySelector('#modalImage');
    const modalTitle = modal.querySelector('#modalTitle');
    const modalSynopsis = modal.querySelector('#modalSynopsis');
    const modalChapterList = modal.querySelector('#modalChapterList');
    const modalGenreTagsContainer = modal.querySelector('.modal-genre-tags');
    // const modalFullCampaignLink = modal.querySelector('#modalFullCampaignLink'); // If using this

    campaignCards.forEach(card => {
        card.addEventListener('click', () => {
            // 1. Get data from the clicked card
            const title = card.dataset.campaignTitle;
            const posterImage = card.dataset.posterImage; // Make sure card has this
            const fullSynopsis = card.dataset.fullSynopsis;
            const chapters = JSON.parse(card.dataset.chapters || '[]'); // Ensure valid JSON
            const genres = card.dataset.genre.split(' '); // Assuming space-separated genres in data-genre

            // 2. Populate the modal
            modalImage.src = posterImage;
            modalImage.alt = `Artwork for ${title}`;
            modalTitle.textContent = title;
            modalSynopsis.textContent = fullSynopsis;

            // Populate genre tags
            modalGenreTagsContainer.innerHTML = ''; // Clear previous tags
            genres.forEach(genreText => {
                if (genreText) { // Ensure not empty string
                    const genreTagElement = document.createElement('span');
                    genreTagElement.classList.add('genre-tag');
                    genreTagElement.textContent = genreText.charAt(0).toUpperCase() + genreText.slice(1); // Capitalize
                    modalGenreTagsContainer.appendChild(genreTagElement);
                }
            });

            modalChapterList.innerHTML = ''; // Clear previous chapters
            if (chapters.length > 0) {
                chapters.forEach(chapter => {
                    const listItem = document.createElement('li');
                    const link = document.createElement('a');
                    link.href = chapter.url;
                    link.textContent = chapter.title;
                    // If your graphic novels open in the same window:
                    // link.target = "_self";
                    // If they open in a new tab (often good for external-feeling links):
                    // link.target = "_blank";
                    listItem.appendChild(link);
                    modalChapterList.appendChild(listItem);
                });
                modal.querySelector('.modal-chapters-section').style.display = 'block';
            } else {
                 modal.querySelector('.modal-chapters-section').style.display = 'none';
            }

            // if (card.dataset.fullCampaignUrl) {
            //    modalFullCampaignLink.href = card.dataset.fullCampaignUrl;
            //    modalFullCampaignLink.style.display = 'inline-block';
            // } else {
            //    modalFullCampaignLink.style.display = 'none';
            // }


            // 3. Display the modal
            modal.style.display = 'flex'; // Or 'block' if you changed it
            setTimeout(() => modal.classList.add('active'), 10); // For transition
            modal.setAttribute('aria-hidden', 'false');
            document.body.style.overflow = 'hidden'; // Prevent background scroll
        });
    });

    // Close modal functionality
    function closeModal() {
        modal.classList.remove('active');
        setTimeout(() => {
            modal.style.display = 'none';
            modal.setAttribute('aria-hidden', 'true');
            document.body.style.overflow = ''; // Restore background scroll
        }, 300); // Match transition duration
    }

    modalCloseBtn.addEventListener('click', closeModal);

    // Optional: Close modal if clicking on the overlay
    modal.addEventListener('click', (event) => {
        if (event.target === modal) {
            closeModal();
        }
    });

    // Optional: Close modal with Escape key
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && modal.classList.contains('active')) {
            closeModal();
        }
    });

    // --- FILTER LOGIC from previous step (can be integrated here) ---
    const genreFilter = document.getElementById('genre-filter');
    if (genreFilter) {
        genreFilter.addEventListener('change', function() {
            const selectedGenre = this.value;
            document.querySelectorAll('.campaign-card').forEach(card => {
                const cardGenres = card.dataset.genre || ""; // Get genres as a string
                if (selectedGenre === 'all' || cardGenres.includes(selectedGenre)) {
                    card.style.display = 'flex'; // Or 'block' or whatever its default display is
                } else {
                    card.style.display = 'none';
                }
            });
        });
    }
});
