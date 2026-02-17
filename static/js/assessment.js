

document.addEventListener('DOMContentLoaded', function() {

    const form = document.getElementById('assessmentForm');
    const formSteps = document.querySelectorAll('.form-step');
    const progress = document.getElementById('progress');
    let currentStep = 0;

    // Labels above progress bar
    const stepLabel = document.querySelector('.progress-step-label');
    const percentLabel = document.querySelector('.progress-percent-label');

    const updateFormSteps = () => {
        // Show active step
        formSteps.forEach((step, index) => {
            step.classList.toggle('form-step-active', index === currentStep);
        });

        // Update progress width
        const progressPercent = ((currentStep + 1) / formSteps.length) * 100;
        progress.style.width = progressPercent + '%';

        // Update labels
        if (stepLabel) stepLabel.textContent = `Step ${currentStep + 1} / ${formSteps.length}`;
        if (percentLabel) percentLabel.textContent = `${Math.round(progressPercent)}%`;
    };

    // Next buttons with validation
document.querySelectorAll('.btn-next').forEach(btn => {
    btn.addEventListener('click', () => {
        const currentForm = formSteps[currentStep];
        const inputs = currentForm.querySelectorAll('input, select, textarea');
        let valid = true;

        // Check standard required fields
        inputs.forEach(input => {
            if (!input.checkValidity()) {
                input.reportValidity(); // show browser native validation
                valid = false;
            }
        });

        // // Check required checkbox groups
        // const checkboxGroups = {};
        // currentForm.querySelectorAll('input[type="checkbox"][required]').forEach(cb => {
        //     if (!checkboxGroups[cb.name]) checkboxGroups[cb.name] = [];
        //     if (cb.checked) checkboxGroups[cb.name].push(cb.value);
        // });

        // currentForm.querySelectorAll('input[type="checkbox"][required]').forEach(cb => {
        //     const groupChecked = checkboxGroups[cb.name] && checkboxGroups[cb.name].length > 0;
        //     if (!groupChecked) {
        //         alert('Please select at least one option for ' + cb.name);
        //         valid = false;
        //     }
        // });

        // Only move to next step if all validations pass
        if (valid && currentStep < formSteps.length - 1) {
            currentStep++;
            updateFormSteps();
        }
    });
});


    updateFormSteps();

    // Postcode AJAX suburb suggestion
    const locationInput = document.getElementById('locationInput');
    const locationSelect = document.getElementById('locationSelect');

    const hiddenPostcode = document.getElementById('selectedPostcode');
    const hiddenCity = document.getElementById('selectedCity');
    const hiddenLat = document.getElementById('selectedLat');
    const hiddenLon = document.getElementById('selectedLon');

    let debounceTimer;

    locationInput.addEventListener('input', function () {
        clearTimeout(debounceTimer);

        const query = this.value.trim();

        debounceTimer = setTimeout(() => {
            if (query.length < 2) {
                locationSelect.innerHTML = '';
                return;
            }

            fetch(`/api/location-autocomplete/?q=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    locationSelect.innerHTML = '';

                    if (data.length === 0) {
                        const option = document.createElement('option');
                        option.text = "No results found";
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
                .catch(error => {
                    console.error("Autocomplete error:", error);
                });

        }, 300);
    });

    locationSelect.addEventListener('change', function () {
        const selected = JSON.parse(this.value);

        hiddenPostcode.value = selected.postcode;
        hiddenCity.value = selected.city;
        hiddenLat.value = selected.lat;
        hiddenLon.value = selected.lon;
    });





// Form submit
form.addEventListener('submit', function(e) {
    e.preventDefault();
    const formData = new FormData(form);
    const data = {};
    formData.forEach((value, key) => {
        if (key === 'documents') {
            if (!data[key]) data[key] = [];
            data[key].push(value);
        } else {
            data[key] = value;
        }
    });

    fetch('/api/assessment/submit/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data),
    })
    .then(res => res.json())
    .then(result => {
        form.style.display = 'none';
        const resultDiv = document.getElementById('result');
        resultDiv.style.display = 'block';
        resultDiv.innerHTML = `
            <div style="padding: 30px; border-radius: 12px; text-align: center;">
                <h2 style="font-size: 28px; color: black; margin-bottom: 15px;">Readiness Score: ${result.readiness_score}</h2>
                <p style="font-size: 18px; margin-bottom: 10px;"><strong>Risk Level:</strong> <span style="color:${getRiskColor(result.risk_level)}">${result.risk_level}</span></p>
                <div style="text-align:left; margin-top:20px;">
                    <h3 style="font-size:20px; color:#198754; margin-bottom:8px;">Strengths:</h3>
                    <ul style="list-style: disc; padding-left: 20px; color:#198754;">
                        ${result.strengths.map(s => `<li>${s}</li>`).join('')}
                    </ul>
                    <h3 style="font-size:20px; color:#dc3545; margin-bottom:8px; margin-top:15px;">Weaknesses:</h3>
                    <ul style="list-style: disc; padding-left: 20px; color:#dc3545;">
                        ${result.weaknesses.map(w => `<li>${w}</li>`).join('')}
                    </ul>
                </div>
                <div style="margin-top:25px; display:flex; justify-content:center; gap:15px; flex-wrap:wrap;">
                    <button onclick="location.reload()" style="padding:10px 20px; background:#C92A4D; color:white; border:none; border-radius:8px; cursor:pointer; font-size:16px;">Try Again</button>
                    <a href="/pricing/" style="padding:10px 20px; background:#0e0e0e; color:white; border:none; border-radius:8px; cursor:pointer; font-size:16px; text-decoration:none; display:flex; align-items:center; justify-content:center;">Upgrade to Premium</a>
                </div>
            </div>
        `;
    });

    // Helper function to color risk level
    function getRiskColor(risk) {
        switch(risk) {
            case 'Low': return '#198754';  // green
            case 'Medium': return '#ffc107'; // yellow
            case 'High': return '#dc3545';  // red
            default: return '#6c757d';      // gray
        }
    }
});

});

// CSRF helper
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

