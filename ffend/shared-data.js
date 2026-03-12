// shared-data.js - Complete User Profile Management with Email-based OTP

// Automatic API base URL for dev/prod
const API_BASE =
  window.location.hostname === "localhost"
    ? "http://localhost:5000"
    : "";

// ===== EMAIL AUTHORIZATION SETTINGS =====
// Set to 'true' to allow ANY email
// Set to 'false' to only allow emails in the ALLOWED_EMAILS list
const ALLOW_ANY_EMAIL = true; // ✅ Any email can register

// Allowed emails for registration (only used if ALLOW_ANY_EMAIL is false)
const ALLOWED_EMAILS = []; // Empty - all emails allowed

// OTP Configuration
const OTP_EXPIRY_MINUTES = 10; // OTP valid for 10 minutes
const OTP_LENGTH = 6;

// Function to check if email is allowed
function isEmailAllowed(email) {
    if (ALLOW_ANY_EMAIL) {
        return true; // Allow any email
    }
    return ALLOWED_EMAILS.includes(email.toLowerCase());
}

// Generate random OTP
function generateOTP() {
    return Math.floor(Math.random() * 900000) + 100000; // 6-digit random number
}

// Send OTP to real email address via backend
async function sendOTPToEmail(email, otp) {
    try {
        const response = await fetch(`${API_BASE}/api/email/send-otp`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: email,
                otp: otp
            })
        });

        const data = await response.json();
        
        if (data.success) {
            console.log(`✅ OTP sent successfully to ${email}`);
            return true;
        } else {
            console.error(`❌ Failed to send OTP: ${data.message}`);
            return false;
        }
    } catch (error) {
        console.error('Error sending OTP email:', error);
        // Fallback to console for development
        console.log(`[FALLBACK] OTP for ${email}: ${otp}`);
        return false;
    }
}

let currentUser = null;

// Get all user profiles from localStorage
function getUserProfiles() {
    try {
        const stored = localStorage.getItem('userProfiles');
        return stored ? JSON.parse(stored) : {};
    } catch (e) {
        console.error('Error reading user profiles:', e);
        return {};
    }
}

// Save all user profiles to localStorage
function saveUserProfiles(profiles) {
    try {
        localStorage.setItem('userProfiles', JSON.stringify(profiles));
        console.log('User profiles saved successfully');
        return true;
    } catch (e) {
        console.error('Error saving user profiles:', e);
        return false;
    }
}

// Register a new user with complete profile
function registerUser(userData) {
    if (!userData || !userData.email) {
        console.error('Invalid user data - email is required');
        return null;
    }

    const profiles = getUserProfiles();
    const email = userData.email.toLowerCase();
    
    // Check if user already exists
    if (profiles[email]) {
        console.warn('User already exists, updating profile');
    }

    // Create complete user profile
    const userProfile = {
        // Contact info (use email as primary contact)
        contact: email,
        email: email,
        phone: userData.phone || '',
        name: userData.name || '',
        
        // Plant preferences
        plantCategory: userData.plantCategory || '',
        relatedPlants: Array.isArray(userData.relatedPlants) 
            ? userData.relatedPlants 
            : (userData.relatedPlants ? [userData.relatedPlants] : []),
        
        // Account metadata
        memberSince: userData.memberSince || new Date().toISOString(),
        registeredDate: userData.registeredDate || new Date().toISOString(),
        lastUpdated: new Date().toISOString(),
        
        // Additional info (for future use)
        address: userData.address || '',
        city: userData.city || '',
        state: userData.state || '',
        zipCode: userData.zipCode || ''
    };

    // Save to profiles
    profiles[email] = userProfile;
    
    // Also save by phone number if provided (for phone login)
    if (userData.phone) {
        profiles[userData.phone] = userProfile;
    }

    // Save to localStorage
    if (saveUserProfiles(profiles)) {
        console.log('User registered successfully:', userProfile);
        return userProfile;
    } else {
        console.error('Failed to save user profile');
        return null;
    }
}

// Login user and retrieve their complete profile
function loginUser(contact) {
    if (!contact) {
        console.error('No contact provided for login');
        return null;
    }

    const profiles = getUserProfiles();
    const contactKey = contact.toLowerCase();

    console.log('Attempting login for:', contactKey);
    console.log('Available profiles:', Object.keys(profiles));

    // Check if user profile exists
    if (profiles[contactKey]) {
        currentUser = profiles[contactKey];
        console.log('User found - logging in:', currentUser);
    } else {
        // User doesn't exist - this shouldn't happen after proper registration
        console.warn('No profile found for:', contactKey);
        console.log('Creating minimal profile - user should complete registration');
        
        currentUser = {
            contact: contactKey,
            email: contactKey.includes('@') ? contactKey : '',
            phone: contactKey.includes('@') ? '' : contactKey,
            memberSince: new Date().toISOString(),
            registeredDate: new Date().toISOString()
        };
        
        // Don't save this minimal profile, user needs to complete registration
    }

    // Save current session
    try {
        localStorage.setItem('currentUser', JSON.stringify(currentUser));
        console.log('Login successful, session saved');
        return currentUser;
    } catch (e) {
        console.error('Error saving login session:', e);
        return null;
    }
}

// Get currently logged-in user
function getCurrentUser() {
    if (!currentUser) {
        try {
            const stored = localStorage.getItem('currentUser');
            if (stored) {
                currentUser = JSON.parse(stored);
                console.log('Retrieved current user from storage:', currentUser);
            }
        } catch (e) {
            console.error('Error retrieving current user:', e);
        }
    }
    return currentUser;
}

// Update user profile
function updateUserProfile(updates) {
    const user = getCurrentUser();
    
    if (!user || !user.contact) {
        console.error('No user logged in - cannot update profile');
        return null;
    }

    const profiles = getUserProfiles();
    const contact = user.contact;

    if (!profiles[contact]) {
        console.error('User profile not found in storage');
        return null;
    }

    // Merge updates with existing profile
    profiles[contact] = {
        ...profiles[contact],
        ...updates,
        lastUpdated: new Date().toISOString()
    };

    // Update phone reference if phone changed
    if (updates.phone && updates.phone !== user.phone) {
        // Remove old phone reference
        if (user.phone) {
            delete profiles[user.phone];
        }
        // Add new phone reference
        profiles[updates.phone] = profiles[contact];
    }

    currentUser = profiles[contact];

    // Save everything
    saveUserProfiles(profiles);
    localStorage.setItem('currentUser', JSON.stringify(currentUser));

    console.log('Profile updated successfully:', currentUser);
    return currentUser;
}

// Save profile data from a form
function saveProfileData(formData) {
    const user = getCurrentUser();
    
    if (!user) {
        console.error('No user logged in');
        return false;
    }

    const updates = {
        name: formData.name || user.name || '',
        phone: formData.phone || user.phone || '',
        email: formData.email || user.email || '',
        plantCategory: formData.plantCategory || user.plantCategory || '',
        relatedPlants: formData.relatedPlants || user.relatedPlants || [],
        address: formData.address || user.address || '',
        city: formData.city || user.city || '',
        state: formData.state || user.state || '',
        zipCode: formData.zipCode || user.zipCode || ''
    };

    return updateUserProfile(updates) !== null;
}

// Check if user is logged in (use on protected pages)
function requireLogin() {
    const user = getCurrentUser();
    if (!user) {
        console.log('No user logged in, redirecting to login');
        window.location.href = 'l1.html';
        return false;
    }
    return true;
}

// ===== OTP MANAGEMENT FUNCTIONS =====

// Get all OTP records from localStorage
function getOTPRecords() {
    try {
        const stored = localStorage.getItem('otpRecords');
        return stored ? JSON.parse(stored) : {};
    } catch (e) {
        console.error('Error reading OTP records:', e);
        return {};
    }
}

// Save OTP records to localStorage
function saveOTPRecords(records) {
    try {
        localStorage.setItem('otpRecords', JSON.stringify(records));
        return true;
    } catch (e) {
        console.error('Error saving OTP records:', e);
        return false;
    }
}

// Generate and send OTP to user's registered email
function generateAndSendOTP(email) {
    const emailLower = email.toLowerCase();
    const profiles = getUserProfiles();
    
    // Check if user exists
    if (!profiles[emailLower]) {
        console.error('User not found:', emailLower);
        return { success: false, message: 'User not registered with this email' };
    }
    
    const userProfile = profiles[emailLower];
    const otp = generateOTP().toString();
    const expiryTime = Date.now() + (OTP_EXPIRY_MINUTES * 60 * 1000);
    
    // Store OTP with expiry
    const otpRecords = getOTPRecords();
    otpRecords[emailLower] = {
        otp: otp,
        expiryTime: expiryTime,
        attempts: 0,
        createdAt: new Date().toISOString()
    };
    
    saveOTPRecords(otpRecords);
    
    // Send OTP to the user's registered email
    sendOTPToEmail(userProfile.email, otp);
    
    return { 
        success: true, 
        message: `OTP sent to ${userProfile.email}`,
        email: userProfile.email,
        expiryMinutes: OTP_EXPIRY_MINUTES
    };
}

// Verify OTP for a given email
function verifyOTP(email, otp) {
    const emailLower = email.toLowerCase();
    const otpRecords = getOTPRecords();
    
    if (!otpRecords[emailLower]) {
        return { success: false, message: 'No OTP found. Request a new OTP.' };
    }
    
    const record = otpRecords[emailLower];
    
    // Check if OTP has expired
    if (Date.now() > record.expiryTime) {
        delete otpRecords[emailLower];
        saveOTPRecords(otpRecords);
        return { success: false, message: 'OTP has expired. Request a new OTP.' };
    }
    
    // Check if OTP matches
    if (record.otp !== otp.toString()) {
        record.attempts += 1;
        if (record.attempts >= 5) {
            delete otpRecords[emailLower];
            saveOTPRecords(otpRecords);
            return { success: false, message: 'Too many incorrect attempts. Please request a new OTP.' };
        }
        saveOTPRecords(otpRecords);
        return { success: false, message: `Incorrect OTP. ${5 - record.attempts} attempts remaining.` };
    }
    
    // OTP verified successfully
    delete otpRecords[emailLower];
    saveOTPRecords(otpRecords);
    
    // Login the user
    const profiles = getUserProfiles();
    const userProfile = profiles[emailLower];
    currentUser = userProfile;
    localStorage.setItem('currentUser', JSON.stringify(currentUser));
    
    return { success: true, message: 'OTP verified! Logging in...', user: userProfile };
}

// Get user email by phone number (for login)
function getEmailByPhone(phone) {
    const profiles = getUserProfiles();
    if (profiles[phone]) {
        return profiles[phone].email;
    }
    return null;
}

// Logout user
function logoutUser() {
    console.log('Logging out user');
    currentUser = null;
    localStorage.removeItem('currentUser');
    window.location.href = 'l1.html';
}

// ===== GARDEN MANAGEMENT FUNCTIONS =====

// Get all plants in user's garden
function getUserGardenPlants(email) {
    try {
        const allGardens = localStorage.getItem('userGardens');
        if (!allGardens) return [];
        
        const gardens = JSON.parse(allGardens);
        return gardens[email.toLowerCase()] || [];
    } catch (e) {
        console.error('Error reading user garden:', e);
        return [];
    }
}

// Add plant to user's garden
function addPlantToGarden(email, plantData) {
    try {
        const allGardens = JSON.parse(localStorage.getItem('userGardens') || '{}');
        const emailLower = email.toLowerCase();
        
        if (!allGardens[emailLower]) {
            allGardens[emailLower] = [];
        }
        
        console.log('=== ADD PLANT TO GARDEN ===');
        console.log('Plant data received:', plantData);
        console.log('Water field:', plantData.water);
        console.log('Best watering field:', plantData.best_watering);
        
        // Determine watering schedule - prioritize water field from API
        const wateringSchedule = plantData.water || plantData.best_watering || 'Regular watering';
        console.log('Final watering schedule:', wateringSchedule);
        
        // Create garden entry with all plant details
        // Handle both API format and hardcoded format
        const gardenPlant = {
            plantId: 'PLANT-' + Date.now(),
            name: plantData.name || 'Unknown Plant',
            scientific_name: plantData.scientific_name || plantData.scientific || '',
            description: plantData.description || '',
            water: plantData.water || '',
            best_soil: plantData.best_soil || plantData.soil || '',
            best_light: plantData.best_light || plantData.climate || '',
            toxicity: plantData.toxicity || '',
            purposes: plantData.purposes || [],
            cultural_significance: plantData.cultural_significance || '',
            image_url: plantData.image_url || '',
            medical: plantData.medical || '',
            taxonomy: plantData.taxonomy || {},
            common_names: plantData.common_names || [],
            suitability: plantData.suitability || '',
            toxicityInfo: plantData.toxicityInfo || '',
            confidence: plantData.confidence || 0,
            addedAt: new Date().toISOString(),
            // Set watering schedule from plant data
            watering_schedule: wateringSchedule,
            location: 'Not set',
            health_status: 'Healthy',
            notes: ''
        };
        
        console.log('Garden plant object:', gardenPlant);
        console.log('Watering schedule in garden plant:', gardenPlant.watering_schedule);
        
        allGardens[emailLower].push(gardenPlant);
        localStorage.setItem('userGardens', JSON.stringify(allGardens));
        
        console.log('Plant added to garden:', gardenPlant);
        console.log('=== ADD PLANT COMPLETE ===');
        return gardenPlant;
    } catch (e) {
        console.error('Error adding plant to garden:', e);
        return null;
    }
}

// Remove plant from garden
function removeFromGarden(email, plantId) {
    try {
        const allGardens = JSON.parse(localStorage.getItem('userGardens') || '{}');
        const emailLower = email.toLowerCase();
        
        if (allGardens[emailLower]) {
            allGardens[emailLower] = allGardens[emailLower].filter(plant => plant.plantId !== plantId);
            localStorage.setItem('userGardens', JSON.stringify(allGardens));
            console.log('Plant removed from garden:', plantId);
            return true;
        }
        return false;
    } catch (e) {
        console.error('Error removing plant from garden:', e);
        return false;
    }
}

// Update plant details in garden
function updateGardenPlant(email, plantId, updates) {
    try {
        const allGardens = JSON.parse(localStorage.getItem('userGardens') || '{}');
        const emailLower = email.toLowerCase();
        
        if (allGardens[emailLower]) {
            const plantIndex = allGardens[emailLower].findIndex(p => p.plantId === plantId);
            if (plantIndex !== -1) {
                allGardens[emailLower][plantIndex] = {
                    ...allGardens[emailLower][plantIndex],
                    ...updates,
                    updatedAt: new Date().toISOString()
                };
                localStorage.setItem('userGardens', JSON.stringify(allGardens));
                console.log('Garden plant updated:', plantId);
                return allGardens[emailLower][plantIndex];
            }
        }
        return null;
    } catch (e) {
        console.error('Error updating garden plant:', e);
        return null;
    }
}

// Check if plant already in garden
function isPlantInGarden(email, plantName) {
    try {
        if (!email || !plantName) {
            console.warn('isPlantInGarden: Missing email or plantName');
            return false;
        }
        const plants = getUserGardenPlants(email);
        const exists = plants.some(p => p.name && p.name.toLowerCase() === plantName.toLowerCase());
        console.log(`Checking if "${plantName}" in garden for ${email}:`, exists);
        return exists;
    } catch (e) {
        console.error('Error checking plant in garden:', e);
        return false;
    }
}

// ===== ORDER MANAGEMENT FUNCTIONS =====

// Get all orders for a specific user
function getUserOrders(email) {
    try {
        const allOrders = localStorage.getItem('userOrders');
        if (!allOrders) return [];
        
        const orders = JSON.parse(allOrders);
        return orders[email.toLowerCase()] || [];
    } catch (e) {
        console.error('Error reading user orders:', e);
        return [];
    }
}

// Add new order for user
function addUserOrder(email, orderData) {
    try {
        const allOrders = JSON.parse(localStorage.getItem('userOrders') || '{}');
        const emailLower = email.toLowerCase();
        
        if (!allOrders[emailLower]) {
            allOrders[emailLower] = [];
        }
        
        const order = {
            orderId: 'ORD-' + Date.now(),
            ...orderData,
            createdAt: new Date().toISOString()
        };
        
        allOrders[emailLower].push(order);
        localStorage.setItem('userOrders', JSON.stringify(allOrders));
        
        console.log('Order added:', order);
        return order;
    } catch (e) {
        console.error('Error adding order:', e);
        return null;
    }
}

// Get all orders from localStorage
function getAllOrders() {
    try {
        const stored = localStorage.getItem('userOrders');
        return stored ? JSON.parse(stored) : {};
    } catch (e) {
        console.error('Error reading all orders:', e);
        return {};
    }
}

// Delete an order
function deleteUserOrder(email, orderId) {
    try {
        const allOrders = JSON.parse(localStorage.getItem('userOrders') || '{}');
        const emailLower = email.toLowerCase();
        
        if (allOrders[emailLower]) {
            allOrders[emailLower] = allOrders[emailLower].filter(order => order.orderId !== orderId);
            localStorage.setItem('userOrders', JSON.stringify(allOrders));
            console.log('Order deleted:', orderId);
            return true;
        }
        return false;
    } catch (e) {
        console.error('Error deleting order:', e);
        return false;
    }
}

// Debug function - check storage
function debugStorage() {
    console.log('=== DEBUG STORAGE ===');
    console.log('Current User:', getCurrentUser());
    console.log('All User Profiles:', getUserProfiles());
    console.log('All User Gardens:', localStorage.getItem('userGardens'));
    console.log('All User Orders:', getAllOrders());
    console.log('LocalStorage currentUser:', localStorage.getItem('currentUser'));
    console.log('LocalStorage userProfiles:', localStorage.getItem('userProfiles'));
    console.log('LocalStorage userGardens:', localStorage.getItem('userGardens'));
    console.log('LocalStorage userOrders:', localStorage.getItem('userOrders'));
}

// Clear all data (for testing/reset)
function clearAllData() {
    if (confirm('Are you sure you want to clear all user data? This cannot be undone.')) {
        localStorage.clear();
        currentUser = null;
        console.log('All data cleared');
        alert('All data has been cleared');
        window.location.reload();
    }
}

// Initialize - check if there's a current session
console.log('Shared-data.js loaded');
console.log('Allowed emails:', ALLOWED_EMAILS);

// Test function - add test plant to garden (for debugging)
function testAddPlant() {
    console.log('=== TEST ADD PLANT START ===');
    
    const user = getCurrentUser();
    console.log('Current user:', user);
    
    if (!user) {
        console.error('ERROR: No user logged in for test');
        alert('Please login first to test adding a plant');
        return;
    }
    
    if (!user.email) {
        console.error('ERROR: User has no email:', user);
        return;
    }
    
    const testPlant = {
        name: 'Test Rose',
        scientific: 'Rosa spp',
        water: 'Water daily',
        soil: 'Well-drained soil',
        climate: 'Full sun',
        purposes: ['Decorative'],
        toxicity: 'safe',
        toxicityInfo: 'Non-toxic'
    };
    
    console.log('Test plant to add:', testPlant);
    console.log('Adding to email:', user.email);
    
    const result = addPlantToGarden(user.email, testPlant);
    console.log('addPlantToGarden returned:', result);
    
    // Verify it was added
    const plants = getUserGardenPlants(user.email);
    console.log('Garden plants after add:', plants);
    console.log('Total plants in garden:', plants ? plants.length : 0);
    
    // Check localStorage directly
    const rawGardens = localStorage.getItem('userGardens');
    console.log('Raw localStorage userGardens:', rawGardens);
    
    if (result) {
        alert(`✅ Test plant "${result.name}" added successfully!\n\nCheck browser console for details.`);
    } else {
        alert('❌ Failed to add test plant. Check browser console.');
    }
    
    console.log('=== TEST ADD PLANT END ===');
}