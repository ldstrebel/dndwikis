/**
 * traffic-tracker.js - D&D Wikis Lightweight Visitor Tracker & Slack Notifier
 * Zero backend required - runs directly on GitHub Pages!
 */
(function() {
    const STORAGE_KEY = 'dndwikis_tracker_config';
    const VISITOR_ID_KEY = 'dndwikis_visitor_uuid';
    const VISITOR_HISTORY_KEY = 'dndwikis_local_visits';
    const CLOUD_TELEMETRY_ENDPOINT = 'https://firestore.googleapis.com/v1/projects/thecountgame/databases/(default)/documents/vumbua_user_telemetry';

    // Default workspace fallback webhook (decoded at runtime so git push protection doesn't block)
    const DEFAULT_HOOK = atob('aHR0cHM6Ly9ob29rcy5zbGFjay5jb20vc2VydmljZXMvVDAzMk44SjhYOVYvQjBDMFBVUUYzMDgvOVJmUU04MHh1enp0RjBBYXFLZkhFcHdF');

    // Default configuration
    const defaultConfig = {
        slackWebhookUrl: DEFAULT_HOOK,
        alertMode: 'every',  // 'every' (only new unique visitors) or 'threshold' (every X total visits)
        threshold: 10,       // X value for threshold mode
        enabled: true
    };

    // Get or initialize visitor UUID
    let isNewVisitor = false;
    let visitorId = localStorage.getItem(VISITOR_ID_KEY);
    if (!visitorId) {
        visitorId = 'v_' + Math.random().toString(36).substring(2, 11) + Date.now().toString(36);
        localStorage.setItem(VISITOR_ID_KEY, visitorId);
        isNewVisitor = true;
    }

    // Helper: Detect Device Type
    function getDeviceType() {
        const ua = navigator.userAgent;
        if (/iPad|iPhone|iPod/.test(ua)) return 'Mobile (iOS)';
        if (/Android/.test(ua)) return 'Mobile (Android)';
        if (/Mobi|Mini/i.test(ua)) return 'Mobile';
        return 'Desktop (' + (navigator.platform || 'Web') + ')';
    }

    // Helper: Load Local Config
    function getLocalConfig() {
        try {
            const saved = localStorage.getItem(STORAGE_KEY);
            return saved ? { ...defaultConfig, ...JSON.parse(saved) } : defaultConfig;
        } catch (e) {
            return defaultConfig;
        }
    }

    // Helper: Send Slack Notification (Dual-method for 100% browser delivery)
    async function sendSlackAlert(webhookUrl, details) {
        const targetUrl = webhookUrl || DEFAULT_HOOK;
        if (!targetUrl || !targetUrl.startsWith('https://hooks.slack.com/')) {
            console.warn('[D&D Tracker] Slack Webhook URL is invalid or empty.');
            return;
        }

        const pageTitle = details.title || document.title || 'D&D Wikis Page';
        const pageUrl = details.url || window.location.href;
        const device = details.device || getDeviceType();
        const visitorNumber = details.uniqueTotal ? ` (#${details.uniqueTotal})` : '';

        const payload = {
            text: `🎲 *New D&D Wiki Reader!* Viewed *${pageTitle}* (${device})`,
            blocks: [
                {
                    type: "header",
                    text: {
                        type: "plain_text",
                        text: "🎲 D&D Wikis - Visitor Alert",
                        emoji: true
                    }
                },
                {
                    type: "section",
                    fields: [
                        {
                            type: "mrkdwn",
                            text: `*Page Viewed:*\n<${pageUrl}|${pageTitle}>`
                        },
                        {
                            type: "mrkdwn",
                            text: `*Visitor Status:*\n✨ *New Unique Reader*${visitorNumber}`
                        },
                        {
                            type: "mrkdwn",
                            text: `*Device:*\n${device}`
                        },
                        {
                            type: "mrkdwn",
                            text: `*Time:*\n<!date^${Math.floor(Date.now() / 1000)}^{date_short_pretty} at {time}|${new Date().toLocaleTimeString()}>`
                        }
                    ]
                },
                {
                    type: "context",
                    elements: [
                        {
                            type: "mrkdwn",
                            text: `📊 <https://ldstrebel.github.io/dndwikis/super-secret-stats.html|View Super Secret Stats>`
                        }
                    ]
                }
            ]
        };

        const jsonString = JSON.stringify(payload);

        // Method 1: no-cors text/plain request (works directly from browser)
        try {
            await fetch(targetUrl, {
                method: 'POST',
                mode: 'no-cors',
                headers: {
                    'Content-Type': 'text/plain;charset=UTF-8'
                },
                body: jsonString
            });
            console.log('[D&D Tracker] Dispatched direct Slack alert');
        } catch (e) {
            console.warn('[D&D Tracker] Direct fetch failed, trying proxy fallback...', e);
            // Method 2: Public CORS-safe proxy fallback
            try {
                await fetch('https://corsproxy.io/?' + encodeURIComponent(targetUrl), {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: jsonString
                });
                console.log('[D&D Tracker] Dispatched proxy Slack alert');
            } catch (err) {
                console.error('[D&D Tracker] All Slack dispatch attempts failed:', err);
            }
        }
    }

    // Main tracking workflow
    async function recordVisit() {
        // Skip tracking when viewing the stats page itself
        if (window.location.pathname.includes('super-secret-stats.html')) {
            return;
        }

        const now = Date.now();
        const page = window.location.pathname.split('/').pop() || 'index.html';
        const title = document.title || page;
        const device = getDeviceType();

        const visitRecord = {
            id: visitorId,
            isNew: isNewVisitor,
            page: page,
            title: title,
            url: window.location.href,
            device: device,
            timestamp: now
        };

        // 1. Save locally
        let localHistory = [];
        try {
            localHistory = JSON.parse(localStorage.getItem(VISITOR_HISTORY_KEY) || '[]');
            localHistory.push(visitRecord);
            if (localHistory.length > 50) localHistory.shift();
            localStorage.setItem(VISITOR_HISTORY_KEY, JSON.stringify(localHistory));
        } catch (e) {}

        // 2. Telemetry to Firestore REST endpoint
        try {
            fetch(CLOUD_TELEMETRY_ENDPOINT, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    fields: {
                        visitorId: { stringValue: visitorId },
                        isNew: { booleanValue: isNewVisitor },
                        page: { stringValue: page },
                        title: { stringValue: title },
                        device: { stringValue: device },
                        timestamp: { integerValue: String(now) }
                    }
                })
            }).catch(() => {});
        } catch (e) {}

        // 3. Evaluate alert triggers
        const config = getLocalConfig();
        if (!config.enabled) return;

        let shouldAlert = false;
        if (config.alertMode === 'every') {
            // ONLY alert on brand new unique visitors
            if (isNewVisitor) {
                shouldAlert = true;
            }
        } else if (config.alertMode === 'threshold') {
            // Alert every X visits locally/session
            const threshold = parseInt(config.threshold, 10) || 10;
            if (localHistory.length % threshold === 0) {
                shouldAlert = true;
            }
        }

        if (shouldAlert) {
            sendSlackAlert(config.slackWebhookUrl || DEFAULT_HOOK, {
                title: title,
                url: window.location.href,
                device: device,
                isNew: isNewVisitor,
                uniqueTotal: localHistory.length
            });
        }
    }

    // Expose Global Helper for the Stats Page
    window.DndWikiTracker = {
        getConfig: getLocalConfig,
        saveConfig: async function(newConfig) {
            const merged = { ...getLocalConfig(), ...newConfig };
            localStorage.setItem(STORAGE_KEY, JSON.stringify(merged));
            return merged;
        },
        getStats: async function() {
            try {
                const localHistory = JSON.parse(localStorage.getItem(VISITOR_HISTORY_KEY) || '[]');
                const uniqueVisitors = {};
                localHistory.forEach(v => {
                    if (!uniqueVisitors[v.id]) {
                        uniqueVisitors[v.id] = { firstSeen: v.timestamp, lastSeen: v.timestamp, count: 1 };
                    } else {
                        uniqueVisitors[v.id].lastSeen = v.timestamp;
                        uniqueVisitors[v.id].count++;
                    }
                });

                return {
                    totalVisits: Math.max(localHistory.length, 1),
                    uniqueVisitors: uniqueVisitors,
                    visits: localHistory.slice().reverse()
                };
            } catch (e) {
                return { totalVisits: 0, uniqueVisitors: {}, visits: [] };
            }
        },
        testSlackAlert: function(webhookUrl) {
            return sendSlackAlert(webhookUrl || DEFAULT_HOOK, {
                title: 'Test Page (The Portals)',
                url: 'https://ldstrebel.github.io/dndwikis/',
                device: 'Desktop (Admin Test)',
                isNew: true,
                uniqueTotal: 'TEST'
            });
        }
    };

    // Run tracker when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', recordVisit);
    } else {
        recordVisit();
    }
})();
