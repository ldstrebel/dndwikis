/**
 * dice-physics.js - D&D Wikis Physics-Based D20 Dice Roller
 * Adapted from Latest Distraction with full D20 icosahedron geometry,
 * tumbling physics, Nat 20 confetti, and Nat 1 glass-crack effects.
 */
(function() {
    let canvas = null;
    let ctx = null;
    let animId = null;
    let isRolling = false;

    // Initialize overlay canvas
    function initCanvas() {
        if (canvas) return;
        canvas = document.createElement('canvas');
        canvas.id = 'dicePhysicsCanvas';
        canvas.style.position = 'fixed';
        canvas.style.top = '0';
        canvas.style.left = '0';
        canvas.style.width = '100vw';
        canvas.style.height = '100vh';
        canvas.style.pointerEvents = 'none';
        canvas.style.zIndex = '9998';
        canvas.style.opacity = '0';
        canvas.style.transition = 'opacity 0.3s ease';
        document.body.appendChild(canvas);
        ctx = canvas.getContext('2d');

        window.addEventListener('resize', () => {
            if (canvas) {
                canvas.width = window.innerWidth;
                canvas.height = window.innerHeight;
            }
        });
    }

    // Draw D20 Icosahedron Faceted Die on Canvas
    function drawD20(ctx, x, y, size, angle, value, isCrit20, isCrit1) {
        ctx.save();
        ctx.translate(x, y);
        ctx.rotate(angle);

        const r = size / 2;

        // Shadow
        ctx.shadowColor = isCrit20 ? 'rgba(212, 175, 55, 0.6)' : (isCrit1 ? 'rgba(239, 68, 68, 0.6)' : 'rgba(0, 0, 0, 0.5)');
        ctx.shadowBlur = isCrit20 ? 25 : (isCrit1 ? 25 : 12);
        ctx.shadowOffsetY = 6;

        // Colors based on theme
        const baseColor = isCrit20 ? '#d4af37' : (isCrit1 ? '#dc2626' : '#25B8B8');
        const darkColor = isCrit20 ? '#785b12' : (isCrit1 ? '#7f1d1d' : '#146464');
        const highlightColor = isCrit20 ? '#fef08a' : (isCrit1 ? '#fca5a5' : '#50D8D8');

        // Hexagonal Outer Silhouette (D20 projected outline)
        const hexPoints = [];
        for (let i = 0; i < 6; i++) {
            const a = (i * Math.PI / 3) - (Math.PI / 6);
            hexPoints.push({ x: r * Math.cos(a), y: r * Math.sin(a) });
        }

        // Inner Triangle (center face)
        const innerTri = [];
        const innerR = r * 0.52;
        for (let i = 0; i < 3; i++) {
            const a = (i * 2 * Math.PI / 3) - (Math.PI / 2);
            innerTri.push({ x: innerR * Math.cos(a), y: innerR * Math.sin(a) });
        }

        // 1. Fill Outer Base
        ctx.beginPath();
        ctx.moveTo(hexPoints[0].x, hexPoints[0].y);
        for (let i = 1; i < 6; i++) ctx.lineTo(hexPoints[i].x, hexPoints[i].y);
        ctx.closePath();
        ctx.fillStyle = darkColor;
        ctx.fill();
        ctx.lineWidth = 2.5;
        ctx.strokeStyle = highlightColor;
        ctx.stroke();

        // 2. Draw 6 Outer Facets (Triangles between inner triangle and outer hexagon)
        ctx.shadowBlur = 0; // Disable shadow for internal facet lines
        const facetPairs = [
            [hexPoints[0], hexPoints[1], innerTri[0]],
            [hexPoints[1], innerTri[1], innerTri[0]],
            [hexPoints[1], hexPoints[2], innerTri[1]],
            [hexPoints[2], hexPoints[3], innerTri[1]],
            [hexPoints[3], hexPoints[4], innerTri[2]],
            [hexPoints[4], innerTri[2], innerTri[0]],
            [hexPoints[4], hexPoints[5], innerTri[0]],
            [hexPoints[5], hexPoints[0], innerTri[0]]
        ];

        facetPairs.forEach((tri, idx) => {
            ctx.beginPath();
            ctx.moveTo(tri[0].x, tri[0].y);
            ctx.lineTo(tri[1].x, tri[1].y);
            ctx.lineTo(tri[2].x, tri[2].y);
            ctx.closePath();
            ctx.fillStyle = idx % 2 === 0 ? baseColor + 'bb' : darkColor + 'ee';
            ctx.fill();
            ctx.strokeStyle = highlightColor + '88';
            ctx.lineWidth = 1;
            ctx.stroke();
        });

        // 3. Draw Center Triangle Face
        ctx.beginPath();
        ctx.moveTo(innerTri[0].x, innerTri[0].y);
        ctx.lineTo(innerTri[1].x, innerTri[1].y);
        ctx.lineTo(innerTri[2].x, innerTri[2].y);
        ctx.closePath();
        ctx.fillStyle = isCrit20 ? '#fde047' : (isCrit1 ? '#ef4444' : '#1e293b');
        ctx.fill();
        ctx.lineWidth = 2;
        ctx.strokeStyle = highlightColor;
        ctx.stroke();

        // 4. Draw Number on Center Face
        ctx.fillStyle = isCrit20 ? '#181a1b' : (isCrit1 ? '#ffffff' : '#50D8D8');
        ctx.font = `bold ${Math.round(r * 0.46)}px 'Cinzel Decorative', 'MedievalSharp', Inter, sans-serif`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(String(value), 0, innerR * 0.1);

        ctx.restore();
    }

    // Launch Physics Simulation
    window.rollD20Physics = function(onComplete) {
        initCanvas();
        if (isRolling) return;
        isRolling = true;

        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        canvas.style.opacity = '1';

        const width = canvas.width;
        const height = canvas.height;
        const finalValue = Math.floor(Math.random() * 20) + 1;
        const isCrit20 = finalValue === 20;
        const isCrit1 = finalValue === 1;

        const size = Math.min(Math.max(width * 0.12, 85), 130);
        const radius = size / 2;

        // Initial launch trajectory (thrown from bottom-center upwards with random angle & spin)
        const die = {
            x: width * (0.35 + Math.random() * 0.3),
            y: height - 80,
            vx: (Math.random() - 0.5) * 18,
            vy: -16 - Math.random() * 8,
            angle: Math.random() * Math.PI * 2,
            vAngle: (Math.random() - 0.5) * 0.35,
            value: Math.floor(Math.random() * 20) + 1,
            size: size
        };

        const gravity = 0.55;
        const restitution = 0.68;
        const friction = 0.98;
        const startTime = Date.now();
        const rollDuration = 1800; // 1.8s physics duration

        let stage = 'rolling'; // 'rolling', 'settled', 'fade'
        let settleTime = 0;
        let confetti = [];
        let crackLines = [];
        let crackProgress = 0;

        // Generate Glass Shatter Cracks for Nat 1
        function generateCracks(originX, originY) {
            const numBranches = 10 + Math.floor(Math.random() * 4);
            for (let i = 0; i < numBranches; i++) {
                const baseAngle = (i / numBranches) * Math.PI * 2 + (Math.random() * 0.3 - 0.15);
                let cx = originX;
                let cy = originY;
                const segments = 4 + Math.floor(Math.random() * 4);
                const segLen = 25 + Math.random() * 30;

                for (let j = 0; j < segments; j++) {
                    const angle = baseAngle + (Math.random() * 0.5 - 0.25);
                    const nx = cx + Math.cos(angle) * segLen;
                    const ny = cy + Math.sin(angle) * segLen;
                    crackLines.push({ x1: cx, y1: cy, x2: nx, y2: ny, t: j / segments });
                    cx = nx;
                    cy = ny;
                }
            }
        }

        // Spawn Confetti for Nat 20
        function spawnConfetti() {
            for (let i = 0; i < 140; i++) {
                confetti.push({
                    x: width / 2 + (Math.random() - 0.5) * 200,
                    y: height / 2 + (Math.random() - 0.5) * 100,
                    vx: (Math.random() - 0.5) * 12,
                    vy: -8 - Math.random() * 10,
                    color: `hsl(${Math.random() * 360}, 95%, 60%)`,
                    size: 5 + Math.random() * 7,
                    rot: Math.random() * Math.PI * 2,
                    vRot: (Math.random() - 0.5) * 0.2
                });
            }
        }

        function loop() {
            const now = Date.now();
            const elapsed = now - startTime;

            ctx.clearRect(0, 0, width, height);

            if (stage === 'rolling') {
                if (elapsed < rollDuration - 300) {
                    // Apply Physics
                    die.vy += gravity;
                    die.vx *= friction;
                    die.x += die.vx;
                    die.y += die.vy;
                    die.angle += die.vAngle;

                    // Floor bounce
                    if (die.y + radius > height - 40) {
                        die.y = height - 40 - radius;
                        die.vy = -die.vy * restitution;
                        die.vAngle += die.vx * 0.03;
                    }
                    // Ceiling bounce
                    if (die.y - radius < 40) {
                        die.y = 40 + radius;
                        die.vy = -die.vy * restitution;
                    }
                    // Left Wall
                    if (die.x - radius < 30) {
                        die.x = 30 + radius;
                        die.vx = -die.vx * restitution;
                        die.vAngle -= die.vy * 0.02;
                    }
                    // Right Wall
                    if (die.x + radius > width - 30) {
                        die.x = width - 30 - radius;
                        die.vx = -die.vx * restitution;
                        die.vAngle += die.vy * 0.02;
                    }

                    // Spin random numbers
                    if (Math.random() < 0.2) {
                        die.value = Math.floor(Math.random() * 20) + 1;
                    }
                } else {
                    // Decelerate & Align Upright
                    const t = (elapsed - (rollDuration - 300)) / 300;
                    die.vx *= 0.8;
                    die.vy *= 0.8;
                    die.vAngle *= 0.8;
                    die.angle = die.angle * (1 - t);
                    die.value = finalValue;
                }

                if (elapsed >= rollDuration) {
                    stage = 'settled';
                    settleTime = now;
                    die.value = finalValue;
                    die.angle = 0;

                    if (isCrit20) spawnConfetti();
                    if (isCrit1) generateCracks(die.x, die.y);

                    if (onComplete) onComplete(finalValue);
                }
            } else if (stage === 'settled') {
                const settledElapsed = now - settleTime;

                // Nat 1 Crack Propagation
                if (isCrit1 && crackLines.length > 0) {
                    crackProgress = Math.min(crackProgress + 0.05, 1);
                    ctx.save();
                    ctx.strokeStyle = 'rgba(239, 68, 68, 0.9)';
                    ctx.lineWidth = 2;
                    ctx.shadowColor = 'rgba(239, 68, 68, 0.6)';
                    ctx.shadowBlur = 6;
                    crackLines.forEach(line => {
                        if (crackProgress >= line.t) {
                            ctx.beginPath();
                            ctx.moveTo(line.x1, line.y1);
                            ctx.lineTo(line.x2, line.y2);
                            ctx.stroke();
                        }
                    });
                    ctx.restore();
                }

                // Nat 20 Confetti Physics
                if (isCrit20 && confetti.length > 0) {
                    confetti.forEach(c => {
                        c.vy += 0.35;
                        c.x += c.vx;
                        c.y += c.vy;
                        c.rot += c.vRot;

                        ctx.save();
                        ctx.translate(c.x, c.y);
                        ctx.rotate(c.rot);
                        ctx.fillStyle = c.color;
                        ctx.fillRect(-c.size / 2, -c.size / 2, c.size, c.size * 0.6);
                        ctx.restore();
                    });
                }

                // Draw Banner for Crits
                if (isCrit20 || isCrit1) {
                    ctx.save();
                    ctx.font = `bold ${Math.round(size * 0.35)}px 'Cinzel Decorative', 'MedievalSharp', serif`;
                    ctx.textAlign = 'center';
                    ctx.fillStyle = isCrit20 ? '#fef08a' : '#f87171';
                    ctx.shadowColor = isCrit20 ? 'rgba(212, 175, 55, 0.8)' : 'rgba(239, 68, 68, 0.8)';
                    ctx.shadowBlur = 15;
                    ctx.fillText(isCrit20 ? '🌟 NATURAL 20! CRITICAL SUCCESS! 🌟' : '💀 NATURAL 1! CRITICAL FAILURE! 💀', width / 2, die.y - radius - 30);
                    ctx.restore();
                }

                // Smoothly finish after 2.2 seconds
                if (settledElapsed > 2200) {
                    canvas.style.opacity = '0';
                    setTimeout(() => {
                        isRolling = false;
                        cancelAnimationFrame(animId);
                        ctx.clearRect(0, 0, width, height);
                    }, 400);
                    return;
                }
            }

            // Draw the D20
            drawD20(ctx, die.x, die.y, die.size, die.angle, die.value, isCrit20, isCrit1);

            animId = requestAnimationFrame(loop);
        }

        loop();
    };
})();
