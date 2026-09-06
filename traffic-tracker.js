/**
 * traffic-tracker.js - D&D Wikis Lightweight Visitor Tracker & Slack Notifier
 * Zero backend required - runs directly on GitHub Pages!
 */
(function() {
    // Storage & Cloud Sync Constants
    const STORAGE_KEY = 'dndwikis_tracker_config';
    const VISITOR_ID_KEY = 'dndwikis_visitor_uuid';
    const VISITOR_HISTORY_KEY = 'dndwikis_local_visits';
    const CLOUD_SYNC_ENDPOINT = 'https://kvdb.io/4yZ3q9N1X8vFm7Lp2kR6w/';
    const CLOUD_KEY_STATS = 'stats_v1';
    const CLOUD_KEY_CONFIG = 'config_v1';

    // Default configuration
    const defaultConfig = {
        slackWebhookUrl: '', // Configured via super-secret-stats.html
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

    // Helper: Send Slack Notification
    async function sendSlackAlert(webhookUrl, details) {
        if (!webhookUrl || !webhookUrl.startsWith('https://hooks.slack.com/')) {
            console.warn('[D&D Tracker] Slack Webhook URL is not configured yet. Configure it in super-secret-stats.html');
            return;
        }

        const pageTitle = document.title || 'D&D Wikis Page';
        const pageUrl = window.location.href;
        const device = getDeviceType();
        const visitorNumber = details.uniqueTotal ? ` (#${details.uniqueTotal})` : '';

        const payload = {
            blocks: [
                {
                    type: "header",
                    text: {
                        type: "plain_text",
                        text: "🎲 D&D Wikis - New Visitor Alert!",
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
                            text: `*Visitor:*\n✨ New Unique Reader${visitorNumber}`
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

        try {
            await fetch(webhookUrl, {
                method: 'POST',
                mode: 'no-cors',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: 'payload=' + encodeURIComponent(JSON.stringify(payload))
            });
            console.log('[D&D Tracker] Slack notification dispatched');
        } catch (err) {
            console.error('[D&D Tracker] Failed to send Slack alert:', err);
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

        const visitRecord = {
            id: visitorId,
            isNew: isNewVisitor,
            page: page,
            title: title,
            url: window.location.href,
            device: getDeviceType(),
            timestamp: now
        };

        // 1. Save locally
        try {
            const localHistory = JSON.parse(localStorage.getItem(VISITOR_HISTORY_KEY) || '[]');
            localHistory.push(visitRecord);
            if (localHistory.length > 50) localHistory.shift();
            localStorage.setItem(VISITOR_HISTORY_KEY, JSON.stringify(localHistory));
        } catch (e) {}

        // 2. Fetch latest config & stats from cloud store
        let config = getLocalConfig();
        let cloudStats = { totalVisits: 0, uniqueVisitors: {}, visits: [] };

        try {
            const configRes = await fetch(CLOUD_SYNC_ENDPOINT + CLOUD_KEY_CONFIG, { cache: 'no-cache' });
            if (configRes.ok) {
                const remoteConfig = await configRes.json();
                config = { ...config, ...remoteConfig };
                localStorage.setItem(STORAGE_KEY, JSON.stringify(config));
            }
        } catch (e) {}

        try {
            const statsRes = await fetch(CLOUD_SYNC_ENDPOINT + CLOUD_KEY_STATS, { cache: 'no-cache' });
            if (statsRes.ok) {
                cloudStats = await statsRes.json();
            }
        } catch (e) {}

        // Update stats
        cloudStats.totalVisits = (cloudStats.totalVisits || 0) + 1;
        if (!cloudStats.uniqueVisitors) cloudStats.uniqueVisitors = {};

        // Track visitor profile (firstSeen, lastSeen, visitCount)
        if (!cloudStats.uniqueVisitors[visitorId]) {
            cloudStats.uniqueVisitors[visitorId] = {
                firstSeen: now,
                lastSeen: now,
                count: 1
            };
        } else {
            const profile = cloudStats.uniqueVisitors[visitorId];
            // Normalize if older timestamp format
            if (typeof profile === 'number') {
                cloudStats.uniqueVisitors[visitorId] = {
                    firstSeen: profile,
                    lastSeen: now,
                    count: 2
                };
            } else {
                profile.lastSeen = now;
                profile.count = (profile.count || 1) + 1;
            }
        }

        if (!cloudStats.visits) cloudStats.visits = [];
        cloudStats.visits.unshift(visitRecord);
        if (cloudStats.visits.length > 100) cloudStats.visits.length = 100;

        // Prune visitors older than 30 days
        const thirtyDaysAgo = now - (30 * 24 * 60 * 60 * 1000);
        Object.keys(cloudStats.uniqueVisitors).forEach(id => {
            const v = cloudStats.uniqueVisitors[id];
            const lastSeen = typeof v === 'number' ? v : v.lastSeen;
            if (lastSeen < thirtyDaysAgo) {
                delete cloudStats.uniqueVisitors[id];
            }
        });

        // Save back to cloud store
        try {
            await fetch(CLOUD_SYNC_ENDPOINT + CLOUD_KEY_STATS, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(cloudStats)
            });
        } catch (e) {}

        // 3. Evaluate alert triggers
        if (!config.enabled || !config.slackWebhookUrl) return;

        let shouldAlert = false;
        if (config.alertMode === 'every') {
            // ONLY alert on brand new unique visitors (never on repeat users)
            if (isNewVisitor) {
                shouldAlert = true;
            }
        } else if (config.alertMode === 'threshold') {
            // Alert every X total visits
            const threshold = parseInt(config.threshold, 10) || 10;
            if (cloudStats.totalVisits % threshold === 0) {
                shouldAlert = true;
            }
        }

        if (shouldAlert) {
            const uniqueTotal = Object.keys(cloudStats.uniqueVisitors || {}).length;
            sendSlackAlert(config.slackWebhookUrl, {
                isNew: isNewVisitor,
                uniqueTotal: uniqueTotal
            });
        }
    }

    // Expose Global Helper for the Stats Page
    window.DndWikiTracker = {
        getConfig: getLocalConfig,
        saveConfig: async function(newConfig) {
            const merged = { ...getLocalConfig(), ...newConfig };
            localStorage.setItem(STORAGE_KEY, JSON.stringify(merged));
            try {
                await fetch(CLOUD_SYNC_ENDPOINT + CLOUD_KEY_CONFIG, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(merged)
                });
            } catch (e) {}
            return merged;
        },
        getStats: async function() {
            try {
                const res = await fetch(CLOUD_SYNC_ENDPOINT + CLOUD_KEY_STATS, { cache: 'no-cache' });
                if (res.ok) return await res.json();
            } catch (e) {}
            return {
                totalVisits: 0,
                uniqueVisitors: {},
                visits: []
            };
        },
        testSlackAlert: function(webhookUrl) {
            return sendSlackAlert(webhookUrl, { isNew: true, uniqueTotal: 'TEST' });
        }
    };

    // Run tracker when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', recordVisit);
    } else {
        recordVisit();
    }
})();
