document.addEventListener('DOMContentLoaded', () => {
    
    // --- Slider Value Updates ---
    const sliders = [
        { id: 'study_hours_per_week', suffix: ' hrs' },
        { id: 'sleep_hours_per_night', suffix: ' hrs' },
        { id: 'extracurricular_hours_per_week', suffix: ' hrs' },
        { id: 'attendance_percentage', suffix: '%' },
        { id: 'midterm_score', suffix: '' },
        { id: 'stress_level', suffix: '' }
    ];

    sliders.forEach(sliderConfig => {
        const input = document.getElementById(sliderConfig.id);
        const display = input.nextElementSibling;
        
        input.addEventListener('input', (e) => {
            display.textContent = e.target.value + sliderConfig.suffix;
        });
    });

    // --- Global State ---
    let currentSchedule = [];
    let currentMetrics = {};
    let currentUser = null;
    let isLoginMode = true;

    // --- Authentication Logic ---
    const authModal = document.getElementById('auth-modal');
    const btnShowLogin = document.getElementById('btn-show-login');
    const closeModal = document.querySelector('.close-modal');
    const btnSubmitAuth = document.getElementById('btn-submit-auth');
    const authUsernameInput = document.getElementById('auth-username');
    const authPasswordInput = document.getElementById('auth-password');
    const authTitle = document.getElementById('auth-title');
    const btnToggleAuth = document.getElementById('btn-toggle-auth');
    const authToggleText = document.getElementById('auth-toggle-text');
    const authError = document.getElementById('auth-error');

    // Boot check
    fetch('/api/status').then(r=>r.json()).then(d => {
        if(d.logged_in) {
            currentUser = d.username;
            btnShowLogin.textContent = 'Log Out';
        }
    });

    btnShowLogin.addEventListener('click', async () => {
        if(currentUser) {
            await fetch('/api/logout', { method: 'POST' });
            currentUser = null;
            btnShowLogin.textContent = 'Log In';
            alert("Logged out successfully.");
        } else {
            authModal.classList.remove('hidden');
        }
    });

    closeModal.addEventListener('click', () => authModal.classList.add('hidden'));

    btnToggleAuth.addEventListener('click', () => {
        isLoginMode = !isLoginMode;
        authTitle.textContent = isLoginMode ? 'Log In' : 'Register';
        btnSubmitAuth.textContent = isLoginMode ? 'Log In' : 'Sign Up';
        btnToggleAuth.textContent = isLoginMode ? 'Register' : 'Log In';
        authToggleText.firstChild.textContent = isLoginMode ? "Don't have an account? " : "Already have an account? ";
    });

    btnSubmitAuth.addEventListener('click', async () => {
        const u = authUsernameInput.value.trim();
        const p = authPasswordInput.value.trim();
        if(!u || !p) { 
            authError.textContent = "Fields required."; 
            authError.classList.remove('hidden'); 
            return; 
        }
        
        try {
            const endpoint = isLoginMode ? '/api/login' : '/api/register';
            const res = await fetch(endpoint, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username: u, password: p})
            });
            const data = await res.json();
            if(!res.ok) throw new Error(data.error);

            if(isLoginMode) {
                currentUser = data.username;
                btnShowLogin.textContent = 'Log Out';
                authModal.classList.add('hidden');
                
                // Try Load plan
                const loadRes = await fetch('/api/load');
                if(loadRes.ok) {
                    const savedData = await loadRes.json();
                    currentSchedule = savedData.weekly_schedule;
                    currentMetrics = savedData.metrics;

                    // Update UI Sliders
                    sliders.forEach(sc => {
                        const ins = document.getElementById(sc.id);
                        if(currentMetrics[sc.id] !== undefined) {
                            ins.value = currentMetrics[sc.id];
                            ins.nextElementSibling.textContent = ins.value + sc.suffix;
                        }
                    });

                    // Trigger render
                    document.getElementById('chat-fab').classList.remove('hidden');
                    renderResult(savedData);
                    renderScheduleToDOM(currentSchedule);
                }
            } else {
                authError.textContent = "Registered! You can now log in.";
                authError.style.color = "var(--success)";
                authError.classList.remove('hidden');
            }
        } catch(e) {
            authError.textContent = e.message;
            authError.style.color = "var(--danger)";
            authError.classList.remove('hidden');
        }
    });

    function renderScheduleToDOM(scheduleArray) {
        const container = document.getElementById('schedule-container');
        if (!container) return; // Not rendered yet

        let html = `
            <div class="weekly-schedule">
                <h3 class="schedule-title">
                    <i class="fa-regular fa-calendar-days"></i> Your Detailed Daily Schedule
                </h3>
                <div class="schedule-grid">
        `;

        scheduleArray.forEach(dayPlan => {
             html += `
                 <div class="schedule-day">
                     <div class="day-name">
                        <span class="day-title">${dayPlan.day}</span>
                        <span class="day-focus">${dayPlan.focus}</span>
                     </div>
                     <div class="day-details">
                         <div class="time-slot">
                            <div class="slot-label"><i class="fa-solid fa-sun" style="color: #fbbf24;"></i> Morning</div>
                            <div class="slot-desc">${dayPlan.morning || dayPlan.activity}</div>
                         </div>
                         <div class="time-slot">
                            <div class="slot-label"><i class="fa-solid fa-cloud-sun" style="color: #f97316;"></i> Afternoon</div>
                            <div class="slot-desc">${dayPlan.afternoon || ""}</div>
                         </div>
                         <div class="time-slot">
                            <div class="slot-label"><i class="fa-solid fa-moon" style="color: #60a5fa;"></i> Evening</div>
                            <div class="slot-desc">${dayPlan.evening || ""}</div>
                         </div>
                     </div>
                 </div>
             `;
        });

        html += `
                </div>
            </div>
        `;
        container.innerHTML = html;
    }

    // --- Form Submission ---
    const form = document.getElementById('prediction-form');
    const resultDisplay = document.getElementById('result-display');
    const predictBtn = document.getElementById('predict-btn');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        // 1. Gather data
        const formData = new FormData(form);
        const payload = {
            study_hours_per_week: parseInt(formData.get('study_hours_per_week')),
            sleep_hours_per_night: parseInt(formData.get('sleep_hours_per_night')),
            extracurricular_hours_per_week: parseInt(formData.get('extracurricular_hours_per_week')),
            attendance_percentage: parseInt(formData.get('attendance_percentage')),
            midterm_score: parseInt(formData.get('midterm_score')),
            stress_level: parseInt(formData.get('stress_level'))
        };

        // 2. Show loading state
        predictBtn.disabled = true;
        predictBtn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Analyzing...';
        
        resultDisplay.innerHTML = `
            <div class="spinner"></div>
            <p style="margin-top: 1rem; color: var(--text-secondary);">Running inference model...</p>
        `;

        try {
            // 3. Send request to Flask API
            const response = await fetch('/api/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                throw new Error(`Server error: ${response.status}`);
            }

            const data = await response.json();
            
            if (data.error) throw new Error(data.error);

            // Save globally
            currentSchedule = data.weekly_schedule;
            currentMetrics = data.metrics;

            // Show Chat FAB
            document.getElementById('chat-fab').classList.remove('hidden');

            setTimeout(() => { // small delay for visual effect
                renderResult(data);
                renderScheduleToDOM(currentSchedule);
                predictBtn.disabled = false;
                predictBtn.innerHTML = '<i class="fa-solid fa-microchip"></i> Analyze Risk';
            }, 800);

        } catch (error) {
            console.error(error);
            // Error Handling UI omitted for brevity...
        }
    });

    function renderResult(data) {
        const isBurnout = data.burnout_predicted === 1;
        const prob = (data.burnout_probability * 100).toFixed(1);
        const riskClass = isBurnout ? 'high' : 'low';
        const riskText = isBurnout ? 'High Risk of Burnout' : 'Low Risk of Burnout';
        const colorVar = isBurnout ? 'var(--danger)' : 'var(--success)';
        const rotation = -45 + (180 * (data.burnout_probability));

        let insightMsg = isBurnout 
            ? "Your current patterns indicate burnout risk." : "Your lifestyle appears balanced.";

        let potentialColor = "var(--success)";
        if (data.academic_potential < 50) potentialColor = "var(--danger)";
        else if (data.academic_potential < 75) potentialColor = "var(--warning)";

        let academicPotentialHTML = `
            <div class="academic-potential">
                <h3>Academic Success Potential</h3>
                <div class="potential-bar-container">
                    <div class="potential-bar-fill" style="width: ${data.academic_potential}%; background-color: ${potentialColor};"></div>
                </div>
                <p class="potential-score">${data.academic_potential}/100 Score</p>
            </div>
        `;

        let actionPlanHTML = `<div class="action-plan"><div class="action-grid">`;
        data.action_plan.forEach(item => {
            const extraClass = item.positive ? 'positive-action' : '';
            actionPlanHTML += `
                <div class="action-card ${extraClass}">
                    <div class="action-icon"><i class="fa-solid ${item.icon}"></i></div>
                    <div class="action-content">
                        <h4>${item.title}</h4><p>${item.desc}</p>
                    </div>
                </div>`;
        });
        actionPlanHTML += `</div></div>`;

        resultDisplay.innerHTML = `
            <div class="result-card">
                <div class="risk-level ${riskClass}">${riskText}</div>
                <div class="gauge-container">
                    <div class="gauge-bg"></div>
                    <div class="gauge-fill" style="border-color: ${colorVar}; transform: rotate(${rotation}deg);"></div>
                    <div class="gauge-percent">${prob}%</div>
                </div>
                <p class="insight-text">${insightMsg}</p>
                ${academicPotentialHTML}
                ${actionPlanHTML}
                <div class="export-panel">
                    <button id="btn-save-plan" class="btn btn-secondary"><i class="fa-solid fa-cloud-arrow-up"></i> Save Profile</button>
                    <button id="btn-export-pdf" class="btn btn-primary"><i class="fa-solid fa-file-pdf"></i> Export PDF</button>
                </div>
                <div id="schedule-container"></div>
            </div>
        `;

        // Bind Export & Save Actions
        document.getElementById('btn-export-pdf').addEventListener('click', () => {
            const el = document.getElementById('schedule-container');
            const opt = {
                margin: 0.5,
                filename: 'My_AI_Schedule.pdf',
                image: { type: 'jpeg', quality: 0.98 },
                html2canvas: { scale: 2 },
                jsPDF: { unit: 'in', format: 'letter', orientation: 'portrait' }
            };
            html2pdf().set(opt).from(el).save();
        });

        document.getElementById('btn-save-plan').addEventListener('click', async () => {
            if(!currentUser) {
                alert("Please log in first to save your plan!");
                return;
            }
            try {
                await fetch('/api/save', {
                    method:'POST', 
                    headers:{'Content-Type':'application/json'},
                    body: JSON.stringify({metrics: currentMetrics, schedule: currentSchedule})
                });
                alert("Plan successfully saved to your profile!");
            } catch(e) {
                alert("Error saving plan.");
            }
        });
    }

    // --- Chat Logic ---
    const chatFab = document.getElementById('chat-fab');
    const chatWindow = document.getElementById('chat-window');
    const closeChatBtn = document.getElementById('close-chat');
    const sendChatBtn = document.getElementById('send-chat');
    const chatInput = document.getElementById('chat-input');
    const chatMessages = document.getElementById('chat-messages');

    chatFab.addEventListener('click', () => chatWindow.classList.remove('hidden'));
    closeChatBtn.addEventListener('click', () => chatWindow.classList.add('hidden'));

    async function sendChatMessage() {
        const msg = chatInput.value.trim();
        if (!msg) return;

        // User bubble
        chatMessages.innerHTML += `<div class="chat-bubble user-bubble">${msg}</div>`;
        chatInput.value = '';
        chatMessages.scrollTop = chatMessages.scrollHeight;

        try {
            const resp = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    message: msg, 
                    schedule: currentSchedule,
                    metrics: currentMetrics 
                })
            });
            const chatData = await resp.json();
            
            // AI bubble
            chatMessages.innerHTML += `<div class="chat-bubble ai-bubble">${chatData.response || "Done."}</div>`;
            chatMessages.scrollTop = chatMessages.scrollHeight;

            if (chatData.metrics) {
                currentMetrics = chatData.metrics;
                
                // Magically Slide the UI elements
                sliders.forEach(sliderConfig => {
                    const input = document.getElementById(sliderConfig.id);
                    const display = input.nextElementSibling;
                    if(currentMetrics[sliderConfig.id] !== undefined) {
                        input.value = currentMetrics[sliderConfig.id];
                        display.textContent = input.value + sliderConfig.suffix;
                    }
                });
            }
            
            // Always completely re-render the Risk and Action Plan heuristics
            if(chatData.burnout_probability !== undefined) {
                renderResult(chatData);
            }

            if (chatData.schedule) {
                currentSchedule = chatData.schedule;
                // Ensure schedule is drawn into the new container created by renderResult
                renderScheduleToDOM(currentSchedule);
            }
        } catch(e) {
            chatMessages.innerHTML += `<div class="chat-bubble ai-bubble" style="color:var(--danger);">Error reaching AI Planner.</div>`;
        }
    }

    sendChatBtn.addEventListener('click', sendChatMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendChatMessage();
    });
});
