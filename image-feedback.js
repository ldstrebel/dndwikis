/**
 * image-feedback.js
 * Enables users to press and hold (or long-click) any comic panel image 
 * to trigger a feedback modal with thumbs up/down and a free text area.
 */
(function() {
    let pressTimer = null;
    let targetImageSrc = "";
    
    // Create styles for modal, feedback indicators, and suppress native mobile menus
    const styleEl = document.createElement("style");
    styleEl.innerHTML = `
        .image-container-feedback {
            position: relative;
            cursor: pointer;
        }
        .image-container-feedback::after {
            content: "Hold to give feedback";
            position: absolute;
            bottom: 8px;
            right: 8px;
            background: rgba(15, 23, 42, 0.75);
            backdrop-filter: blur(4px);
            color: #94a3b8;
            font-size: 10px;
            padding: 4px 8px;
            border-radius: 4px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.3s ease;
        }
        .image-container-feedback:hover::after {
            opacity: 1;
        }
        
        /* Suppress default context menus and highlights on mobile browsers */
        .comic-panel img {
            -webkit-touch-callout: none !important; /* iOS Safari */
            -webkit-user-select: none !important;   /* Safari */
            -khtml-user-select: none !important;    /* Konqueror HTML */
            -moz-user-select: none !important;      /* Firefox */
            -ms-user-select: none !important;       /* Internet Explorer/Edge */
            user-select: none !important;           /* Non-prefixed version */
        }

        #feedbackModalOverlay {
            position: fixed;
            inset: 0;
            background-color: rgba(9, 13, 22, 0.85);
            backdrop-filter: blur(8px);
            z-index: 10000;
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.3s ease;
        }
        #feedbackModalOverlay.modal-visible {
            opacity: 1;
            pointer-events: auto;
        }
        .feedback-content-card {
            background-color: #1e293b;
            border: 1px solid rgba(51, 65, 85, 0.8);
            border-radius: 12px;
            width: 90%;
            max-width: 420px;
            padding: 24px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
            transform: scale(0.95);
            transition: transform 0.3s ease;
        }
        #feedbackModalOverlay.modal-visible .feedback-content-card {
            transform: scale(1);
        }
    `;
    document.head.appendChild(styleEl);

    // Create Modal HTML Structure
    const modalMarkup = `
        <div id="feedbackModalOverlay">
            <div class="feedback-content-card space-y-4" id="feedbackContentCard">
                <div class="flex justify-between items-center border-b border-slate-700 pb-3">
                    <h3 class="text-amber-400 font-bold text-lg">Panel Feedback</h3>
                    <button id="closeFeedbackModal" class="text-slate-400 hover:text-slate-200 text-xl font-bold">&times;</button>
                </div>
                
                <div class="text-xs text-slate-400 break-all bg-slate-900/60 p-2 rounded border border-slate-800" id="feedbackTargetLabel">
                    Target: -
                </div>

                <div class="space-y-2">
                    <label class="block text-sm font-semibold text-slate-200">How does this panel represent the story?</label>
                    <div class="flex gap-4">
                        <button id="btnFeedbackUp" class="flex-1 py-2 rounded-lg border border-slate-700 bg-slate-800/40 hover:bg-slate-800 text-center transition-colors flex items-center justify-center gap-2" data-val="up">
                            <span class="text-lg">👍</span> <span class="text-sm font-medium text-slate-200">Accurate</span>
                        </button>
                        <button id="btnFeedbackDown" class="flex-1 py-2 rounded-lg border border-slate-700 bg-slate-800/40 hover:bg-slate-800 text-center transition-colors flex items-center justify-center gap-2" data-val="down">
                            <span class="text-lg">👎</span> <span class="text-sm font-medium text-slate-200">Inaccurate</span>
                        </button>
                    </div>
                </div>

                <div class="space-y-2">
                    <label for="feedbackTextArea" class="block text-sm font-semibold text-slate-200">Free Comment</label>
                    <textarea id="feedbackTextArea" rows="3" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-500" placeholder="Describe layout corrections, character errors, or general suggestions..."></textarea>
                </div>

                <div class="flex gap-3 pt-2">
                    <button id="cancelFeedback" class="flex-1 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold rounded-lg text-sm transition-colors">Cancel</button>
                    <button id="submitFeedback" class="flex-1 py-2 bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold rounded-lg text-sm transition-colors shadow-lg shadow-amber-500/20">Submit</button>
                </div>
            </div>
        </div>
    `;

    const divContainer = document.createElement("div");
    divContainer.innerHTML = modalMarkup;
    document.body.appendChild(divContainer);

    const overlay = document.getElementById("feedbackModalOverlay");
    const contentCard = document.getElementById("feedbackContentCard");
    const closeBtn = document.getElementById("closeFeedbackModal");
    const cancelBtn = document.getElementById("cancelFeedback");
    const submitBtn = document.getElementById("submitFeedback");
    const label = document.getElementById("feedbackTargetLabel");
    const textInput = document.getElementById("feedbackTextArea");
    const btnUp = document.getElementById("btnFeedbackUp");
    const btnDown = document.getElementById("btnFeedbackDown");

    let currentRating = ""; // "up" or "down"

    // Set up ratings handlers
    btnUp.addEventListener("click", () => {
        currentRating = "up";
        btnUp.classList.add("border-amber-500", "bg-amber-500/10");
        btnDown.classList.remove("border-amber-500", "bg-amber-500/10");
    });

    btnDown.addEventListener("click", () => {
        currentRating = "down";
        btnDown.classList.add("border-amber-500", "bg-amber-500/10");
        btnUp.classList.remove("border-amber-500", "bg-amber-500/10");
    });

    function resetForm() {
        textInput.value = "";
        currentRating = "";
        btnUp.classList.remove("border-amber-500", "bg-amber-500/10");
        btnDown.classList.remove("border-amber-500", "bg-amber-500/10");
    }

    function showModal(imgSrc) {
        targetImageSrc = imgSrc;
        const filename = imgSrc.substring(imgSrc.lastIndexOf("/") + 1);
        label.textContent = `Target Panel: ${filename}`;
        resetForm();
        overlay.classList.add("modal-visible");
    }

    function hideModal() {
        overlay.classList.remove("modal-visible");
    }

    // Modal triggers - Tap/Click anywhere outside the card content container to close
    closeBtn.addEventListener("click", hideModal);
    cancelBtn.addEventListener("click", hideModal);
    overlay.addEventListener("click", (e) => {
        if (!contentCard.contains(e.target)) {
            hideModal();
        }
    });

    // Submit handler (saves to LocalStorage / triggers mock analytics call)
    submitBtn.addEventListener("click", () => {
        if (!currentRating && !textInput.value.trim()) {
            alert("Please provide a thumbs rating or input a suggestion before submitting.");
            return;
        }

        const submission = {
            panel: targetImageSrc,
            rating: currentRating,
            comment: textInput.value.trim(),
            timestamp: new Date().toISOString()
        };

        // Retrieve existing logs
        let allFeedback = JSON.parse(localStorage.getItem("panel_feedback_logs") || "[]");
        allFeedback.push(submission);
        localStorage.setItem("panel_feedback_logs", JSON.stringify(allFeedback));

        // Proprogate to global analytics tag if available
        if (typeof window.gtag === "function") {
            window.gtag("event", "panel_feedback", {
                event_category: "comic_engagement",
                panel_src: targetImageSrc,
                rating_score: currentRating,
                feedback_text: textInput.value.trim()
            });
        }

        alert("Thank you! Feedback recorded successfully.");
        hideModal();
    });

    // Wire up events for images inside .comic-panel elements
    const images = document.querySelectorAll(".comic-panel img");
    images.forEach(img => {
        const parent = img.parentElement;
        if (parent) {
            parent.classList.add("image-container-feedback");
        }

        // Timer actions - increased hold threshold to 900ms to avoid scroll issues
        function startPress(e) {
            cancelPress();
            pressTimer = setTimeout(() => {
                showModal(img.src);
            }, 900);
        }

        function cancelPress() {
            if (pressTimer) {
                clearTimeout(pressTimer);
                pressTimer = null;
            }
        }

        // Intercept and prevent the browser's default context menus (e.g. Save Image Options)
        img.addEventListener("contextmenu", (e) => {
            e.preventDefault();
            e.stopPropagation();
            return false;
        });

        // Pointer/Touch Listeners
        img.addEventListener("mousedown", startPress);
        img.addEventListener("mouseup", cancelPress);
        img.addEventListener("mouseleave", cancelPress);

        img.addEventListener("touchstart", (e) => {
            // Cancel native long-press popup trigger on some browsers
            startPress(e);
        }, { passive: true });
        img.addEventListener("touchend", cancelPress);
        img.addEventListener("touchcancel", cancelPress);
        
        // Touchmove represents active scrolling; cancel press immediately to prevent modal trigger
        img.addEventListener("touchmove", cancelPress, { passive: true });
    });
})();
