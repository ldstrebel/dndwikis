/**
 * image-feedback.js
 * Enables users to press and hold (or long-click) any comic panel image 
 * to trigger a feedback modal with thumbs up/down and a free text area.
 * Automatically synchronizes submissions and user telemetry to Firebase Firestore.
 */
(function() {
    let pressTimer = null;
    let targetImageSrc = "";
    
    // Firestore REST API Endpoint Config
    const FIRESTORE_PROJECT = "thecountgame";
    const API_FEEDBACK_ENDPOINT = `https://firestore.googleapis.com/v1/projects/${FIRESTORE_PROJECT}/databases/(default)/documents/vumbua_panel_feedback`;
    const API_TELEMETRY_ENDPOINT = `https://firestore.googleapis.com/v1/projects/${FIRESTORE_PROJECT}/databases/(default)/documents/vumbua_user_telemetry`;

    // Local Storage anonymous session identifiers
    let sessionId = localStorage.getItem("vumbua_session_uuid");
    if (!sessionId) {
        sessionId = "sess_" + Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
        localStorage.setItem("vumbua_session_uuid", sessionId);
    }

    // Capture device detail heuristics
    const getDeviceDetails = () => {
        const ua = navigator.userAgent;
        let device = "Desktop";
        if (/Mobi|Android|iPhone|iPad|iPod/i.test(ua)) {
            device = "Mobile";
        }
        return {
            userAgent: ua,
            deviceType: device,
            platform: navigator.platform,
            screenSize: `${window.innerWidth}x${window.innerHeight}`
        };
    };

    // Telemetry Session State variables
    const sessionStart = Date.now();
    let maxScrollPercent = 0;
    const path = window.location.pathname;
    const pageName = path.substring(path.lastIndexOf("/") + 1) || "index.html";

    // Track active panel timers (which ones are viewed the longest)
    const panelViews = {}; // Maps panel image src to total visible milliseconds
    let activeVisiblePanel = null;
    let activePanelStartTime = null;

    // Create styles for modal, feedback indicators, native mobile menu suppressions, and footer links
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

        .share-feedback-container {
            margin-top: 1.5rem;
            padding: 1rem;
            text-align: center;
            background: rgba(15, 23, 42, 0.4);
            border: 1px dashed rgba(51, 65, 85, 0.5);
            border-radius: 8px;
        }
        .share-feedback-btn {
            font-size: 13px;
            font-weight: 600;
            color: #38bdf8;
            background: none;
            border: none;
            cursor: pointer;
            text-decoration: underline;
            transition: color 0.2s ease;
        }
        .share-feedback-btn:hover {
            color: #f59e0b;
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

    let currentRating = "";

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

    closeBtn.addEventListener("click", hideModal);
    cancelBtn.addEventListener("click", hideModal);
    overlay.addEventListener("click", (e) => {
        if (!contentCard.contains(e.target)) {
            hideModal();
        }
    });

    // Send Feedback document to Firestore
    const pushFeedbackToFirestore = (submission) => {
        const payload = {
            fields: {
                sessionId: { stringValue: sessionId },
                panel: { stringValue: submission.panel },
                rating: { stringValue: submission.rating || "none" },
                comment: { stringValue: submission.comment },
                timestamp: { timestampValue: submission.timestamp },
                deviceType: { stringValue: getDeviceDetails().deviceType },
                screenSize: { stringValue: getDeviceDetails().screenSize },
                platform: { stringValue: getDeviceDetails().platform }
            }
        };

        fetch(API_FEEDBACK_ENDPOINT, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        })
        .then(res => {
            if (!res.ok) console.error("Firestore feedback sync error status:", res.status);
        })
        .catch(err => console.error("Firestore feedback network error:", err));
    };

    submitBtn.addEventListener("click", () => {
        if (!currentRating && !textInput.value.trim()) {
            alert("Please provide a thumbs rating or input a suggestion before submitting.");
            return;
        }

        const submission = {
            panel: targetImageSrc.substring(targetImageSrc.lastIndexOf("/") + 1),
            rating: currentRating,
            comment: textInput.value.trim(),
            timestamp: new Date().toISOString()
        };

        // Cache to LocalStorage fallback
        let allFeedback = JSON.parse(localStorage.getItem("panel_feedback_logs") || "[]");
        allFeedback.push(submission);
        localStorage.setItem("panel_feedback_logs", JSON.stringify(allFeedback));

        // Central Server Sync
        pushFeedbackToFirestore(submission);

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

    // Event hooks for image long-press triggers
    const images = document.querySelectorAll(".comic-panel img");
    images.forEach(img => {
        const parent = img.parentElement;
        if (parent) {
            parent.classList.add("image-container-feedback");
        }

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

        img.addEventListener("contextmenu", (e) => {
            e.preventDefault();
            e.stopPropagation();
            return false;
        });

        img.addEventListener("mousedown", startPress);
        img.addEventListener("mouseup", cancelPress);
        img.addEventListener("mouseleave", cancelPress);

        img.addEventListener("touchstart", (e) => {
            startPress(e);
        }, { passive: true });
        img.addEventListener("touchend", cancelPress);
        img.addEventListener("touchcancel", cancelPress);
        img.addEventListener("touchmove", cancelPress, { passive: true });
    });

    // -------------------------------------------------------------
    // USER BEHAVIOR TELEMETRY PIPELINE
    // -------------------------------------------------------------

    // Send session telemetry document to Firestore on tab hide/exit
    const pushTelemetryToFirestore = (isFinal = false) => {
        // Capture view times for active panels before final compile
        trackPanelTime(null); 

        // Convert panelViews dictionary to document map fields for Firestore structure
        const panelFields = {};
        for (const [panelKey, ms] of Object.entries(panelViews)) {
            const shortName = panelKey.substring(panelKey.lastIndexOf("/") + 1);
            panelFields[shortName.replace(/\./g, "_")] = { integerValue: Math.round(ms / 1000) }; // round to seconds
        }

        const device = getDeviceDetails();
        const durationSec = Math.round((Date.now() - sessionStart) / 1000);

        const payload = {
            fields: {
                sessionId: { stringValue: sessionId },
                page: { stringValue: pageName },
                sessionDurationSeconds: { integerValue: durationSec },
                maxScrollPercent: { integerValue: Math.round(maxScrollPercent) },
                lastActivePanel: { stringValue: activeVisiblePanel ? activeVisiblePanel.substring(activeVisiblePanel.lastIndexOf("/") + 1) : "none" },
                deviceType: { stringValue: device.deviceType },
                screenSize: { stringValue: device.screenSize },
                platform: { stringValue: device.platform },
                timestamp: { timestampValue: new Date().toISOString() },
                panelViews: {
                    mapValue: {
                        fields: panelFields
                    }
                }
            }
        };

        // Utilize sendBeacon for exit requests if supported, otherwise fallback to standard fetch
        const bodyStr = JSON.stringify(payload);
        if (isFinal && navigator.sendBeacon) {
            navigator.sendBeacon(API_TELEMETRY_ENDPOINT, bodyStr);
        } else {
            fetch(API_TELEMETRY_ENDPOINT, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: bodyStr
            })
            .catch(err => console.error("Telemetry fetch logging error:", err));
        }
    };

    // Tracking active panel timings based on visibility
    const trackPanelTime = (newActivePanel) => {
        const now = Date.now();
        if (activeVisiblePanel && activePanelStartTime) {
            const viewDuration = now - activePanelStartTime;
            if (viewDuration > 500) { // filter out brief scroll passes under 500ms
                panelViews[activeVisiblePanel] = (panelViews[activeVisiblePanel] || 0) + viewDuration;
            }
        }
        activeVisiblePanel = newActivePanel;
        activePanelStartTime = now;
    };

    // Track scroll depth percentage
    window.addEventListener("scroll", () => {
        const totalHeight = document.documentElement.scrollHeight - window.innerHeight;
        if (totalHeight > 0) {
            const currentPct = (window.scrollY / totalHeight) * 100;
            if (currentPct > maxScrollPercent) {
                maxScrollPercent = currentPct;
            }
        }
    }, { passive: true });

    // Track visible panel shifts using a viewport center check
    const panelObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target.querySelector("img");
                if (img) {
                    trackPanelTime(img.src);
                }
            }
        });
    }, { root: null, rootMargin: "-40% 0px -40% 0px", threshold: 0.1 });

    document.querySelectorAll("main > section").forEach(section => {
        panelObserver.observe(section);
    });

    // Push heartbeat every 30 seconds to capture active reader telemetry
    const heartbeatInterval = setInterval(() => {
        pushTelemetryToFirestore(false);
    }, 30000);

    // Final push on session unload / tab change
    window.addEventListener("visibilitychange", () => {
        if (document.visibilityState === "hidden") {
            pushTelemetryToFirestore(true);
        }
    });

    window.addEventListener("pagehide", () => {
        pushTelemetryToFirestore(true);
    });

    // -------------------------------------------------------------
    // EXPORTER UI SETUP
    // -------------------------------------------------------------
    const footer = document.querySelector("footer");
    if (footer) {
        const shareContainer = document.createElement("div");
        shareContainer.className = "share-feedback-container";
        shareContainer.innerHTML = `
            <span class="text-xs text-slate-500 mr-2">Done reviewing?</span>
            <button class="share-feedback-btn" id="shareFeedbackBtn">Share click + hold feedback</button>
        `;
        footer.insertBefore(shareContainer, footer.firstChild);

        const shareBtn = document.getElementById("shareFeedbackBtn");
        shareBtn.addEventListener("click", () => {
            const logs = localStorage.getItem("panel_feedback_logs");
            if (!logs || JSON.parse(logs).length === 0) {
                alert("No feedback reviews found to export! Long-press panels to submit reviews first.");
                return;
            }

            const formattedLogs = JSON.parse(logs).map((l, index) => {
                return `[${index + 1}] Panel: ${l.panel}\nRating: ${l.rating === 'up' ? '👍' : '👎'}\nComment: ${l.comment}\n`;
            }).join("\n");

            const shareData = {
                title: "Vumbua Storybook Panel Feedback",
                text: `Here is the panel review feedback for the Vumbua Campaign:\n\n${formattedLogs}`,
            };

            if (navigator.share) {
                navigator.share(shareData).catch(err => console.log("Error sharing:", err));
            } else {
                navigator.clipboard.writeText(shareData.text)
                    .then(() => {
                        alert("Device sharing not supported by this browser. Feedback reviews copied to clipboard instead! Paste them into Slack, email, or text to share.");
                    })
                    .catch(err => alert("Could not copy logs to clipboard: " + err));
            }
        });
    }

    // Top Sticky Navigation Share page
    const sessionShareBtn = document.getElementById("sessionShareBtn");
    if (sessionShareBtn) {
        sessionShareBtn.addEventListener("click", () => {
            const shareData = {
                title: document.title,
                url: window.location.href
            };
            if (navigator.share) {
                navigator.share(shareData)
                    .catch(err => console.log("Error sharing page:", err));
            } else {
                navigator.clipboard.writeText(shareData.url)
                    .then(() => alert("Page link copied to clipboard!"))
                    .catch(err => console.error("Could not copy link:", err));
            }
        });
    }
})();
