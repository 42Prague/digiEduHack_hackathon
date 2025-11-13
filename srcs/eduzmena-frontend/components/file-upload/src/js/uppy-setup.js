// Uppy initialization and configuration

import { config } from './config.js'
import { recordUploadMetadata } from './metadata.js'
import { getSelectedSchoolId } from './dropdowns.js'

let uppyInstance = null

/**
 * Load Uppy modules from CDN
 * @returns {Promise<Object>} Object containing Uppy, Dashboard, and Tus classes
 */
async function loadUppyModules() {
    const uppyModule = await import('https://releases.transloadit.com/uppy/v5.1.11/uppy.min.mjs')

    // Extract modules - handle different export patterns
    let Uppy, Dashboard, Tus

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

    return { Uppy, Dashboard, Tus }
}

/**
 * Initialize Uppy instance
 * @returns {Promise<Object>} Uppy instance
 */
export async function initializeUppy() {
    try {
        const { Uppy, Dashboard, Tus } = await loadUppyModules()

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

        // Setup event handlers
        setupEventHandlers(uppy)

        // Store instance globally for access
        window.uppyInstance = uppy
        uppyInstance = uppy

        console.log('Uppy initialized successfully')
        console.log('TUS Endpoint:', config.tusEndpoint)

        return uppy
    } catch (error) {
        console.error('Error initializing Uppy:', error)
        throw error
    }
}

/**
 * Setup Uppy event handlers
 * @param {Object} uppy - Uppy instance
 */
function setupEventHandlers(uppy) {
    // Update upload button state when school selection changes
    const schoolSelect = document.getElementById('school')
    if (schoolSelect) {
        schoolSelect.addEventListener('change', updateUploadButtonState)
        // Initial check
        updateUploadButtonState()
    }

    // Prevent upload if no school is selected
    uppy.on('upload', (data) => {
        const schoolId = getSelectedSchoolId()
        if (!schoolId) {
            uppy.cancelAll()
            alert('Please select a school before uploading files.')
            return false
        }
    })

    // Handle upload success
    uppy.on('upload-success', (file, response) => {
        console.log('File uploaded successfully:', file.name)
        console.log('Upload URL:', response.uploadURL)
    })

    // Handle upload errors
    uppy.on('upload-error', (file, error, response) => {
        console.error('Upload error:', file.name, error)
        if (response) {
            console.error('Response:', response)
        }
    })

    // Handle upload progress
    uppy.on('upload-progress', (file, progress) => {
        // Progress is handled automatically by Dashboard
        // This is just for logging if needed
        if (progress.bytesUploaded === progress.bytesTotal) {
            console.log(`${file.name}: Upload complete`)
        }
    })

    // Handle upload completion
    uppy.on('complete', async (result) => {
        if (result.successful.length > 0) {
            // Send POST notification for each successful upload
            for (const file of result.successful) {
                await handleSuccessfulUpload(file)
            }
        }
        if (result.failed.length > 0) {
            console.error(`Failed to upload ${result.failed.length} file(s)`)
            result.failed.forEach(file => {
                console.error(`  - ${file.name}: ${file.error}`)
            })
        }
    })
}

/**
 * Handle successful file upload - send notification to backend
 * @param {Object} file - Uploaded file object
 */
async function handleSuccessfulUpload(file) {
    if (!file.uploadURL) return

    const schoolId = getSelectedSchoolId()
    const fileId = file.uploadURL.replace(/\/$/, '').split('/').pop()

    const notifyResult = await recordUploadMetadata({
        fileId,
        fileName: file.name,
        schoolId
    })

    if (notifyResult.success) {
        console.log('Upload metadata stored successfully for:', file.name)
    } else {
        console.error('Failed to store upload metadata for:', file.name, notifyResult.error)
    }
}

/**
 * Update upload button state based on school selection
 */
export function updateUploadButtonState() {
    if (!uppyInstance) return

    const schoolId = getSelectedSchoolId()
    const dashboard = uppyInstance.getPlugin('Dashboard')

    if (dashboard) {
        if (schoolId) {
            dashboard.setOptions({ disabled: false })
        } else {
            dashboard.setOptions({ disabled: true })
        }
    }
}

// Export function for global access
window.updateUploadButtonState = updateUploadButtonState

/**
 * Get Uppy instance
 * @returns {Object|null} Uppy instance or null
 */
export function getUppyInstance() {
    return uppyInstance
}
