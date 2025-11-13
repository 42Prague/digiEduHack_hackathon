// Region and school dropdown management

import { loadRegions, loadSchools } from './storage.js'

let regions = []
let schools = []

/**
 * Initialize dropdowns with current data
 */
export function initializeDropdowns() {
    regions = loadRegions()
    schools = loadSchools()
    populateRegions()
    populateSchools()
    setupRegionFilter()
}

/**
 * Refresh dropdowns with latest data from storage
 */
export function refreshDropdowns() {
    regions = loadRegions()
    schools = loadSchools()
    const currentRegion = document.getElementById('region')?.value || ''
    populateRegions()
    if (currentRegion) {
        document.getElementById('region').value = currentRegion
    }
    populateSchools(currentRegion || null)
}

/**
 * Get current regions data
 * @returns {Array} Current regions array
 */
export function getRegions() {
    return regions
}

/**
 * Get current schools data
 * @returns {Array} Current schools array
 */
export function getSchools() {
    return schools
}

/**
 * Populate region dropdown
 */
function populateRegions() {
    const regionSelect = document.getElementById('region')
    if (!regionSelect) return

    regionSelect.innerHTML = '<option value="">Select a region</option>'

    regions.forEach(region => {
        const option = document.createElement('option')
        option.value = region.id
        option.textContent = region.name
        regionSelect.appendChild(option)
    })
}

/**
 * Populate school dropdown, optionally filtered by region
 * @param {string|null} regionId - Region ID to filter by, or null for all schools
 */
function populateSchools(regionId = null) {
    const schoolSelect = document.getElementById('school')
    if (!schoolSelect) return

    const currentSchoolId = schoolSelect.value // Preserve current selection if possible
    schoolSelect.innerHTML = '<option value="">Select a school</option>'

    const filteredSchools = regionId
        ? schools.filter(s => s.regionId === regionId)
        : schools

    filteredSchools.forEach(school => {
        const option = document.createElement('option')
        option.value = school.id
        option.textContent = school.name
        schoolSelect.appendChild(option)
    })

    // Restore selection if it's still valid
    if (currentSchoolId && filteredSchools.some(s => s.id === currentSchoolId)) {
        schoolSelect.value = currentSchoolId
    }
}

/**
 * Setup event listeners for region and school filtering
 */
function setupRegionFilter() {
    const regionSelect = document.getElementById('region')
    const schoolSelect = document.getElementById('school')

    if (!regionSelect || !schoolSelect) return

    // When region changes, filter schools
    regionSelect.addEventListener('change', (e) => {
        const selectedRegionId = e.target.value

        if (selectedRegionId) {
            // Filter schools by region
            populateSchools(selectedRegionId)

            // If current school is not in the selected region, clear it
            const currentSchoolId = schoolSelect.value
            if (currentSchoolId) {
                const currentSchool = schools.find(s => s.id === currentSchoolId)
                if (currentSchool && currentSchool.regionId !== selectedRegionId) {
                    schoolSelect.value = ''
                }
            }
        } else {
            // Show all schools if no region selected
            populateSchools(null)
        }

        // Update upload button state
        if (window.updateUploadButtonState) {
            setTimeout(() => window.updateUploadButtonState(), 100)
        }
    })

    // When school changes, automatically set the region
    schoolSelect.addEventListener('change', (e) => {
        const selectedSchoolId = e.target.value

        if (selectedSchoolId) {
            // Find the school and its region
            const selectedSchool = schools.find(s => s.id === selectedSchoolId)

            if (selectedSchool && selectedSchool.regionId) {
                // Set the region dropdown to match the school's region
                regionSelect.value = selectedSchool.regionId

                // Filter schools to show only schools in that region
                populateSchools(selectedSchool.regionId)

                // Restore the school selection
                schoolSelect.value = selectedSchoolId
            }
        } else {
            // If school is cleared, show all schools (but keep region if selected)
            const currentRegionId = regionSelect.value
            populateSchools(currentRegionId || null)
        }

        // Update upload button state when school changes
        if (window.updateUploadButtonState) {
            setTimeout(() => window.updateUploadButtonState(), 100)
        }
    })
}

/**
 * Get selected school ID
 * @returns {string} Selected school ID or empty string
 */
export function getSelectedSchoolId() {
    const schoolSelect = document.getElementById('school')
    return schoolSelect?.value || ''
}

/**
 * Get selected region ID
 * @returns {string} Selected region ID or empty string
 */
export function getSelectedRegionId() {
    const regionSelect = document.getElementById('region')
    return regionSelect?.value || ''
}

/**
 * Get selected school object
 * @returns {Object|null} Selected school object or null
 */
export function getSelectedSchool() {
    const schoolId = getSelectedSchoolId()
    return schools.find(s => s.id === schoolId) || null
}

/**
 * Get selected region object
 * @returns {Object|null} Selected region object or null
 */
export function getSelectedRegion() {
    const regionId = getSelectedRegionId()
    return regions.find(r => r.id === regionId) || null
}

