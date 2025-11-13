// Configuration for file listing API
// Change this to match your backend endpoint
const FILE_LIST_API = 'http://localhost:3001/api/files' // Example: Node.js backend
// const FILE_LIST_API = 'http://localhost:5000/api/files' // Example: Python backend
// const FILE_LIST_API = '/api/files' // If using same origin

// File listing functionality
let uploadedFiles = []

// Fetch files from API
async function fetchFiles() {
    try {
        const response = await fetch(FILE_LIST_API)
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`)
        }
        const data = await response.json()
        uploadedFiles = data.files || []
        renderFiles()
    } catch (error) {
        console.error('Error fetching files:', error)
        document.getElementById('files-list').innerHTML = 
            '<div class="empty-state">' +
            '<p>Unable to load files. Make sure the backend API is running.</p>' +
            '<p style="font-size: 0.75rem; color: #64748b; margin-top: 0.5rem;">' +
            `API Endpoint: ${FILE_LIST_API}</p>` +
            '</div>'
    }
}

// Render files list
function renderFiles() {
    const container = document.getElementById('files-list')
    
    if (uploadedFiles.length === 0) {
        container.innerHTML = '<div class="empty-state">No files uploaded yet</div>'
        return
    }

    container.innerHTML = uploadedFiles.map(file => `
        <div class="list-item">
            <div class="list-item-info">
                <div class="list-item-name">${file.name || file.filename || 'Unknown'}</div>
                <div class="list-item-meta">
                    ${file.size ? formatFileSize(file.size) : ''}
                    ${file.uploadedAt ? ` • Uploaded: ${formatDate(file.uploadedAt)}` : ''}
                    ${file.schoolId ? ` • School ID: ${file.schoolId}` : ''}
                    ${file.regionId ? ` • Region ID: ${file.regionId}` : ''}
                </div>
            </div>
            <div class="list-item-actions">
                ${file.url ? `<a href="${file.url}" target="_blank" class="btn btn-secondary">View</a>` : ''}
                ${file.downloadUrl ? `<a href="${file.downloadUrl}" class="btn btn-secondary">Download</a>` : ''}
            </div>
        </div>
    `).join('')
}

// Format file size
function formatFileSize(bytes) {
    if (!bytes) return ''
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

// Format date
function formatDate(dateString) {
    if (!dateString) return ''
    const date = new Date(dateString)
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString()
}

// Refresh files list
function refreshFiles() {
    fetchFiles()
}

// Export functions
window.refreshFiles = refreshFiles

// Auto-refresh every 30 seconds
setInterval(fetchFiles, 30000)

// Initial load
if (document.getElementById('files-list')) {
    fetchFiles()
}

