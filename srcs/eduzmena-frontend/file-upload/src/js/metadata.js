// Upload notification service
// Sends POST request to backend when file upload is successful

// Configuration
const NOTIFICATION_API = '/api/upload/notify' // Change this to your backend endpoint

/**
 * Send notification to backend about successful file upload
 * @param {Object} fileData - File upload data
 * @param {string} fileData.fileId - TUS upload ID
 * @param {string} fileData.fileName - Original file name
 * @param {string} fileData.uploadURL - TUS upload URL
 * @param {string} fileData.schoolId - Selected school ID
 * @param {string} fileData.regionId - Selected region ID
 * @param {string} fileData.schoolInternalId - School internal ID (reg1school1)
 * @param {string} fileData.regionInternalId - Region internal ID (reg1)
 * @returns {Promise<Object>} Response from server
 */
export async function notifyUploadSuccess(fileData) {
    try {
        const response = await fetch(NOTIFICATION_API, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                fileId: fileData.fileId,
                fileName: fileData.fileName,
                uploadURL: fileData.uploadURL,
                schoolId: fileData.schoolId,
                regionId: fileData.regionId,
                schoolInternalId: fileData.schoolInternalId,
                regionInternalId: fileData.regionInternalId,
                uploadedAt: new Date().toISOString()
            })
        })

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`)
        }

        const data = await response.json()
        return { success: true, data }
    } catch (error) {
        console.error('Error sending upload notification:', error)
        return { success: false, error: error.message }
    }
}

/**
 * Send notification using XMLHttpRequest (alternative to fetch)
 * @param {Object} fileData - File upload data
 * @returns {Promise<Object>} Response from server
 */
export function notifyUploadSuccessXHR(fileData) {
    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest()
        
        xhr.open('POST', NOTIFICATION_API, true)
        xhr.setRequestHeader('Content-Type', 'application/json')
        
        xhr.onload = function() {
            if (xhr.status >= 200 && xhr.status < 300) {
                try {
                    const data = JSON.parse(xhr.responseText || '{}')
                    resolve({ success: true, data })
                } catch (e) {
                    resolve({ success: true, data: xhr.responseText })
                }
            } else {
                reject(new Error(`HTTP error! status: ${xhr.status}`))
            }
        }
        
        xhr.onerror = function() {
            reject(new Error('Network error'))
        }
        
        const payload = {
            fileId: fileData.fileId,
            fileName: fileData.fileName,
            uploadURL: fileData.uploadURL,
            schoolId: fileData.schoolId,
            regionId: fileData.regionId,
            schoolInternalId: fileData.schoolInternalId,
            regionInternalId: fileData.regionInternalId,
            uploadedAt: new Date().toISOString()
        }
        
        xhr.send(JSON.stringify(payload))
    }).catch(error => {
        console.error('Error sending upload notification:', error)
        return { success: false, error: error.message }
    })
}

