// Upload metadata helpers - store successful uploads in the backend database

import { filesApi } from './api.js'

/**
 * Inform the backend about a successful TUS upload
 * @param {Object} payload
 * @param {string} payload.fileId - tusd upload identifier
 * @param {string} payload.fileName - original file name
 * @param {string} payload.schoolId - selected school ID (string from dropdown)
 * @returns {Promise<{success: boolean, data?: any, error?: string}>}
 */
export async function recordUploadMetadata({ fileId, fileName, schoolId }) {
    try {
        const body = {
            tus_id: fileId,
            filename: fileName,
            school_id: schoolId ? Number(schoolId) : null
        }
        console.log(body)
        const data = await filesApi.create(body)
        return { success: true, data }
    } catch (error) {
        console.error('Error recording upload metadata:', error)
        return { success: false, error: error.message }
    }
}
