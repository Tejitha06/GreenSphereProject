/**
 * Plant Identification Integration
 * Updated identify.html to use Flask backend
 */

// Update the identifyPlant function in identify.html
async function identifyPlant() {
    const fileInput = document.getElementById('plantImageInput');
    const file = fileInput.files[0];
    const errorDiv = document.getElementById('uploadError');
    const btnText = document.getElementById('identifyBtnText');
    const btnLoading = document.getElementById('identifyBtnLoading');

    // Reset error
    errorDiv.style.display = 'none';

    // Validate file
    if (!file) {
        errorDiv.textContent = 'Please select an image first!';
        errorDiv.style.display = 'block';
        return;
    }

    // Check file type
    if (!file.type.startsWith('image/')) {
        errorDiv.textContent = 'Please upload a valid image file!';
        errorDiv.style.display = 'block';
        return;
    }

    // Check file size (limit to 10MB)
    if (file.size > 10 * 1024 * 1024) {
        errorDiv.textContent = 'Image file is too large. Please use an image under 10MB.';
        errorDiv.style.display = 'block';
        return;
    }

    // Show loading state
    btnText.style.display = 'none';
    btnLoading.style.display = 'inline-block';

    try {
        // Call Flask backend API
        const response = await greensphereAPI.identifyPlantFromFile(file);

        // Hide loading state
        btnText.style.display = 'inline-block';
        btnLoading.style.display = 'none';

        // Display results
        if (response.success && response.data) {
            showIdentifiedPlant(response.data);
            fileInput.value = ''; // Clear file input
        } else {
            errorDiv.textContent = response.message || 'Failed to identify plant. Please try again.';
            errorDiv.style.display = 'block';
        }

    } catch (error) {
        console.error('Identification error:', error);
        btnText.style.display = 'inline-block';
        btnLoading.style.display = 'none';
        errorDiv.textContent = `Failed to identify plant: ${error.message}`;
        errorDiv.style.display = 'block';
    }
}

function showIdentifiedPlant(plantData) {
    document.getElementById('plantModalTitle').textContent = plantData.name;
    document.getElementById('plantModalScientific').textContent = plantData.scientific;

    const purposeBadges = (plantData.purposes || []).map(p =>
        `<span class="purpose-badge">${p}</span>`
    ).join('');

    const toxicityClass = plantData.toxicity === 'toxic' ? 'toxicity-warning' : 'toxicity-safe';
    const toxicityIcon = plantData.toxicity === 'toxic' ? '⚠️' : '✅';

    const confidence = plantData.confidence ? `<small style="color: #4caf50; font-weight: 600;">Confidence: ${plantData.confidence}%</small>` : '';

    const modalBody = `
        <div class="info-section">
            <div class="info-label">🎯 Purpose</div>
            <div class="info-content">${purposeBadges}</div>
        </div>

        <div class="info-section">
            <div class="info-label">✨ Suitability</div>
            <div class="info-content">${plantData.suitability}</div>
        </div>

        <div class="info-section">
            <div class="info-label">🌱 Soil Guide</div>
            <div class="info-content">${plantData.soil}</div>
        </div>

        <div class="info-section">
            <div class="info-label">💧 Water Guide</div>
            <div class="info-content">${plantData.water}</div>
        </div>

        <div class="info-section">
            <div class="info-label">🌡️ Climate Preferences</div>
            <div class="info-content">${plantData.climate}</div>
        </div>

        <div class="info-section">
            <div class="info-label">${toxicityIcon} Toxicity</div>
            <div class="info-content">
                <div class="${toxicityClass}">
                    <strong>${plantData.toxicity === 'toxic' ? 'Warning: Toxic Plant' : 'Safe for Pets & Humans'}</strong><br>
                    ${plantData.toxicityInfo}
                </div>
            </div>
        </div>

        <div class="info-section">
            <div class="info-label">💊 Medical Properties</div>
            <div class="info-content">${plantData.medical}</div>
        </div>

        ${confidence ? `<div class="info-section" style="text-align: center; padding: 10px; background: #f0f0f0; border-radius: 8px;">${confidence}</div>` : ''}

        <button class="btn btn-add-garden" onclick="addToGarden('${plantData.name}')">
            🌿 Add to My Garden
        </button>
    `;

    document.getElementById('plantModalBody').innerHTML = modalBody;

    const modal = new bootstrap.Modal(document.getElementById('plantModal'));
    modal.show();
}
