// Admin panel logic backed by the real API

import { regionsApi, schoolsApi, filesApi } from './api.js'
import { config } from './config.js'

let regions = []
let schools = []
let files = []

function escapeHtml(str) {
    if (!str) return ''
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
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

async function loadData() {
    try {
        const [regionData, schoolData, fileData] = await Promise.all([
            regionsApi.list(),
            schoolsApi.list(),
            filesApi.list(),
        ])

        regions = regionData
        schools = schoolData
        files = fileData

        renderRegions()
        renderSchools()
        renderRegionSelect()
        renderFiles()
    } catch (error) {
        console.error('Failed to load admin data:', error)
        showAlert('Unable to load data from backend. Check console for details.', 'error')
    }
}

function formatDateTime(iso) {
    if (!iso) return '–'
    const d = new Date(iso)
    return d.toLocaleString('cs-CZ', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    })
}

function renderRegions() {
    const container = document.getElementById('regions-list')

    if (!regions.length) {
        container.innerHTML = '<div class="empty-state">No regions created yet</div>'
        return
    }

    container.innerHTML = regions.map(region => `
        <div class="list-item">
            <div class="list-item-info">
                <div class="list-item-name">${region.name}</div>
                <div class="list-item-meta">
                    ${schools.filter(s => s.region_id === region.id).length} school(s) | ID: ${region.id}
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

    if (!schools.length) {
        container.innerHTML = '<div class="empty-state">No schools created yet</div>'
        return
    }

    container.innerHTML = schools.map(school => {
        const region = regions.find(r => r.id === school.region_id)
        return `
            <div class="list-item">
                <div class="list-item-info">
                    <div class="list-item-name">${school.name}</div>
                    <div class="list-item-meta">
                        Region: ${region ? region.name : 'Unknown'} | ID: ${school.id}
                    </div>
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
    if (!select) return
    select.innerHTML = '<option value="">Select a region</option>'
    regions.forEach(region => {
        const option = document.createElement('option')
        option.value = region.id
        option.textContent = region.name
        select.appendChild(option)
    })
}

function renderFiles() {
    const container = document.getElementById('files-list')
    if (!container) return

    if (!files.length) {
        container.innerHTML = '<div class="empty-state">No files uploaded yet</div>'
        return
    }

    container.innerHTML = files.map(file => {
        const school = schools.find(s => s.id === file.school_id)
        const region = school ? regions.find(r => r.id === school.region_id) : null

        const uploadedAt = formatDateTime(file.uploaded_at)
        const analysisStartedAt = formatDateTime(file.analysis_started_at)
        const analysisFinishedAt = formatDateTime(file.analysis_finished_at)
        const status = file.analysis_status || 'pending'

        const statusBadgeClass = {
            pending: 'badge-secondary',
            processing: 'badge-info',
            done: 'badge-success',
            failed: 'badge-danger',
        }[status] || 'badge-secondary'

        const basicStatsPreview = file.basic_stats
            ? `<pre class="file-json-preview">${JSON.stringify(file.basic_stats, null, 2)}</pre>`
            : '<span class="text-muted">No basic stats</span>'

        const llmSummaryPreview = file.llm_summary
            ? `<pre class="file-json-preview">${JSON.stringify(file.llm_summary, null, 2)}</pre>`
            : '<span class="text-muted">No LLM summary</span>'

        const transcriptPreview = file.transcript_text
            ? `
                <details class="file-details">
                    <summary>Transcript</summary>
                    <pre class="file-json-preview file-transcript-preview">
                        ${escapeHtml(file.transcript_text)}
                    </pre>
                </details>
            `
            : ''

        return `
            <div class="list-item">
                <div class="list-item-info">
                    <div class="list-item-name">
                        ${file.filename}
                        <span class="badge ${statusBadgeClass}" style="margin-left: 8px;">
                            ${status}
                        </span>
                    </div>
                    <div class="list-item-meta">
                        File ID: ${file.id ?? '–'} | TUS ID: ${file.tus_id}
                    </div>
                    <div class="list-item-meta">
                        School: ${school ? school.name : 'Unknown'}${region ? ` (Region: ${region.name})` : ''} |
                        School ID: ${file.school_id}
                    </div>
                    <div class="list-item-meta">
                        Uploaded at: ${uploadedAt} |
                        Analysis started: ${analysisStartedAt} |
                        Analysis finished: ${analysisFinishedAt}
                    </div>
                    ${
                        file.analysis_error
                            ? `<div class="list-item-meta text-danger">Error: ${file.analysis_error}</div>`
                            : ''
                    }
                    <details class="file-details">
                        <summary>Basic stats</summary>
                        ${basicStatsPreview}
                    </details>
                    <details class="file-details">
                        <summary>LLM summary</summary>
                        ${llmSummaryPreview}
                    </details>
                    ${transcriptPreview}
                </div>
                <div class="list-item-actions" style="display: flex; flex-direction: column; gap: 8px;">
                    <button class="btn btn-secondary" onclick="previewFile('${file.id}')">
                        Preview
                    </button>

                    <button class="btn btn-warning" onclick="retryFile('${file.id}')">
                        Re-run analysis
                    </button>
                </div>
            </div>
        `
    }).join('')
}

function previewFile(id) {
    const numericId = Number(id)
    const file = files.find(f => f.id === numericId || f.id === id)
    if (!file) return

    // Base tus endpoint, same as Uppy uses for uploads
    const base = config.tusEndpoint.replace(/\/$/, '')   // strip trailing /
    const url = `${base}/${file.tus_id}`                 // e.g. http://localhost:1080/files/<id>

    window.open(url, '_blank')
}

async function addRegion(name) {
    try {
        const payload = { name: name.trim() }
        const newRegion = await regionsApi.create(payload)
        await loadData()
        showAlert(`Region "${newRegion.name}" added successfully (ID: ${newRegion.id})`)
    } catch (error) {
        console.error('Error adding region:', error)
        showAlert(error.message || 'Failed to add region', 'error')
    }
}

async function addSchool(name, regionId) {
    try {
        const payload = {
            name: name.trim(),
            region_id: Number(regionId)
        }
        const newSchool = await schoolsApi.create(payload)
        await loadData()
        showAlert(`School "${newSchool.name}" added successfully (ID: ${newSchool.id})`)
    } catch (error) {
        console.error('Error adding school:', error)
        showAlert(error.message || 'Failed to add school', 'error')
    }
}

async function deleteRegion(id) {
    if (!confirm('Are you sure you want to delete this region?')) {
        return
    }

    try {
        await regionsApi.remove(id)
        await loadData()
        showAlert('Region deleted successfully')
    } catch (error) {
        console.error('Error deleting region:', error)
        showAlert(error.message || 'Failed to delete region', 'error')
    }
}

async function retryFile(id) {
    if (!confirm('Re-run analysis of this file?')) return

    try {
        await filesApi.retry(id)
        showAlert('Analysis restarted', 'success')
        await loadData()
    } catch (err) {
        console.error('Retry failed:', err)
        showAlert('Failed to restart analysis', 'error')
    }
}

async function deleteSchool(id) {
    if (!confirm('Are you sure you want to delete this school?')) {
        return
    }

    try {
        await schoolsApi.remove(id)
        await loadData()
        showAlert('School deleted successfully')
    } catch (error) {
        console.error('Error deleting school:', error)
        showAlert(error.message || 'Failed to delete school', 'error')
    }
}

function setupForms() {
    const regionForm = document.getElementById('region-form')
    const schoolForm = document.getElementById('school-form')

    regionForm?.addEventListener('submit', async (e) => {
        e.preventDefault()
        const nameInput = document.getElementById('region-name')
        const name = nameInput.value.trim()
        if (!name) return
        await addRegion(name)
        nameInput.value = ''
    })

    schoolForm?.addEventListener('submit', async (e) => {
        e.preventDefault()
        const nameInput = document.getElementById('school-name')
        const regionSelect = document.getElementById('school-region')
        const name = nameInput.value.trim()
        const regionId = regionSelect.value
        if (!name || !regionId) return
        await addSchool(name, regionId)
        nameInput.value = ''
        regionSelect.value = ''
    })
}

window.deleteRegion = deleteRegion
window.deleteSchool = deleteSchool
window.refreshFiles = () => loadData()
window.previewFile = previewFile
window.retryFile = retryFile

async function init() {
    setupForms()
    await loadData()
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => init())
} else {
    init()
}
