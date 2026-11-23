/* ==========================================================================
   FITCAMPUS AI - CLIENT-SIDE INTERACTION AND CHARTS
   ========================================================================== */

document.addEventListener('DOMContentLoaded', function() {
    
    // --- 1. PROFILE SETUP WIZARD ---
    const wizardForm = document.getElementById('profile-wizard-form');
    if (wizardForm) {
        const steps = Array.from(document.querySelectorAll('.step-content'));
        const stepIndicators = Array.from(document.querySelectorAll('.wizard-step'));
        const btnPrev = document.getElementById('btn-prev');
        const btnNext = document.getElementById('btn-next');
        const btnSubmit = document.getElementById('btn-submit');
        let currentStep = 0;

        function updateWizard() {
            steps.forEach((step, idx) => {
                if (idx === currentStep) {
                    step.classList.add('active');
                } else {
                    step.classList.remove('active');
                }
            });

            stepIndicators.forEach((indicator, idx) => {
                indicator.classList.remove('active', 'completed');
                if (idx === currentStep) {
                    indicator.classList.add('active');
                } else if (idx < currentStep) {
                    indicator.classList.add('completed');
                }
            });

            // Handle Navigation Buttons Visibility
            if (currentStep === 0) {
                btnPrev.style.display = 'none';
            } else {
                btnPrev.style.display = 'inline-flex';
            }

            if (currentStep === steps.length - 1) {
                btnNext.style.display = 'none';
                btnSubmit.style.display = 'inline-flex';
            } else {
                btnNext.style.display = 'inline-flex';
                btnSubmit.style.display = 'none';
            }
        }

        // Validate fields in the active step
        function validateStep() {
            const activeStepEl = steps[currentStep];
            const requiredInputs = activeStepEl.querySelectorAll('[required]');
            let isValid = true;

            requiredInputs.forEach(input => {
                if (!input.value.trim()) {
                    isValid = false;
                    input.classList.add('input-error');
                    // Remove error styling on input
                    input.addEventListener('input', function() {
                        this.classList.remove('input-error');
                    }, { once: true });
                }
            });

            return isValid;
        }

        btnNext.addEventListener('click', function() {
            if (validateStep()) {
                currentStep++;
                updateWizard();
            } else {
                showToast('Please fill out all required fields before proceeding.', 'error');
            }
        });

        btnPrev.addEventListener('click', function() {
            currentStep--;
            updateWizard();
        });

        // Initialize state
        updateWizard();
    }

    // --- 2. AJAX QUICK LOGS HANDLERS ---
    const quickLogWater = document.getElementById('btn-log-water');
    const quickLogSleep = document.getElementById('btn-log-sleep');
    const quickLogWorkout = document.getElementById('btn-log-workout');

    if (quickLogWater) {
        quickLogWater.addEventListener('click', function() {
            logMetric('/tracker/quick-log', { action: 'water', amount: 0.25 });
        });
    }

    if (quickLogSleep) {
        quickLogSleep.addEventListener('click', function() {
            logMetric('/tracker/quick-log', { action: 'sleep', amount: 1.0 });
        });
    }

    if (quickLogWorkout) {
        quickLogWorkout.addEventListener('click', function() {
            const isCompleted = this.getAttribute('data-completed') === 'true';
            logMetric('/tracker/quick-log', { action: 'workout', status: !isCompleted });
        });
    }

    function logMetric(url, data) {
        fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        })
        .then(response => response.json())
        .then(resData => {
            if (resData.success) {
                showToast(resData.message, 'success');
                updateDashboardUI(resData.data);
            } else {
                showToast(resData.message || 'Failed to save log', 'error');
            }
        })
        .catch(err => {
            console.error('Error logging metric:', err);
            showToast('Network error, please try again.', 'error');
        });
    }

    function updateDashboardUI(logData) {
        // Update text labels
        const waterVal = document.getElementById('lbl-water-val');
        if (waterVal) waterVal.innerText = logData.water_intake.toFixed(2) + ' L';

        const sleepVal = document.getElementById('lbl-sleep-val');
        if (sleepVal) sleepVal.innerText = logData.sleep_hours.toFixed(1) + ' hrs';

        const workoutVal = document.getElementById('lbl-workout-val');
        if (workoutVal) {
            workoutVal.innerText = logData.workout_completed ? 'Completed' : 'Pending';
            workoutVal.className = logData.workout_completed ? 'stat-val text-success' : 'stat-val text-muted';
        }

        const workoutBtn = document.getElementById('btn-log-workout');
        if (workoutBtn) {
            workoutBtn.setAttribute('data-completed', logData.workout_completed.toString());
            workoutBtn.innerHTML = logData.workout_completed 
                ? '<i class="fas fa-check"></i> Workout Checked' 
                : '<i class="fas fa-dumbbell"></i> Check Workout';
            if (logData.workout_completed) {
                workoutBtn.style.background = 'rgba(16, 185, 129, 0.2)';
                workoutBtn.style.borderColor = '#10b981';
            } else {
                workoutBtn.style.background = 'rgba(255, 255, 255, 0.05)';
                workoutBtn.style.borderColor = 'rgba(255,255,255,0.08)';
            }
        }

        // Update charts dynamically if they exist
        if (window.waterChartInstance) {
            window.waterChartInstance.data.datasets[0].data = [logData.water_intake, Math.max(0, 3.0 - logData.water_intake)];
            window.waterChartInstance.update();
        }
    }

    // --- 3. CHART.JS INITIALIZATION ---
    initializeCharts();

    function initializeCharts() {
        // A) Weight Progress Chart (Dashboard & Reports)
        const weightCanvas = document.getElementById('weightChart');
        if (weightCanvas) {
            const rawLabels = weightCanvas.getAttribute('data-labels') || '[]';
            const rawValues = weightCanvas.getAttribute('data-values') || '[]';
            
            try {
                const labels = JSON.parse(rawLabels);
                const values = JSON.parse(rawValues);

                const ctx = weightCanvas.getContext('2d');
                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: 'Weight (kg)',
                            data: values,
                            borderColor: '#3b82f6',
                            backgroundColor: 'rgba(59, 130, 246, 0.1)',
                            borderWidth: 3,
                            fill: true,
                            tension: 0.4,
                            pointBackgroundColor: '#ffffff',
                            pointHoverRadius: 6
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: false }
                        },
                        scales: {
                            y: {
                                grid: { color: 'rgba(255, 255, 255, 0.05)' },
                                ticks: { color: '#94a3b8' }
                            },
                            x: {
                                grid: { display: false },
                                ticks: { color: '#94a3b8' }
                            }
                        }
                    }
                });
            } catch(e) {
                console.error("Error parsing weight chart data:", e);
            }
        }

        // B) Daily Water Circular Progress Chart
        const waterCanvas = document.getElementById('waterChart');
        if (waterCanvas) {
            const currentWater = parseFloat(waterCanvas.getAttribute('data-current') || '0.0');
            const targetWater = 3.0; // 3 Liters default
            const remaining = Math.max(0, targetWater - currentWater);

            const ctx = waterCanvas.getContext('2d');
            window.waterChartInstance = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['Hydrated', 'Remaining'],
                    datasets: [{
                        data: [currentWater, remaining],
                        backgroundColor: ['#3b82f6', 'rgba(255, 255, 255, 0.05)'],
                        borderColor: ['#090d16', 'rgba(255, 255, 255, 0.02)'],
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '80%',
                    plugins: {
                        legend: { display: false },
                        tooltip: { enabled: true }
                    }
                }
            });
        }
    }

    // --- 4. TOAST NOTIFICATION UTILITY ---
    function showToast(message, type = 'success') {
        // Remove existing toast first
        const oldToast = document.querySelector('.toast-notification');
        if (oldToast) oldToast.remove();

        const toast = document.createElement('div');
        toast.className = `toast-notification toast-${type}`;
        
        let icon = '<i class="fas fa-check-circle"></i>';
        if (type === 'error') {
            icon = '<i class="fas fa-exclamation-circle"></i>';
        } else if (type === 'info') {
            icon = '<i class="fas fa-info-circle"></i>';
        }

        toast.innerHTML = `${icon} <span>${message}</span>`;
        document.body.appendChild(toast);

        // Inject Styles dynamically if not already in stylesheet
        if (!document.getElementById('toast-styles')) {
            const style = document.createElement('style');
            style.id = 'toast-styles';
            style.innerHTML = `
                .toast-notification {
                    position: fixed;
                    bottom: 30px;
                    right: 30px;
                    padding: 16px 24px;
                    border-radius: 12px;
                    background: rgba(13, 18, 30, 0.95);
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    color: #ffffff;
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                    z-index: 9999;
                    animation: toastSlideIn 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards;
                    font-weight: 500;
                }
                .toast-success { border-left: 4px solid #10b981; }
                .toast-success i { color: #10b981; }
                .toast-error { border-left: 4px solid #ef4444; }
                .toast-error i { color: #ef4444; }
                .toast-info { border-left: 4px solid #3b82f6; }
                .toast-info i { color: #3b82f6; }
                @keyframes toastSlideIn {
                    from { transform: translateY(100px) scale(0.9); opacity: 0; }
                    to { transform: translateY(0) scale(1); opacity: 1; }
                }
            `;
            document.head.appendChild(style);
        }

        // Auto remove toast
        setTimeout(() => {
            toast.style.animation = 'toastSlideIn 0.2s reverse forwards';
            setTimeout(() => toast.remove(), 200);
        }, 3500);
    }
});
