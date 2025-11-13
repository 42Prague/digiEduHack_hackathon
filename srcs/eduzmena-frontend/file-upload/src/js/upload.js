// Main upload page orchestrator
// This file coordinates all modules for the upload page

import { initializeDropdowns, refreshDropdowns } from './dropdowns.js'
import { watchStorageChanges } from './storage.js'
import { initializeUppy, updateUploadButtonState } from './uppy-setup.js'

// Initialize the page
async function init() {
    try {
        // Initialize dropdowns
        initializeDropdowns()

        // Watch for storage changes and refresh dropdowns when data updates
        watchStorageChanges(() => {
            refreshDropdowns()
            // Update upload button state after refresh
            setTimeout(() => updateUploadButtonState(), 100)
        })

        // Initialize Uppy
        await initializeUppy()

        // Make updateUploadButtonState available globally for dropdown changes
        window.updateUploadButtonState = updateUploadButtonState
    } catch (error) {
        console.error('Error initializing upload page:', error)
    }
}

// Start initialization when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init)
} else {
    init()
}
