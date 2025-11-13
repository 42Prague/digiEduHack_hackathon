// Data storage using localStorage
const STORAGE_KEY_REGIONS = 'admin_regions'
const STORAGE_KEY_SCHOOLS = 'admin_schools'

// Initialize data
let regions = JSON.parse(localStorage.getItem(STORAGE_KEY_REGIONS) || '[]')
let schools = JSON.parse(localStorage.getItem(STORAGE_KEY_SCHOOLS) || '[]')

// Helper functions
function saveRegions() {
    localStorage.setItem(STORAGE_KEY_REGIONS, JSON.stringify(regions))
}

function saveSchools() {
    localStorage.setItem(STORAGE_KEY_SCHOOLS, JSON.stringify(schools))
}

function showAlert(message, type = 'success') {
    const alertContainer = document.getElementById('alert-container')
    const alert = document.createElement('div')
    alert.className = `alert alert-${type}`
    alert.textContent = message
    alertContainer.innerHTML = ''
    alertContainer.appendChild(alert)
    
    setTimeout(() => {
        alert.remove()
    }, 3000)
}

// Generate internal ID for region: reg<number>
function generateRegionInternalId() {
    // Find the highest region number
    let maxNumber = 0
    regions.forEach(region => {
        if (region.internalId && region.internalId.startsWith('reg')) {
            const match = region.internalId.match(/^reg(\d+)$/)
            if (match) {
                const num = parseInt(match[1], 10)
                if (num > maxNumber) {
                    maxNumber = num
                }
            }
        }
    })
    return `reg${maxNumber + 1}`
}

// Generate internal ID for school: reg<number>school<number>
function generateSchoolInternalId(regionId) {
    // Find the region's internal ID
    const region = regions.find(r => r.id === regionId)
    if (!region || !region.internalId) {
        throw new Error('Region not found or missing internal ID')
    }
    
    // Extract region number from internal ID (e.g., "reg1" -> 1)
    const regionMatch = region.internalId.match(/^reg(\d+)$/)
    if (!regionMatch) {
        throw new Error('Invalid region internal ID format')
    }
    const regionNumber = regionMatch[1]
    
    // Find the highest school number for this region
    let maxSchoolNumber = 0
    schools.forEach(school => {
        if (school.regionId === regionId && school.internalId) {
            const match = school.internalId.match(new RegExp(`^reg${regionNumber}school(\\d+)$`))
            if (match) {
                const num = parseInt(match[1], 10)
                if (num > maxSchoolNumber) {
                    maxSchoolNumber = num
                }
            }
        }
    })
    
    return `reg${regionNumber}school${maxSchoolNumber + 1}`
}

// Generate unique ID for localStorage (different from internal ID)
function generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2)
}

// Render functions
function renderRegions() {
    const container = document.getElementById('regions-list')
    
    if (regions.length === 0) {
        container.innerHTML = '<div class="empty-state">No regions added yet</div>'
        return
    }

    container.innerHTML = regions.map(region => `
        <div class="list-item">
            <div class="list-item-info">
                <div class="list-item-name">${region.name}</div>
                <div class="list-item-meta">
                    ${schools.filter(s => s.regionId === region.id).length} school(s) | ID: ${region.internalId || 'N/A'}
                </div>
            </div>
            <div class="list-item-actions">
                <button class="btn btn-danger" onclick="deleteRegion('${region.id}')">Delete</button>
            </div>
        </div>
    `).join('')
}

function renderSchools() {
    const container = document.getElementById('schools-list')
    
    if (schools.length === 0) {
        container.innerHTML = '<div class="empty-state">No schools added yet</div>'
        return
    }

    container.innerHTML = schools.map(school => {
        const region = regions.find(r => r.id === school.regionId)
        return `
            <div class="list-item">
                <div class="list-item-info">
                    <div class="list-item-name">${school.name}</div>
                    <div class="list-item-meta">Region: ${region ? region.name : 'Unknown'} | ID: ${school.internalId || 'N/A'}</div>
                </div>
                <div class="list-item-actions">
                    <button class="btn btn-danger" onclick="deleteSchool('${school.id}')">Delete</button>
                </div>
            </div>
        `
    }).join('')
}

function renderRegionSelect() {
    const select = document.getElementById('school-region')
    select.innerHTML = '<option value="">Select a region</option>' +
        regions.map(region => 
            `<option value="${region.id}">${region.name}</option>`
        ).join('')
}

// CRUD operations
function addRegion(name) {
    if (regions.some(r => r.name.toLowerCase() === name.toLowerCase())) {
        showAlert('Region already exists', 'error')
        return false
    }

    const region = {
        id: generateId(), // Unique ID for localStorage
        internalId: generateRegionInternalId(), // Internal ID: reg<number>
        name: name.trim()
    }
    regions.push(region)
    saveRegions()
    renderRegions()
    renderRegionSelect()
    showAlert(`Region "${name}" added successfully (ID: ${region.internalId})`)
    return true
}

function deleteRegion(id) {
    if (!confirm('Are you sure you want to delete this region? Schools in this region will also be deleted.')) {
        return
    }

    // Delete schools in this region
    schools = schools.filter(s => s.regionId !== id)
    saveSchools()

    // Delete region
    regions = regions.filter(r => r.id !== id)
    saveRegions()

    renderRegions()
    renderSchools()
    renderRegionSelect()
    showAlert('Region deleted successfully')
}

function addSchool(name, regionId) {
    if (schools.some(s => s.name.toLowerCase() === name.toLowerCase() && s.regionId === regionId)) {
        showAlert('School already exists in this region', 'error')
        return false
    }

    try {
        const school = {
            id: generateId(), // Unique ID for localStorage
            internalId: generateSchoolInternalId(regionId), // Internal ID: reg<number>school<number>
            name: name.trim(),
            regionId: regionId
        }
        schools.push(school)
        saveSchools()
        renderSchools()
        renderRegions()
        showAlert(`School "${name}" added successfully (ID: ${school.internalId})`)
        return true
    } catch (error) {
        showAlert(`Error adding school: ${error.message}`, 'error')
        return false
    }
}

function deleteSchool(id) {
    if (!confirm('Are you sure you want to delete this school?')) {
        return
    }

    schools = schools.filter(s => s.id !== id)
    saveSchools()
    renderSchools()
    renderRegions()
    showAlert('School deleted successfully')
}

// Make functions globally available for onclick handlers
window.deleteRegion = deleteRegion
window.deleteSchool = deleteSchool

// Form handlers
document.getElementById('region-form').addEventListener('submit', (e) => {
    e.preventDefault()
    const nameInput = document.getElementById('region-name')
    const name = nameInput.value.trim()
    
    if (name) {
        if (addRegion(name)) {
            nameInput.value = ''
        }
    }
})

document.getElementById('school-form').addEventListener('submit', (e) => {
    e.preventDefault()
    const nameInput = document.getElementById('school-name')
    const regionSelect = document.getElementById('school-region')
    const name = nameInput.value.trim()
    const regionId = regionSelect.value
    
    if (name && regionId) {
        if (addSchool(name, regionId)) {
            nameInput.value = ''
            regionSelect.value = ''
        }
    }
})

// Migrate existing data to add internal IDs if missing
function migrateToInternalIds() {
    let needsSave = false
    
    // Migrate regions
    regions.forEach(region => {
        if (!region.internalId) {
            region.internalId = generateRegionInternalId()
            needsSave = true
        }
    })
    
    // Migrate schools (after regions are migrated)
    schools.forEach(school => {
        if (!school.internalId) {
            try {
                school.internalId = generateSchoolInternalId(school.regionId)
                needsSave = true
            } catch (error) {
                console.error('Error migrating school:', error)
            }
        }
    })
    
    if (needsSave) {
        saveRegions()
        saveSchools()
    }
}

// Run migration on load (after all functions are defined)
migrateToInternalIds()

// Initial render
renderRegions()
renderSchools()
renderRegionSelect()

