// Region and school dropdown management

import { loadRegions, loadSchools } from './storage.js'

let regions = []
let schools = []
let filtersInitialized = false

async function fetchDropdownData() {
    const [regionsData, schoolsData] = await Promise.all([loadRegions(), loadSchools()])
    regions = Array.isArray(regionsData) ? regionsData : []
    schools = Array.isArray(schoolsData) ? schoolsData : []
}

/**
 * Initialize dropdowns with current data
 */
export async function initializeDropdowns() {
    await fetchDropdownData()
    populateRegions()
    populateSchools()
    if (!filtersInitialized) {
        setupRegionFilter()
        filtersInitialized = true
    }
}

/**
 * Refresh dropdowns with latest data from backend or provided payload
 */
export async function refreshDropdowns(nextData = null) {
    if (nextData) {
        regions = Array.isArray(nextData.regions) ? nextData.regions : regions
        schools = Array.isArray(nextData.schools) ? nextData.schools : schools
    } else {
        await fetchDropdownData()
    }

    const regionSelect = document.getElementById('region')
    const currentRegion = regionSelect?.value || ''

    populateRegions()
    if (regionSelect && currentRegion) {
        regionSelect.value = currentRegion
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

    regionSelect.innerHTML = '<option value="">Vyberte region</option>'

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
    schoolSelect.innerHTML = '<option value="">Vyberte školu</option>'

    const filteredSchools = regionId
        ? schools.filter(s => String(s.region_id) === String(regionId))
        : schools

    filteredSchools.forEach(school => {
        const option = document.createElement('option')
        option.value = school.id
        option.textContent = school.name
        schoolSelect.appendChild(option)
    })

    // Restore selection if it's still valid
    if (
        currentSchoolId &&
        filteredSchools.some(s => String(s.id) === String(currentSchoolId))
    ) {
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
                const currentSchool = schools.find(s => String(s.id) === String(currentSchoolId))
                if (currentSchool && String(currentSchool.region_id) !== String(selectedRegionId)) {
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
            const selectedSchool = schools.find(s => String(s.id) === String(selectedSchoolId))

            if (selectedSchool && selectedSchool.region_id) {
                // Set the region dropdown to match the school's region
                regionSelect.value = selectedSchool.region_id

                // Filter schools to show only schools in that region
                populateSchools(selectedSchool.region_id)

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
    return schools.find(s => String(s.id) === String(schoolId)) || null
}

/**
 * Get selected region object
 * @returns {Object|null} Selected region object or null
 */
export function getSelectedRegion() {
    const regionId = getSelectedRegionId()
    return regions.find(r => String(r.id) === String(regionId)) || null
}
