// Storage management for regions and schools

import { STORAGE_KEY_REGIONS, STORAGE_KEY_SCHOOLS } from './config.js'

/**
 * Load regions from localStorage
 * @returns {Array} Array of region objects
 */
export function loadRegions() {
    return JSON.parse(localStorage.getItem(STORAGE_KEY_REGIONS) || '[]')
}

/**
 * Load schools from localStorage
 * @returns {Array} Array of school objects
 */
export function loadSchools() {
    return JSON.parse(localStorage.getItem(STORAGE_KEY_SCHOOLS) || '[]')
}

/**
 * Watch for storage changes and call callback when data changes
 * @param {Function} callback - Function to call when data changes
 */
export function watchStorageChanges(callback) {
    // Watch for storage events (cross-tab)
    window.addEventListener('storage', (e) => {
        if (e.key === STORAGE_KEY_REGIONS || e.key === STORAGE_KEY_SCHOOLS) {
            callback()
        }
    })

    // Also check for changes in the same window (same-tab)
    let lastRegions = JSON.stringify(loadRegions())
    let lastSchools = JSON.stringify(loadSchools())

    setInterval(() => {
        const currentRegions = JSON.stringify(loadRegions())
        const currentSchools = JSON.stringify(loadSchools())

        if (currentRegions !== lastRegions || currentSchools !== lastSchools) {
            lastRegions = currentRegions
            lastSchools = currentSchools
            callback()
        }
    }, 1000) // Check every second
}

