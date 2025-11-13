// Configuration
const config = {
    tusEndpoint: 'http://127.0.0.1:1080/files/',
    retryDelays: [0, 1000, 3000, 5000],
    chunkSize: 5 * 1024 * 1024, // 5MB
    resume: true,
    maxNumberOfFiles: null, // null = unlimited
    maxFileSize: null, // null = unlimited
    allowedFileTypes: null // null = all types
}

// Data storage keys
const STORAGE_KEY_REGIONS = 'admin_regions'
const STORAGE_KEY_SCHOOLS = 'admin_schools'

// Load regions and schools from localStorage
let regions = JSON.parse(localStorage.getItem(STORAGE_KEY_REGIONS) || '[]')
let schools = JSON.parse(localStorage.getItem(STORAGE_KEY_SCHOOLS) || '[]')

// Populate dropdowns
function populateRegions() {
    const regionSelect = document.getElementById('region')
    regionSelect.innerHTML = '<option value="">Select a region</option>'
    
    regions.forEach(region => {
        const option = document.createElement('option')
        option.value = region.id
        option.textContent = region.name
        regionSelect.appendChild(option)
    })
}

function populateSchools(regionId = null) {
    const schoolSelect = document.getElementById('school')
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

// Handle region change to filter schools
function setupRegionFilter() {
    const regionSelect = document.getElementById('region')
    const schoolSelect = document.getElementById('school')
    
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

// Initialize dropdowns
populateRegions()
populateSchools()
setupRegionFilter()

// Function to check upload button state (will be called after Uppy is initialized)
window.updateUploadButtonState = function() {
    if (window.uppyInstance) {
        const schoolSelect = document.getElementById('school')
        const schoolId = schoolSelect ? schoolSelect.value : ''
        const dashboard = window.uppyInstance.getPlugin('Dashboard')
        
        if (dashboard) {
            if (schoolId) {
                dashboard.setOptions({ disabled: false })
            } else {
                dashboard.setOptions({ disabled: true })
            }
        }
    }
}

// Watch for storage changes (when admin panel updates data)
window.addEventListener('storage', (e) => {
    if (e.key === STORAGE_KEY_REGIONS || e.key === STORAGE_KEY_SCHOOLS) {
        regions = JSON.parse(localStorage.getItem(STORAGE_KEY_REGIONS) || '[]')
        schools = JSON.parse(localStorage.getItem(STORAGE_KEY_SCHOOLS) || '[]')
        const currentRegion = document.getElementById('region').value
        populateRegions()
        document.getElementById('region').value = currentRegion
        populateSchools(currentRegion || null)
    }
})

// Also check for changes in the same window (for when admin panel is in same tab)
setInterval(() => {
    const newRegions = JSON.parse(localStorage.getItem(STORAGE_KEY_REGIONS) || '[]')
    const newSchools = JSON.parse(localStorage.getItem(STORAGE_KEY_SCHOOLS) || '[]')
    
    if (JSON.stringify(newRegions) !== JSON.stringify(regions) || 
        JSON.stringify(newSchools) !== JSON.stringify(schools)) {
        regions = newRegions
        schools = newSchools
        const currentRegion = document.getElementById('region').value
        populateRegions()
        document.getElementById('region').value = currentRegion
        populateSchools(currentRegion || null)
    }
}, 1000) // Check every second

// Import Uppy modules from CDN
let Uppy, Dashboard, Tus

try {
    const uppyModule = await import('https://releases.transloadit.com/uppy/v5.1.11/uppy.min.mjs')
    
    // Extract modules - handle different export patterns
    if (uppyModule.Uppy) {
        Uppy = uppyModule.Uppy
        Dashboard = uppyModule.Dashboard
        Tus = uppyModule.Tus
    } else if (uppyModule.default) {
        Uppy = uppyModule.default.Uppy || uppyModule.default
        Dashboard = uppyModule.default.Dashboard
        Tus = uppyModule.default.Tus
    } else {
        // Try direct access
        Uppy = uppyModule.Uppy || uppyModule
        Dashboard = uppyModule.Dashboard
        Tus = uppyModule.Tus
    }

    if (!Uppy || !Dashboard || !Tus) {
        throw new Error('Failed to load Uppy modules. Available: ' + Object.keys(uppyModule).join(', '))
    }

    // Initialize Uppy
    const uppy = new Uppy({
        debug: true,
        autoProceed: false, // User must click upload button
        restrictions: {
            maxNumberOfFiles: config.maxNumberOfFiles,
            maxFileSize: config.maxFileSize,
            allowedFileTypes: config.allowedFileTypes
        }
    })

    // Add Dashboard plugin
    uppy.use(Dashboard, {
        target: '#files-drag-drop',
        inline: true,
        showProgressDetails: true,
        proudlyDisplayPoweredByUppy: false,
        height: 500,
        browserBackButtonClose: true,
        theme: 'light',
        // Disable upload button initially - will be enabled when school is selected
        disabled: true
    })

    // Initialize TUS plugin with endpoint from config
    uppy.use(Tus, {
        endpoint: config.tusEndpoint,
        retryDelays: config.retryDelays,
        chunkSize: config.chunkSize,
        resume: config.resume,
        removeFingerprintOnSuccess: false
    })

    // Store uppy instance globally for access
    window.uppyInstance = uppy

    // Function to check if school is selected and enable/disable upload
    function updateUploadButtonState() {
        const schoolSelect = document.getElementById('school')
        const schoolId = schoolSelect ? schoolSelect.value : ''
        const dashboard = uppy.getPlugin('Dashboard')
        
        if (dashboard) {
            if (schoolId) {
                dashboard.setOptions({ disabled: false })
            } else {
                dashboard.setOptions({ disabled: true })
            }
        }
    }

    // Check upload button state when school selection changes
    const schoolSelect = document.getElementById('school')
    if (schoolSelect) {
        schoolSelect.addEventListener('change', updateUploadButtonState)
        // Initial check
        updateUploadButtonState()
    }

    // Prevent upload if no school is selected
    uppy.on('upload', (data) => {
        const schoolId = document.getElementById('school')?.value
        if (!schoolId) {
            uppy.cancelAll()
            alert('Please select a school before uploading files.')
            return false
        }
    })

    // Handle upload events
    uppy.on('upload-success', (file, response) => {
        console.log('File uploaded successfully:', file.name)
        console.log('Upload URL:', response.uploadURL)
    })

    uppy.on('upload-error', (file, error, response) => {
        console.error('Upload error:', file.name, error)
        if (response) {
            console.error('Response:', response)
        }
    })

    uppy.on('upload-progress', (file, progress) => {
        // Progress is handled automatically by Dashboard
        // This is just for logging if needed
        if (progress.bytesUploaded === progress.bytesTotal) {
            console.log(`${file.name}: Upload complete`)
        }
    })

    uppy.on('complete', (result) => {
        if (result.successful.length > 0) {
            result.successful.forEach(file => {
                const schoolSelect = document.querySelector('#school')
                const regionSelect = document.querySelector('#region')
                const schoolId = schoolSelect?.value
                const regionId = regionSelect?.value
                
                // Find the selected school and region objects
                const selectedSchool = schools.find(s => s.id === schoolId)
                const selectedRegion = regions.find(r => r.id === regionId)
                
                console.log("Uploaded file:")
                console.log("File name:", file.name)
                console.log("File ID:", file.uploadURL.split('/').pop())
                console.log("School name:", schoolSelect?.selectedOptions[0]?.textContent || 'N/A')
                console.log("School internal ID:", selectedSchool?.internalId || 'N/A')
                console.log("Region name:", regionSelect?.selectedOptions[0]?.textContent || 'N/A')
                console.log("Region internal ID:", selectedRegion?.internalId || 'N/A')
            })
        }
        if (result.failed.length > 0) {
            console.error(`Failed to upload ${result.failed.length} file(s)`)
            result.failed.forEach(file => {
                console.error(`  - ${file.name}: ${file.error}`)
            })
        }
    })

    console.log('TUS Endpoint:', config.tusEndpoint)

} catch (error) {
    console.error('Error initializing Uppy:', error)
}