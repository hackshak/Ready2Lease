document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('assessmentForm');
    if (!form) return;

    const formSteps = document.querySelectorAll('.form-step');
    const progress = document.getElementById('progress');
    const stepLabel = document.querySelector('.progress-step-label');
    const percentLabel = document.querySelector('.progress-percent-label');

    let currentStep = 0;

    // ========== Multi‑Step Navigation ==========
    function updateFormSteps() {
        formSteps.forEach((step, index) => {
            step.classList.toggle('form-step-active', index === currentStep);
        });
        const progressPercent = ((currentStep + 1) / formSteps.length) * 100;
        if (progress) progress.style.width = progressPercent + '%';
        if (stepLabel) stepLabel.textContent = `Step ${currentStep + 1} / ${formSteps.length}`;
        if (percentLabel) percentLabel.textContent = `${Math.round(progressPercent)}%`;
    }

    // Validate current step before moving forward
    function isCurrentStepValid() {
        const currentForm = formSteps[currentStep];
        if (!currentForm) return false;

        // Basic HTML5 validation for visible inputs
        const inputs = currentForm.querySelectorAll('input, select, textarea');
        for (let input of inputs) {
            // Skip hidden inputs – they are validated separately if needed
            if (input.type === 'hidden') continue;
            if (!input.checkValidity()) {
                input.reportValidity();
                return false;
            }
        }

        // Custom validation for Step 1: location must be selected
        if (currentStep === 0) {
            const locationSelect = document.getElementById('locationSelect');
            const hiddenPostcode = document.getElementById('selectedPostcode');
            if (!locationSelect.value || !hiddenPostcode.value) {
                alert('Please select a valid location from the dropdown.');
                return false;
            }
        }

        return true;
    }

    document.querySelectorAll('.btn-next').forEach(btn => {
        btn.addEventListener('click', () => {
            if (isCurrentStepValid() && currentStep < formSteps.length - 1) {
                currentStep++;
                updateFormSteps();
            }
        });
    });

    document.querySelectorAll('.btn-prev').forEach(btn => {
        btn.addEventListener('click', () => {
            if (currentStep > 0) {
                currentStep--;
                updateFormSteps();
            }
        });
    });

    updateFormSteps();

    // ========== Location Autocomplete ==========
    const locationInput = document.getElementById('locationInput');
    const locationSelect = document.getElementById('locationSelect');
    const hiddenPostcode = document.getElementById('selectedPostcode');
    const hiddenCity = document.getElementById('selectedCity');
    const hiddenSuburb = document.getElementById('selectedSuburb');
    const hiddenLat = document.getElementById('selectedLat');
    const hiddenLon = document.getElementById('selectedLon');

    let debounceTimer;

    if (locationInput && locationSelect) {
        locationInput.addEventListener('input', function () {
            clearTimeout(debounceTimer);
            const query = this.value.trim();

            debounceTimer = setTimeout(() => {
                if (query.length < 2) {
                    locationSelect.innerHTML = '<option value="">Start typing...</option>';
                    return;
                }

                fetch(`/api/location-autocomplete/?q=${encodeURIComponent(query)}`, {
                    credentials: 'same-origin'
                })
                    .then(response => response.json())
                    .then(data => {
                        locationSelect.innerHTML = '<option value="">Select a location</option>';
                        if (!Array.isArray(data) || data.length === 0) {
                            const option = document.createElement('option');
                            option.text = 'No results found';
                            option.disabled = true;
                            locationSelect.appendChild(option);
                            return;
                        }

                        data.forEach(item => {
                            const option = document.createElement('option');
                            option.value = JSON.stringify(item);
                            option.text = item.label;
                            locationSelect.appendChild(option);
                        });
                    })
                    .catch(error => console.error('Autocomplete error:', error));
            }, 300);
        });

        locationSelect.addEventListener('change', function () {
            // Reset hidden fields
            hiddenPostcode.value = '';
            hiddenCity.value = '';
            hiddenSuburb.value = '';
            hiddenLat.value = '';
            hiddenLon.value = '';

            const selectedValue = this.value;
            if (!selectedValue) return;

            try {
                const selected = JSON.parse(selectedValue);
                if (hiddenPostcode) hiddenPostcode.value = selected.postcode || '';
                if (hiddenCity) hiddenCity.value = selected.city || '';
                if (hiddenSuburb) hiddenSuburb.value = selected.suburb || '';
                if (hiddenLat) hiddenLat.value = selected.lat || '';
                if (hiddenLon) hiddenLon.value = selected.lon || '';
            } catch (e) {
                console.error('Invalid location selection', e);
            }
        });
    }

    // ========== Form Submission ==========
    form.addEventListener('submit', function (e) {
        e.preventDefault();

        // Final validation before submission
        if (!isCurrentStepValid()) return;

        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) submitBtn.disabled = true;

        const formData = new FormData(form);
        const data = {};

        formData.forEach((value, key) => {
            if (key === 'documents') {
                if (!data[key]) data[key] = [];
                data[key].push(value);
            } else {
                // Convert numeric strings to numbers where appropriate
                if (key === 'moving_with_adults' || key === 'moving_with_children' || key === 'moving_with_pets') {
                    data[key] = parseInt(value, 10) || 0;
                } else {
                    data[key] = value;
                }
            }
        });

        // Remove empty strings for optional numeric fields
        ['household_income', 'individual_income', 'monthly_rent_budget'].forEach(field => {
            if (data[field] === '') delete data[field];
        });

        fetch('/api/assessment/submit/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            },
            credentials: 'same-origin',
            body: JSON.stringify(data)
        })
            .then(res => {
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                return res.json();
            })
            .then(result => {
                form.style.display = 'none';
                const resultDiv = document.getElementById('result');
                if (!resultDiv) return;

                resultDiv.style.display = 'block';
                resultDiv.innerHTML = `
                    <div style="padding: 30px; border-radius: 12px; text-align: center;">
                        <h2 style="font-size: 28px; margin-bottom: 15px;">
                            Readiness Score: ${result.readiness_score ?? 0}%
                        </h2>
                        <p style="font-size: 18px; margin-bottom: 10px;">
                            <strong>Risk Level:</strong>
                            <span style="color:${getRiskColor(result.risk_level)}">
                                ${result.risk_level ?? 'N/A'}
                            </span>
                        </p>
                        <div style="text-align:left; margin-top:20px;">
                            <h3 style="color:#198754;">Strengths:</h3>
                            <ul>
                                ${(result.strengths || []).map(s => `<li>${escapeHtml(s)}</li>`).join('')}
                            </ul>
                            <h3 style="color:#dc3545; margin-top:15px;">Weaknesses:</h3>
                            <ul>
                                ${(result.weaknesses || []).map(w => `<li>${escapeHtml(w)}</li>`).join('')}
                            </ul>
                        </div>
                        <div style="margin-top:25px;">
                            <button onclick="location.reload()" 
                                style="padding:10px 20px; background:#C92A4D; color:white; border:none; border-radius:8px; cursor:pointer;">
                                Try Again
                            </button>
                            <a href="${CHECKOUT_URL}" 
                                style="padding:10px 20px; background:#0e0e0e; color:white; border-radius:8px; text-decoration:none; margin-left:10px;">
                                Upgrade to Premium
                            </a>
                        </div>
                    </div>
                `;
            })
            .catch(error => {
                console.error('Submission error:', error);
                alert('Something went wrong. Please try again.');
            })
            .finally(() => {
                if (submitBtn) submitBtn.disabled = false;
            });
    });
});

// ========== Helper Functions ==========
function getRiskColor(risk) {
    switch (risk) {
        case 'Low': return '#198754';
        case 'Medium': return '#ffc107';
        case 'High': return '#dc3545';
        default: return '#6c757d';
    }
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>]/g, function (m) {
        if (m === '&') return '&amp;';
        if (m === '<') return '&lt;';
        if (m === '>') return '&gt;';
        return m;
    });
}