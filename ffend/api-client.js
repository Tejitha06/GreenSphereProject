// Automatically set API base URL for dev/prod
const API_BASE =
  window.location.hostname === "localhost"
    ? "http://localhost:5000/api"
    : "/api";

/**
 * GreenSphere API Client
 * Handles all API communication for plant identification and disease detection
 */

class GreenSphereAPI {
    constructor(baseURL = API_BASE) {
        this.baseURL = baseURL;
        this.timeout = 30000; // 30 seconds
    }

    /**
     * Identify a plant from an image file
     * @param {File} imageFile - The image file to identify
     * @returns {Promise<Object>} Plant identification result
     */
    async identifyPlantFromFile(imageFile) {
        try {
            const formData = new FormData();
            formData.append('image', imageFile);

            const response = await fetch(`${this.baseURL}/plants/identify`, {
                method: 'POST',
                body: formData,
                headers: {
                    // Don't set Content-Type header, let browser set it with boundary
                }
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || `HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Plant identification error:', error);
            throw error;
        }
    }

    /**
     * Identify a plant from a base64-encoded image
     * @param {string} base64Image - The base64-encoded image data
     * @param {string} filename - The filename of the image
     * @returns {Promise<Object>} Plant identification result
     */
    async identifyPlantFromBase64(base64Image, filename = 'plant.jpg') {
        try {
            const payload = {
                image: base64Image,
                filename: filename
            };

            const response = await fetch(`${this.baseURL}/plants/identify/base64`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || `HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Plant identification error:', error);
            throw error;
        }
    }

    /**
     * Detect disease in a plant from an image file
     * @param {File} imageFile - The image file to analyze
     * @returns {Promise<Object>} Disease detection result
     */
    async detectDiseaseFromFile(imageFile) {
        try {
            const formData = new FormData();
            formData.append('image', imageFile);

            const response = await fetch(`${this.baseURL}/diseases/detect`, {
                method: 'POST',
                body: formData,
                headers: {
                    // Don't set Content-Type header, let browser set it with boundary
                }
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || `HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Disease detection error:', error);
            throw error;
        }
    }

    /**
     * Detect disease in a plant from a base64-encoded image
     * @param {string} base64Image - The base64-encoded image data
     * @param {string} filename - The filename of the image
     * @returns {Promise<Object>} Disease detection result
     */
    async detectDiseaseFromBase64(base64Image, filename = 'plant.jpg') {
        try {
            const payload = {
                image: base64Image,
                filename: filename
            };

            const response = await fetch(`${this.baseURL}/diseases/detect/base64`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || `HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Disease detection error:', error);
            throw error;
        }
    }

    /**
     * Get health status of the API
     * @returns {Promise<Object>} Health status
     */
    async getHealth() {
        try {
            const response = await fetch(`${this.baseURL}/health`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Health check error:', error);
            throw error;
        }
    }

    /**
     * Get list of common plants
     * @returns {Promise<Object>} List of common plants
     */
    async getCommonPlants() {
        try {
            const response = await fetch(`${this.baseURL}/plants/common`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Get common plants error:', error);
            throw error;
        }
    }

    /**
     * Get list of common diseases
     * @returns {Promise<Object>} List of common diseases
     */
    async getCommonDiseases() {
        try {
            const response = await fetch(`${this.baseURL}/diseases/common`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Get common diseases error:', error);
            throw error;
        }
    }
}

// Create global instance
const greensphereAPI = new GreenSphereAPI();
