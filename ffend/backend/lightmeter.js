// LightMeter Analysis Module

// Element references - initialized after DOM is loaded
let imageUpload, imagePreview, analyzeBtn, currentLocationEl, resultArea;

let uploadedImageFile = null;
let userLocation = {
    lat: null,
    lon: null,
    name: 'Unknown',
    detected: false
};

// Initialize DOM elements after page load
function initializeElements() {
    imageUpload = document.getElementById('imageUpload');
    imagePreview = document.getElementById('imagePreview');
    analyzeBtn = document.getElementById('analyzeBtn');
    currentLocationEl = document.getElementById('currentLocation');
    resultArea = document.getElementById('resultArea');
    
    // Check if critical elements exist
    if (!imageUpload || !analyzeBtn || !currentLocationEl) {
        console.error('[ERROR] Critical HTML elements not found. Check lightmeter.html');
        return false;
    }
    
    return true;
}

// Function to get location by IP address (fallback)
function getLocationByIP(controller = null) {
    console.log('[DEBUG] Starting IP Geolocation Fetch');
    
    const timeoutSeconds = 5; // 5 second timeout for IP geolocation
    const abortController = controller || new AbortController();
    const timeoutId = setTimeout(() => {
        console.warn('[WARN] IP geolocation timeout - aborting');
        abortController.abort();
    }, timeoutSeconds * 1000);
    
    if (currentLocationEl) {
        currentLocationEl.textContent = '📍 Detecting location...';
    }
    
    return fetch('http://127.0.0.1:5000/get-location-by-ip', { signal: abortController.signal })
        .then(response => {
            clearTimeout(timeoutId);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return response.json();
        })
        .then(data => {
            console.log('[DEBUG] IP API response data received');
            
            if (data.lat && data.lon) {
                userLocation.lat = data.lat;
                userLocation.lon = data.lon;
                userLocation.name = data.location || `${data.city || 'Unknown'}, ${data.country || 'Unknown'}`;
                userLocation.detected = true;
                
                if (currentLocationEl) {
                    currentLocationEl.textContent = `📍 ${userLocation.name}`;
                }
                console.log(`[DEBUG] ✓ IP Location Set: ${userLocation.name}`);
                return true;
            } else {
                throw new Error('Missing coordinates in response');
            }
        })
        .catch(error => {
            clearTimeout(timeoutId);
            console.warn('[WARN] IP geolocation failed:', error.message);
            // Default location fallback
            userLocation.lat = 40.7128;
            userLocation.lon = -74.0060;
            userLocation.name = 'Default Location (New York)';
            if (currentLocationEl) {
                currentLocationEl.textContent = `📍 ${userLocation.name}`;
            }
            return false;
        });
}

// Initialize LightMeter - CALLABLE for both standalone page and modal
function initializeLightmeter() {
    console.log('[DEBUG] Initializing LightMeter');
    
    // Initialize DOM elements
    if (!initializeElements()) {
        console.error('[ERROR] Failed to initialize elements');
        return false;
    }
    
    // Attach event listeners (check for duplicates first)
    if (imageUpload._lightmeterInitialized) {
        console.log('[DEBUG] LightMeter already initialized');
        return true;
    }
    
    imageUpload._lightmeterInitialized = true;
    
    // Image upload handler
    imageUpload.addEventListener('change', function(event) {
        const file = event.target.files[0];
        if (!file) return;
        uploadedImageFile = file;
        const reader = new FileReader();
        reader.onload = function(e) {
            imagePreview.src = e.target.result;
            imagePreview.style.display = 'block';
            console.log('[DEBUG] Image selected');
        };
        reader.readAsDataURL(file);
    });
    
    // Analyze button handler
    analyzeBtn.addEventListener('click', analyzeLightmeterImage);
    
    // Start location detection (non-blocking, with timeout)
    startLocationDetectionWithTimeout();
    
    console.log('[DEBUG] LightMeter initialized');
    return true;
}

// Location detection with built-in timeout
async function startLocationDetectionWithTimeout() {
    try {
        await Promise.race([
            startLocationDetection(),
            new Promise((_, reject) => setTimeout(() => reject('Location detection timeout'), 8000))
        ]);
    } catch (error) {
        console.log('[DEBUG] Location detection timed out or failed, using default');
        if (!userLocation.detected) {
            userLocation.lat = 40.7128;
            userLocation.lon = -74.0060;
            userLocation.name = 'Default (New York)';
            userLocation.detected = true;
            if (currentLocationEl) {
                currentLocationEl.textContent = `📍 ${userLocation.name}`;
            }
        }
    }
}

// Separate analysis function for better organization
function analyzeLightmeterImage() {
    console.log('[DEBUG] Analyze button clicked');
    
    if (!uploadedImageFile) {
        alert('Please upload an image first.');
        return;
    }
    
    // If location not detected yet, use default
    if (!userLocation.lat || !userLocation.lon) {
        console.warn('[WARN] Location not ready, using default');
        userLocation.lat = 40.7128;
        userLocation.lon = -74.0060;
        userLocation.name = 'Default Location';
    }
    
    console.log(`[DEBUG] Starting analysis: location=${userLocation.name}, lat=${userLocation.lat}, lon=${userLocation.lon}`);
    
    // Create FormData to send image and coordinates
    const formData = new FormData();
    formData.append('image', uploadedImageFile);
    formData.append('lat', userLocation.lat);
    formData.append('lon', userLocation.lon);
    formData.append('location', userLocation.name);
    
    analyzeBtn.disabled = true;
    analyzeBtn.textContent = 'Analyzing plant and light...';
    console.log('[DEBUG] Sending analysis request to backend');
    
    // Create abort controller for timeout management
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60000); // 60 second timeout
    
    // Send to backend for analysis
    fetch('http://127.0.0.1:5000/analyze', {
        method: 'POST',
        body: formData,
        signal: controller.signal
    })
    .then(response => {
        clearTimeout(timeoutId);
        console.log('[DEBUG] Analysis response status:', response.status);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
    })
    .then(data => {
        console.log('[DEBUG] Analysis data received and parsed');
        
        if (data.error) {
            alert('Error: ' + data.error);
            analyzeBtn.disabled = false;
            analyzeBtn.textContent = 'Analyze Light';
            return;
        }
        
        displayLightmeterResults(data);
        
        analyzeBtn.disabled = false;
        analyzeBtn.textContent = 'Analyze Light';
        console.log('[DEBUG] Analysis complete and displayed');
    })
    .catch(error => {
        clearTimeout(timeoutId);
        console.error('[ERROR] Analysis failed:', error.message);
        alert('Error analyzing image: ' + error.message);
        analyzeBtn.disabled = false;
        analyzeBtn.textContent = 'Analyze Light';
    });
}

// Display results from analysis
function displayLightmeterResults(data) {
    console.log('[DEBUG] Displaying results:', data);
    
    // Display basic results
    const resultLocationEl = document.getElementById('resultLocation');
    if (resultLocationEl) {
        resultLocationEl.textContent = data.location || userLocation.name;
    }
    
    // Display detected plant name prominently at top
    if (data.plant_name) {
        const plantDisplayName = data.plant_name.charAt(0).toUpperCase() + data.plant_name.slice(1);
        const detectedPlantEl = document.getElementById('detectedPlantName');
        if (detectedPlantEl) {
            // Show plant name with source of identification
            let displayText = plantDisplayName;
            if (data.plant_auto_detected) {
                displayText += ` <span style="font-size: 0.9em; color: #666;">Auto-Detected</span>`;
            }
            detectedPlantEl.innerHTML = displayText;
        }
        
        // Display scientific name if available
        if (data.scientific_name) {
            const scientificEl = document.getElementById('scientificName');
            if (scientificEl) {
                scientificEl.textContent = `(${data.scientific_name})`;
                scientificEl.style.fontStyle = 'italic';
                scientificEl.style.color = '#666';
                scientificEl.style.fontSize = '0.9em';
            } else {
                // Create element if it doesn't exist
                const newEl = document.createElement('p');
                newEl.id = 'scientificName';
                newEl.textContent = `Scientific name: ${data.scientific_name}`;
                newEl.style.fontStyle = 'italic';
                newEl.style.color = '#666';
                newEl.style.fontSize = '0.9em';
                detectedPlantEl.parentElement.appendChild(newEl);
            }
        }
        
        // Display identification method
        const methodEl = document.getElementById('identificationMethod');
        if (methodEl) {
            if (data.api_used) {
                methodEl.innerHTML = '✓ Identified via Plant.ID AI';
                methodEl.style.color = '#28a745';
            } else {
                methodEl.innerHTML = '✓ Identified via Local Analysis';
                methodEl.style.color = '#ffc107';
            }
        }
        
        console.log(`[DEBUG] ✓ Plant displayed: ${plantDisplayName}`);
    }
    
    // Display light data source (very important - shows if Gemini was used)
    if (data.light_data_source) {
        const sourceEl = document.getElementById('lightDataSource') || document.createElement('p');
        sourceEl.id = 'lightDataSource';
        
        if (data.light_data_source === 'gemini_ai') {
            sourceEl.innerHTML = '<strong>Light Requirements:</strong> AI-powered (via Gemini)';
            sourceEl.style.color = '#1976D2';
            sourceEl.style.fontWeight = 'bold';
            sourceEl.style.padding = '8px';
            sourceEl.style.backgroundColor = '#E3F2FD';
            sourceEl.style.borderRadius = '4px';
            sourceEl.style.marginBottom = '10px';
            console.log('[DEBUG] ✓ Using Gemini AI for light requirements');
        } else {
            sourceEl.innerHTML = '<strong>Light Requirements:</strong> Database (fallback)';
            sourceEl.style.color = '#FF9800';
        }
        
        if (!document.getElementById('lightDataSource')) {
            const resultAreaEl = document.getElementById('resultArea');
            if (resultAreaEl) {
                resultAreaEl.parentElement.insertBefore(sourceEl, resultAreaEl);
            }
        }
    }
    
    // Display Gemini reasoning if available
    if (data.light_analysis_reasoning) {
        const reasoningEl = document.getElementById('lightReasoning') || document.createElement('p');
        reasoningEl.id = 'lightReasoning';
        reasoningEl.innerHTML = `<em>Analysis: ${data.light_analysis_reasoning}</em>`;
        reasoningEl.style.color = '#666';
        reasoningEl.style.fontSize = '0.9em';
        reasoningEl.style.padding = '8px';
        reasoningEl.style.backgroundColor = '#F5F5F5';
        reasoningEl.style.borderRadius = '4px';
        reasoningEl.style.marginBottom = '10px';
        
        if (!document.getElementById('lightReasoning')) {
            const resultAreaEl = document.getElementById('resultArea');
            if (resultAreaEl) {
                resultAreaEl.parentElement.insertBefore(reasoningEl, resultAreaEl);
            }
        }
    }
    
    const grayscaleEl = document.getElementById('grayscaleValue');
    if (grayscaleEl) grayscaleEl.textContent = data.average_grayscale.toFixed(2);
    
    const detectedLightEl = document.getElementById('detectedLight');
    if (detectedLightEl) detectedLightEl.textContent = data.detected_light;
    
    const weatherIntensityEl = document.getElementById('weatherIntensity');
    if (weatherIntensityEl) weatherIntensityEl.textContent = data.weather_intensity;
    
    const weatherConditionEl = document.getElementById('weatherCondition');
    if (weatherConditionEl) weatherConditionEl.textContent = data.weather_description || 'Weather data unavailable';
    
    const temperatureEl = document.getElementById('temperature');
    if (temperatureEl) temperatureEl.textContent = data.temperature || 'N/A';
    
    const humidityEl = document.getElementById('humidity');
    if (humidityEl) humidityEl.textContent = data.humidity || 'N/A';
    
    console.log('[DEBUG] Results displayed');
    
    // Display plant-specific comparison if available
    const plantComparisonBox = document.getElementById('plantComparisonBox');
    if (data.plant_comparison && plantComparisonBox) {
        const comp = data.plant_comparison;
        const autoDetected = data.plant_auto_detected ? '🔍 Auto-detected: ' : '🌿 ';
        const plantNameDisplay = document.getElementById('plantNameDisplay');
        if (plantNameDisplay) plantNameDisplay.textContent = `${autoDetected}${data.plant_name.toUpperCase()}`;
        
        const currentGrayscaleEl = document.getElementById('currentGrayscale');
        if (currentGrayscaleEl) currentGrayscaleEl.textContent = comp.current.toFixed(1);
        
        const idealGrayscaleEl = document.getElementById('idealGrayscale');
        if (idealGrayscaleEl) idealGrayscaleEl.textContent = comp.range;
        
        // Set status color and message
        const matchEl = document.getElementById('plantMatch');
        if (matchEl) {
            matchEl.textContent = `${comp.status} - ${comp.advice}`;
            
            if (comp.status.includes('Perfect')) {
                matchEl.style.backgroundColor = '#d4edda';
                matchEl.style.color = '#155724';
            } else if (comp.status.includes('Too Dark')) {
                matchEl.style.backgroundColor = '#f8d7da';
                matchEl.style.color = '#721c24';
            } else {
                matchEl.style.backgroundColor = '#f8d7da';
                matchEl.style.color = '#721c24';
            }
        }
        
        plantComparisonBox.style.display = 'block';
        console.log(`[DEBUG] Plant${data.plant_auto_detected ? ' (auto-detected)' : ''} comparison displayed:`, data.plant_comparison);
    } else if (plantComparisonBox) {
        plantComparisonBox.style.display = 'none';
    }
    
    // Display warning only if there's an actual warning (not for ideal conditions)
    const warningBox = document.getElementById('warningBox');
    if (data.has_warning && warningBox) {
        const warningText = document.getElementById('warningText');
        if (warningText) warningText.textContent = data.warning;
        warningBox.style.display = 'block';
    } else if (warningBox) {
        warningBox.style.display = 'none';
    }
    
    // Display suggestions
    const suggestionsList = document.getElementById('suggestionsList');
    if (suggestionsList) {
        suggestionsList.innerHTML = '';
        data.suggestions.forEach(suggestion => {
            const li = document.createElement('li');
            li.textContent = suggestion;
            suggestionsList.appendChild(li);
        });
        const suggestionsBox = document.getElementById('suggestionsBox');
        if (suggestionsBox) suggestionsBox.style.display = 'block';
    }
    
    // Display smart suggestions
    const smartSuggestionsList = document.getElementById('smartSuggestionsList');
    if (smartSuggestionsList && data.smart_suggestions) {
        smartSuggestionsList.innerHTML = '';
        data.smart_suggestions.forEach(suggestion => {
            const li = document.createElement('li');
            li.textContent = suggestion;
            smartSuggestionsList.appendChild(li);
        });
        const smartSuggestionsBox = document.getElementById('smartSuggestionsBox');
        if (smartSuggestionsBox) smartSuggestionsBox.style.display = 'block';
    }
    
    if (resultArea) resultArea.style.display = 'block';
    console.log('[DEBUG] ====== Analysis Complete ======');
}

// Initialize on page load (for standalone lightmeter.html)
if (document.readyState !== 'loading') {
    // DOM already loaded
    initializeLightmeter();
} else {
    // DOM still loading
    document.addEventListener('DOMContentLoaded', initializeLightmeter);
}

// Start location detection (called during initialization)
async function startLocationDetection() {
    console.log('[DEBUG] Starting Location Detection');
    
    if (!currentLocationEl) {
        console.error('[ERROR] currentLocationEl not found');
        return;
    }
    
    // Show detecting message immediately
    currentLocationEl.textContent = '📍 Detecting location...';
    
    // Default location (fallback if everything fails)
    const setDefaultLocation = () => {
        if (!userLocation.detected) {
            userLocation.lat = 40.7128;
            userLocation.lon = -74.0060;
            userLocation.name = 'Default (New York)';
            userLocation.detected = true;
            if (currentLocationEl) {
                currentLocationEl.textContent = `📍 ${userLocation.name}`;
            }
            console.log('[DEBUG] Using default location');
        }
    };
    
    // TRY 1: Browser geolocation first (if it succeeds quickly)
    if ('geolocation' in navigator) {
        console.log('[DEBUG] Trying browser geolocation (2s timeout)');
        
        await new Promise((resolve) => {
            const timeoutId = setTimeout(() => {
                console.log('[DEBUG] Browser geolocation timeout, moving to IP');
                resolve(false);
            }, 2000);
            
            navigator.geolocation.getCurrentPosition(
                function(position) {
                    clearTimeout(timeoutId);
                    if (userLocation.detected) return; // Already got location
                    
                    userLocation.lat = position.coords.latitude;
                    userLocation.lon = position.coords.longitude;
                    userLocation.detected = true;
                    userLocation.name = `GPS: ${userLocation.lat.toFixed(4)}, ${userLocation.lon.toFixed(4)}`;
                    console.log('[DEBUG] ✓ Browser geolocation success');
                    
                    if (currentLocationEl) {
                        currentLocationEl.textContent = `📍 ${userLocation.name}`;
                    }
                    
                    // Try to get location name (non-blocking, no timeout needed)
                    fetch(`http://127.0.0.1:5000/get-weather-by-coords?lat=${userLocation.lat}&lon=${userLocation.lon}`)
                        .then(response => response.json())
                        .then(data => {
                            if (data.location) {
                                userLocation.name = data.location;
                                if (currentLocationEl) {
                                    currentLocationEl.textContent = `📍 ${userLocation.name}`;
                                }
                                console.log(`[DEBUG] ✓ Location name: ${userLocation.name}`);
                            }
                        })
                        .catch(err => console.log('[DEBUG] Location name skipped'));
                    
                    resolve(true);
                },
                function(error) {
                    clearTimeout(timeoutId);
                    console.log('[DEBUG] Browser geolocation denied/failed, moving to IP');
                    resolve(false);
                },
                {
                    enableHighAccuracy: false,
                    timeout: 2000,
                    maximumAge: 300000
                }
            );
        });
    }
    
    // TRY 2: If browser geolocation failed, use IP geolocation
    if (!userLocation.detected) {
        console.log('[DEBUG] Trying IP geolocation (5s timeout)');
        await getLocationByIP();
    }
    
    // TRY 3: If still no location, use default
    if (!userLocation.detected) {
        setDefaultLocation();
    }
    
    console.log(`[DEBUG] ✓ Location detection complete: ${userLocation.name}`);
}
