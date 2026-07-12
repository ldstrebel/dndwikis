/**
 * D&D Wikis - The Portals
 * Main JavaScript functionality for campaign showcase and modal system
 * 
 * FEATURES:
 * - Campaign card interactions and modal display
 * - Genre filtering system
 * - Dice roller with animation
 * - Mobile navigation toggle
 * - Accessibility features (ARIA, keyboard navigation, focus management)
 * 
 * ADDING NEW CAMPAIGNS:
 * Campaigns are automatically detected from HTML data attributes on .campaign-card elements.
 * No JavaScript changes needed when adding new campaigns - just follow the HTML structure.
 * 
 * See README.md for detailed campaign addition instructions.
 */

// Constants for localStorage keys
const CAMPAIGN_ORDER_KEY = 'campaignOrder';
const VIEW_TYPE_KEY = 'viewType';

document.addEventListener('DOMContentLoaded', () => {
    // Check if we have any clicked campaigns and apply sorting
    const cards = document.querySelectorAll('.campaign-card');
    let hasClickedCampaigns = false;
    
    cards.forEach(card => {
        const title = card.dataset.campaignTitle;
        if (getLastClickedTime(title) > 0) {
            hasClickedCampaigns = true;
        }
    });

    if (hasClickedCampaigns) {
        sortCampaignCards();
    }

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

    // Campaign Order Management
    function getLastClickedTime(campaignTitle) {
        const campaignId = campaignTitle.toLowerCase().replace(/\s+/g, '-');
        return parseInt(localStorage.getItem(`lastClicked_${campaignId}`)) || 0;
    }

    function sortCampaignCards() {
        const campaignGrid = document.getElementById('campaign-grid');
        if (!campaignGrid) return;
        
        const cards = Array.from(campaignGrid.getElementsByClassName('campaign-card'));
        
        cards.sort((a, b) => {
            const titleA = a.dataset.campaignTitle;
            const titleB = b.dataset.campaignTitle;
            const timeA = getLastClickedTime(titleA);
            const timeB = getLastClickedTime(titleB);
            return timeB - timeA; // Most recent first
        });

        // Reorder DOM elements
        cards.forEach(card => campaignGrid.appendChild(card));
    }

    // View Toggle System
    const bannerViewBtn = document.getElementById('banner-view-btn');
    const iconViewBtn = document.getElementById('icon-view-btn');
    const campaignGrid = document.getElementById('campaign-grid');
    
    function saveViewType(isIconView) {
        localStorage.setItem(VIEW_TYPE_KEY, isIconView ? 'icon' : 'banner');
    }

    function loadSavedViewType() {
        const viewType = localStorage.getItem(VIEW_TYPE_KEY);
        if (viewType === 'icon') {
            campaignGrid.classList.add('icon-view');
            iconViewBtn.classList.add('active');
            iconViewBtn.setAttribute('aria-pressed', 'true');
            bannerViewBtn.classList.remove('active');
            bannerViewBtn.setAttribute('aria-pressed', 'false');
        } else {
            campaignGrid.classList.remove('icon-view');
            bannerViewBtn.classList.add('active');
            bannerViewBtn.setAttribute('aria-pressed', 'true');
            iconViewBtn.classList.remove('active');
            iconViewBtn.setAttribute('aria-pressed', 'false');
        }
    }
    
    if (bannerViewBtn && iconViewBtn && campaignGrid) {
        // Load saved view type on page load
        loadSavedViewType();
        
        bannerViewBtn.addEventListener('click', () => {
            campaignGrid.classList.remove('icon-view');
            saveViewType(false);
            bannerViewBtn.classList.add('active');
            bannerViewBtn.setAttribute('aria-pressed', 'true');
            iconViewBtn.classList.remove('active');
            iconViewBtn.setAttribute('aria-pressed', 'false');
        });
        
        iconViewBtn.addEventListener('click', () => {
            campaignGrid.classList.add('icon-view');
            iconViewBtn.classList.add('active');
            iconViewBtn.setAttribute('aria-pressed', 'true');
            bannerViewBtn.classList.remove('active');
            bannerViewBtn.setAttribute('aria-pressed', 'false');
        });
    }

    // Mobile Menu Campaign Links
    const campaignLinks = document.querySelectorAll('.campaign-link');
    campaignLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const campaignType = link.dataset.campaign;
            let targetCard;
            
            // Find the corresponding campaign card
            switch(campaignType) {
                case 'meryl':
                    targetCard = document.querySelector('[data-campaign-title="The Chronicles of Meryl"]');
                    break;
                case 'dungeon-crawlers':
                    targetCard = document.querySelector('[data-campaign-title="Dungeon Crawlers"]');
                    break;
                case 'verdant-scar':
                    targetCard = document.querySelector('[data-campaign-title="Verdant Scar"]');
                    break;
            }
            
            if (targetCard) {
                // Close mobile menu
                mainNav.classList.remove('nav-open');
                menuToggle.classList.remove('menu-open');
                menuToggle.setAttribute('aria-expanded', 'false');
                mainNav.setAttribute('aria-hidden', 'true');
                
                // Scroll to campaign card
                targetCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
                
                // Highlight the card briefly
                targetCard.style.transform = 'scale(1.05)';
                targetCard.style.boxShadow = '0px 8px 25px rgba(var(--logo-teal-rgb), 0.5)';
                setTimeout(() => {
                    targetCard.style.transform = '';
                    targetCard.style.boxShadow = '';
                }, 1000);
            }
        });
    });

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
    const modalShareBtn = modal.querySelector('#modalShareBtn');
    const modalLoadingSpinner = document.getElementById('modalLoadingSpinner'); // D20 spinner in modal

    if (modalShareBtn) {
        modalShareBtn.addEventListener('click', () => {
            const title = modalTitle ? modalTitle.textContent : "Campaign";
            let shortName = title.split(' ')[0].toLowerCase();
            // Handle "The Chronicles of Meryl" -> "meryl"
            if (shortName === "the") {
                const parts = title.split(' ');
                shortName = parts[parts.length - 1].toLowerCase();
            }
            const shareUrl = `${window.location.origin}${window.location.pathname}?c=${shortName}`;

            const shareData = {
                title: `${title} - Campaign Showcase`,
                text: `Check out the chapters and storyboards for the ${title} campaign!`,
                url: shareUrl
            };

            if (navigator.share) {
                navigator.share(shareData)
                    .catch(err => console.log("Error sharing campaign:", err));
            } else {
                navigator.clipboard.writeText(shareUrl)
                    .then(() => alert("Campaign link copied to clipboard!"))
                    .catch(err => console.error("Could not copy link:", err));
            }
        });
    }

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

            // Update campaign order and sort
            const campaignId = title.toLowerCase().replace(/\s+/g, '-');
            localStorage.setItem(`lastClicked_${campaignId}`, Date.now());
            sortCampaignCards();

            // Show the modal and prevent background scrolling
            modal.setAttribute('aria-hidden', 'false');
            document.body.style.overflow = 'hidden';
            
            // Set focus to the modal close button for accessibility
            if (modalCloseBtn) {
                modalCloseBtn.focus();
            }

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

                            // Update last clicked time for the campaign
                            const campaignId = title.toLowerCase().replace(/\s+/g, '-');
                            localStorage.setItem(`lastClicked_${campaignId}`, Date.now());

                            // Show modal's own D20 spinner for immediate feedback
                            if (modalLoadingSpinner) {
                                modalLoadingSpinner.classList.remove('visually-hidden');
                            }
                            if (modalChapterList) {
                                modalChapterList.style.opacity = '0.3'; // Dim the chapter list
                            }

                            // Sort campaign cards after chapter selection
                            sortCampaignCards();

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

    // Auto-open campaign from URL parameters (e.g., ?c=vumbua or ?campaign=vumbua)
    const urlParams = new URLSearchParams(window.location.search);
    const campaignParam = urlParams.get('campaign') || urlParams.get('c');
    if (campaignParam) {
        const query = campaignParam.toLowerCase().trim();
        const targetCard = Array.from(campaignCards).find(card => {
            const title = (card.dataset.campaignTitle || "").toLowerCase();
            return title === query || title.includes(query);
        });
        if (targetCard) {
            setTimeout(() => {
                targetCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
                targetCard.click();
            }, 150);
        }
    }
});