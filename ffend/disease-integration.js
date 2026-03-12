/**
 * Disease Detection Integration
 * Updated disease.html to use Flask backend
 */

// Update the detectDisease function in disease.html
async function detectDisease() {
    const fileInput = document.querySelector('input[type="file"]');
    const file = fileInput.files[0];
    const errorDiv = document.querySelector('.alert') || createErrorDiv();
    const btnText = document.querySelector('button[onclick="detectDisease()"]');

    // Reset error
    if (errorDiv) errorDiv.style.display = 'none';

    // Validate file
    if (!file) {
        showError('Please select an image first!', errorDiv);
        return;
    }

    // Check file type
    if (!file.type.startsWith('image/')) {
        showError('Please upload a valid image file!', errorDiv);
        return;
    }

    // Check file size (limit to 10MB)
    if (file.size > 10 * 1024 * 1024) {
        showError('Image file is too large. Please use an image under 10MB.', errorDiv);
        return;
    }

    // Show loading state
    const originalText = btnText.textContent;
    btnText.textContent = 'Analyzing...';
    btnText.disabled = true;

    try {
        // Call Flask backend API
        const response = await greensphereAPI.detectDiseaseFromFile(file);

        // Hide loading state
        btnText.textContent = originalText;
        btnText.disabled = false;

        // Display results
        if (response.success) {
            if (response.data.isHealthy) {
                showHealthyPlant(response.data);
            } else {
                showDetectedDisease(response.data);
            }
            fileInput.value = ''; // Clear file input
        } else {
            showError(response.message || 'Failed to analyze plant. Please try again.', errorDiv);
        }

    } catch (error) {
        console.error('Disease detection error:', error);
        btnText.textContent = originalText;
        btnText.disabled = false;
        showError(`Failed to analyze plant: ${error.message}`, errorDiv);
    }
}

function showHealthyPlant(plantData) {
    document.getElementById('diseaseTitle').textContent = '✅ Healthy Plant';
    document.getElementById('diseaseSubtitle').textContent = 'Your plant looks healthy!';

    const content = `
        <div class="p-4">
            <div class="alert alert-success mb-4" role="alert">
                <strong>Good News!</strong> No diseases detected in your plant.
            </div>
            <div class="section-box">
                <p class="text-muted">Keep up with regular plant care to maintain its health:</p>
                <ul class="mb-0">
                    <li>Water appropriately for your plant species</li>
                    <li>Ensure adequate light exposure</li>
                    <li>Monitor for any pest infestations</li>
                    <li>Remove dead leaves and debris</li>
                    <li>Maintain good air circulation</li>
                </ul>
            </div>
        </div>
    `;

    document.getElementById('diseaseContent').innerHTML = content;

    const myModal = new bootstrap.Modal(document.getElementById('diseaseModal'));
    myModal.show();
}

function showDetectedDisease(diseaseData) {
    document.getElementById('diseaseTitle').textContent = diseaseData.title;
    document.getElementById('diseaseSubtitle').textContent = diseaseData.description;

    const severityClass = diseaseData.severity === 'Very High' ? 'severity-very-high' :
        diseaseData.severity === 'High' ? 'severity-high' : 'severity-moderate';

    const content = `
        <div class="p-4">
            <div class="mb-4">
                <span class="badge-severity ${severityClass}">Severity: ${diseaseData.severity}</span>
                <small style="margin-left: 10px; color: #666;">Confidence: ${diseaseData.probability}%</small>
            </div>

            <div class="section-box">
                <h5 class="text-danger fw-bold mb-3">🦠 Causes</h5>
                <ul class="mb-0">
                    ${(diseaseData.causes || []).map(c => `<li>${c}</li>`).join('')}
                </ul>
            </div>

            <div class="section-box">
                <h5 class="text-warning-emphasis fw-bold mb-3">⚠️ Symptoms</h5>
                <ul class="mb-0">
                    ${(diseaseData.symptoms || []).map(s => `<li>${s}</li>`).join('')}
                </ul>
            </div>

            <div class="section-box">
                <h5 class="text-success fw-bold mb-3">🏠 Home Remedies</h5>
                <ul class="mb-0">
                    ${(diseaseData.homeRemedies || []).map(r => `<li>${r}</li>`).join('')}
                </ul>
            </div>

            <div class="section-box">
                <h5 class="text-primary fw-bold mb-3">🌱 Fertilizer</h5>
                <ul class="mb-0">
                    ${(diseaseData.fertilizer || []).map(f => `<li>${f}</li>`).join('')}
                </ul>
            </div>

            <div class="section-box">
                <h5 class="text-secondary fw-bold mb-3">🧪 Recommended Pesticide</h5>
                <ul class="mb-0">
                    ${(diseaseData.pesticide || []).map(p => `<li>${p}</li>`).join('')}
                </ul>
            </div>

            <div class="section-box">
                <h5 class="text-info fw-bold mb-3">🛡️ Prevention Tips</h5>
                <ul class="mb-0">
                    ${(diseaseData.prevention || []).map(p => `<li>${p}</li>`).join('')}
                </ul>
            </div>
        </div>
    `;

    document.getElementById('diseaseContent').innerHTML = content;

    const myModal = new bootstrap.Modal(document.getElementById('diseaseModal'));
    myModal.show();
}

function showError(message, errorDiv) {
    if (errorDiv) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
    } else {
        alert(message);
    }
}

function createErrorDiv() {
    const div = document.createElement('div');
    div.className = 'alert alert-danger mt-3';
    div.style.display = 'none';
    document.querySelector('.upload-box').appendChild(div);
    return div;
}
