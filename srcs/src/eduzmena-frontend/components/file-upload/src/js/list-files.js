// File listing pulled directly from the backend

import { filesApi } from './api.js'
import { config } from './config.js'

let uploadedFiles = []

async function fetchFiles() {
    try {
        uploadedFiles = await filesApi.list()
        renderFiles()
    } catch (error) {
        console.error('Error fetching files:', error)
        document.getElementById('files-list').innerHTML =
            '<div class="empty-state">' +
            '<p>Unable to load files. Make sure the backend API is running.</p>' +
            `<p style="font-size: 0.75rem; color: #64748b; margin-top: 0.5rem;">API Endpoint: ${config.apiBaseUrl}/files</p>` +
            '</div>'
    }
}

function renderFiles() {
    const container = document.getElementById('files-list')

    if (!uploadedFiles.length) {
        container.innerHTML = '<div class="empty-state">No files uploaded yet</div>'
        return
    }

    container.innerHTML = uploadedFiles.map(file => {
        const schoolInfo = file.school_id ? ` • School ID: ${file.school_id}` : ''
        const tusUrl = `${config.tusEndpoint}${file.tus_id}`

        return `
            <div class="list-item">
                <div class="list-item-info">
                    <div class="list-item-name">${file.filename || file.tus_id}</div>
                    <div class="list-item-meta">
                        TUS ID: ${file.tus_id}${schoolInfo}
                    </div>
                </div>
                <div class="list-item-actions">
                    <a href="${tusUrl}" target="_blank" class="btn btn-secondary">Open in tusd</a>
                </div>
            </div>
        `
    }).join('')
}

function refreshFiles() {
    fetchFiles()
}

window.refreshFiles = refreshFiles

setInterval(fetchFiles, 30000)

if (document.getElementById('files-list')) {
    fetchFiles()
}
