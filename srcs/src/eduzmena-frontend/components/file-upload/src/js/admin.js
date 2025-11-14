// Admin panel logic backed by the real API

import { regionsApi, schoolsApi, filesApi } from './api.js'
import { config } from './config.js'

const DEFAULT_SCHOOLS_PAGE_SIZE = 10
const DEFAULT_FILES_PAGE_SIZE = 10
const UNKNOWN_DOCUMENT_TYPE_VALUE = '__unknown__'

const FILE_FORMAT_DEFINITIONS = [
    {
        value: 'text',
        label: 'Text document',
        icon: '📄',
        extensions: ['.txt', '.md', '.rtf', '.doc', '.docx', '.pdf']
    },
    {
        value: 'table',
        label: 'Table / Spreadsheet',
        icon: '📊',
        extensions: ['.csv', '.tsv', '.xls', '.xlsx', '.ods']
    },
    {
        value: 'audio',
        label: 'Audio',
        icon: '🎧',
        extensions: ['.mp3', '.wav', '.m4a', '.aac', '.flac', '.ogg']
    }
]

const DEFAULT_FILE_FORMAT = {
    value: 'text',
    label: 'Text document',
    icon: '📄'
}

let regions = []
let schools = []
let files = []

const schoolPagination = {
    page: 1,
    pageSize: DEFAULT_SCHOOLS_PAGE_SIZE
}

const filePagination = {
    page: 1,
    pageSize: DEFAULT_FILES_PAGE_SIZE
}

function escapeHtml(str) {
    if (!str) return ''
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
}

function showAlert(message, type = 'success') {
    const alertContainer = document.getElementById('alert-container')
    if (!alertContainer) return

    const alert = document.createElement('div')
    alert.className = `alert alert-${type} alert-popover`
    alert.textContent = message

    alertContainer.innerHTML = ''
    alertContainer.appendChild(alert)

    requestAnimationFrame(() => {
        alert.classList.add('is-visible')
    })

    setTimeout(() => {
        alert.classList.remove('is-visible')
        alert.classList.add('is-leaving')
    }, 2600)

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
        schoolPagination.page = 1
        filePagination.page = 1

        renderRegions()
        renderRegionSelects()
        renderSchoolFilterSelect()
        renderDocumentTypeFilterSelect()
        renderFileFormatFilterSelect()
        renderSchools()
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
    if (!container) return

    const regionFilter = document.getElementById('schools-region-filter')?.value || ''
    const schoolsToRender = regionFilter
        ? schools.filter(s => String(s.region_id) === regionFilter)
        : schools

    if (!schoolsToRender.length) {
        const emptyMessage = regionFilter
            ? 'No schools found for the selected region'
            : 'No schools created yet'
        container.innerHTML = `<div class="empty-state">${emptyMessage}</div>`
        renderSchoolPagination({ totalItems: 0, totalPages: 0, start: 0, end: 0 })
        return
    }

    const safePageSize = Math.max(1, Number(schoolPagination.pageSize) || DEFAULT_SCHOOLS_PAGE_SIZE)
    if (safePageSize !== schoolPagination.pageSize) {
        schoolPagination.pageSize = safePageSize
    }

    const totalItems = schoolsToRender.length
    const totalPages = Math.max(Math.ceil(totalItems / safePageSize), 1)
    if (schoolPagination.page > totalPages) {
        schoolPagination.page = totalPages
    }

    const currentPage = Math.max(schoolPagination.page, 1)
    schoolPagination.page = currentPage

    const startIndex = (currentPage - 1) * safePageSize
    const paginatedSchools = schoolsToRender.slice(startIndex, startIndex + safePageSize)
    const endIndex = startIndex + paginatedSchools.length

    container.innerHTML = paginatedSchools.map(school => {
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

    renderSchoolPagination({
        totalItems,
        totalPages,
        start: startIndex + 1,
        end: endIndex
    })
}

function renderSchoolPagination({ totalItems, totalPages, start, end }) {
    const container = document.getElementById('schools-pagination')
    if (!container) return

    if (!totalItems) {
        container.innerHTML = ''
        return
    }

    const pageCount = Math.max(totalPages, 1)
    const currentPage = Math.min(Math.max(schoolPagination.page, 1), pageCount)
    const rangeStart = Math.min(start, totalItems)
    const rangeEnd = Math.min(end, totalItems)
    const prevDisabled = currentPage <= 1
    const nextDisabled = currentPage >= pageCount

    container.innerHTML = `
        <div class="pagination-info">Showing ${rangeStart}-${rangeEnd} of ${totalItems}</div>
        <div class="pagination-controls">
            <button type="button" class="btn btn-secondary" data-action="prev" ${prevDisabled ? 'disabled' : ''}>
                Previous
            </button>
            <div class="pagination-page">Page ${currentPage} / ${pageCount}</div>
            <button type="button" class="btn btn-secondary" data-action="next" ${nextDisabled ? 'disabled' : ''}>
                Next
            </button>
        </div>
    `

    container.querySelector('[data-action="prev"]')?.addEventListener('click', () => {
        if (schoolPagination.page > 1) {
            schoolPagination.page -= 1
            renderSchools()
        }
    })

    container.querySelector('[data-action="next"]')?.addEventListener('click', () => {
        const maxPage = Math.max(pageCount, 1)
        if (schoolPagination.page < maxPage) {
            schoolPagination.page += 1
            renderSchools()
        }
    })
}

function renderRegionSelects() {
    const configs = [
        { id: 'school-region', placeholder: 'Select region' },
        { id: 'files-region-filter', placeholder: 'All regions' },
        { id: 'schools-region-filter', placeholder: 'All schools' }
    ]

    configs.forEach(({ id, placeholder }) => {
        const select = document.getElementById(id)
        if (!select) return

        const prevValue = select.value
        select.innerHTML = ''

        const defaultOption = document.createElement('option')
        defaultOption.value = ''
        defaultOption.textContent = placeholder
        select.appendChild(defaultOption)

        regions.forEach(region => {
            const option = document.createElement('option')
            option.value = String(region.id)
            option.textContent = region.name
            select.appendChild(option)
        })

        const optionExists = regions.some(region => String(region.id) === prevValue)
        if (prevValue && optionExists) {
            select.value = prevValue
        }
    })
}

function renderSchoolFilterSelect() {
    const select = document.getElementById('files-school-filter')
    if (!select) return

    const regionFilter = document.getElementById('files-region-filter')?.value || ''
    const prevValue = select.value
    select.innerHTML = '<option value="">All schools</option>'

    const availableSchools = regionFilter
        ? schools.filter(s => String(s.region_id) === regionFilter)
        : schools

    availableSchools.forEach(school => {
        const option = document.createElement('option')
        option.value = String(school.id)
        option.textContent = school.name
        select.appendChild(option)
    })

    const optionExists = availableSchools.some(s => String(s.id) === prevValue)
    select.value = optionExists ? prevValue : ''
}

function renderDocumentTypeFilterSelect() {
    const select = document.getElementById('files-doc-type-filter')
    if (!select) return

    const prevValue = select.value
    select.innerHTML = '<option value="">All document types</option>'

    const typeMap = new Map()
    files.forEach(file => {
        const { type, label, icon } = getDocumentTypeInfo(file)
        const value = type ?? UNKNOWN_DOCUMENT_TYPE_VALUE
        if (!typeMap.has(value)) {
            typeMap.set(value, {
                label: label || 'Unknown document type',
                icon: icon || ''
            })
        }
    })

    const sortedTypes = Array
        .from(typeMap.entries())
        .sort((a, b) => a[1].label.localeCompare(b[1].label))

    sortedTypes.forEach(([value, info]) => {
        const option = document.createElement('option')
        option.value = value
        const text = info.icon ? `${info.icon} ${info.label}` : info.label
        option.textContent = text
        select.appendChild(option)
    })

    const optionExists = sortedTypes.some(([value]) => value === prevValue)
    select.value = optionExists ? prevValue : ''
}

function getFileFormatInfo(file) {
    const filename = (file?.filename || '').toLowerCase()
    const dotIndex = filename.lastIndexOf('.')
    const extension = dotIndex >= 0 ? filename.slice(dotIndex) : ''

    const match = FILE_FORMAT_DEFINITIONS.find(def =>
        def.extensions.includes(extension)
    )

    if (match) {
        return match
    }

    if (!extension && file?.transcript_text) {
        const audioFormat = FILE_FORMAT_DEFINITIONS.find(def => def.value === 'audio')
        if (audioFormat) {
            return audioFormat
        }
    }

    return DEFAULT_FILE_FORMAT
}

function getDocumentTypeInfo(file) {
    const raw = file.llm_summary
    if (!raw) {
        return { type: null, icon: '📄', label: 'Unknown document type' }
    }

    let obj = raw
    if (typeof raw === 'string') {
        try {
            obj = JSON.parse(raw)
        } catch (e) {
            return { type: null, icon: '📄', label: 'Unknown document type' }
        }
    }

    const detectedType = obj?.data?.type || obj?.type || null

    switch (detectedType) {
        case 'attendance_checklist':
            return { type: detectedType, icon: '📋', label: 'Attendance checklist' }
        case 'feedback_form':
            return { type: detectedType, icon: '📝', label: 'Feedback form' }
        case 'record':
            return { type: detectedType, icon: '📄', label: 'Record' }
        default:
            return { type: detectedType, icon: '❔', label: 'Unknown document type' }
    }
}

function renderFileFormatFilterSelect() {
    const select = document.getElementById('files-format-filter')
    if (!select) return

    const prevValue = select.value
    select.innerHTML = '<option value="">All formats</option>'

    const formatMap = new Map()
    files.forEach(file => {
        const { value, label, icon } = getFileFormatInfo(file)
        if (!formatMap.has(value)) {
            formatMap.set(value, { label, icon })
        }
    })

    const sortedFormats = Array
        .from(formatMap.entries())
        .sort((a, b) => a[1].label.localeCompare(b[1].label))

    sortedFormats.forEach(([value, info]) => {
        const option = document.createElement('option')
        option.value = value
        option.textContent = info.icon ? `${info.icon} ${info.label}` : info.label
        select.appendChild(option)
    })

    const optionExists = formatMap.has(prevValue)
    select.value = optionExists ? prevValue : ''
}

function renderFiles() {
    const container = document.getElementById('files-list')
    if (!container) return

    const regionFilter = document.getElementById('files-region-filter')?.value || ''
    const schoolFilter = document.getElementById('files-school-filter')?.value || ''
    const docTypeFilter = document.getElementById('files-doc-type-filter')?.value || ''
    const formatFilter = document.getElementById('files-format-filter')?.value || ''
    const statusFilter = document.getElementById('files-status-filter')?.value || ''

    const filteredFiles = files.filter(file => {
        const school = schools.find(s => s.id === file.school_id)
        const matchesRegion = regionFilter
            ? school && String(school.region_id) === regionFilter
            : true
        const matchesSchool = schoolFilter
            ? String(file.school_id) === schoolFilter
            : true
        const { type } = getDocumentTypeInfo(file)
        const docTypeValue = type ?? UNKNOWN_DOCUMENT_TYPE_VALUE
        const matchesDocType = docTypeFilter
            ? docTypeValue === docTypeFilter
            : true
        const fileFormat = getFileFormatInfo(file)
        const matchesFormat = formatFilter
            ? fileFormat.value === formatFilter
            : true
        const fileStatus = file.analysis_status || 'pending'
        const matchesStatus = statusFilter
            ? fileStatus === statusFilter
            : true
        return matchesRegion && matchesSchool && matchesDocType && matchesFormat && matchesStatus
    })

    if (!filteredFiles.length) {
        const emptyMessage = schoolFilter
            ? 'No files uploaded for the selected school'
            : 'No files uploaded yet'
        container.innerHTML = `<div class="empty-state">${emptyMessage}</div>`
        renderFilePagination({ totalItems: 0, totalPages: 0, start: 0, end: 0 })
        return
    }

    const safePageSize = Math.max(1, Number(filePagination.pageSize) || DEFAULT_FILES_PAGE_SIZE)
    if (safePageSize !== filePagination.pageSize) {
        filePagination.pageSize = safePageSize
    }

    const totalItems = filteredFiles.length
    const totalPages = Math.max(Math.ceil(totalItems / safePageSize), 1)
    if (filePagination.page > totalPages) {
        filePagination.page = totalPages
    }
    const currentPage = Math.max(filePagination.page, 1)
    filePagination.page = currentPage

    const startIndex = (currentPage - 1) * safePageSize
    const paginatedFiles = filteredFiles.slice(startIndex, startIndex + safePageSize)
    const endIndex = startIndex + paginatedFiles.length

    container.innerHTML = paginatedFiles.map(file => {
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

        const { type: docType, icon: docIcon, label: docLabel } = getDocumentTypeInfo(file)
        const docTypeLabel = docType ? `${docLabel} (${docType})` : docLabel
        const { label: formatLabel, icon: formatIcon } = getFileFormatInfo(file)
        const formatDisplay = formatIcon ? `${formatIcon} ${formatLabel}` : formatLabel

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
                        <span class="file-type-icon" title="${escapeHtml(docLabel)}" style="margin-right: 4px;">
                            ${docIcon}
                        </span>
                        ${file.filename}
                        <span class="badge ${statusBadgeClass}" style="margin-left: 8px;">
                            ${status}
                        </span>
                    </div>
                    <div class="list-item-meta">
                        File ID: ${file.id ?? '–'} | TUS ID: ${file.tus_id} |
                        Type: ${escapeHtml(docTypeLabel)} |
                        Format: ${escapeHtml(formatDisplay)}
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
                        Preview file
                    </button>

                    <button class="btn btn-warning" onclick="retryFile('${file.id}')">
                        Refresh analysis
                    </button>
                </div>
            </div>
        `
    }).join('')

    renderFilePagination({
        totalItems,
        totalPages,
        start: startIndex + 1,
        end: endIndex
    })
}

function renderFilePagination({ totalItems, totalPages, start, end }) {
    const container = document.getElementById('files-pagination')
    if (!container) return

    if (!totalItems) {
        container.innerHTML = ''
        return
    }

    const pageCount = Math.max(totalPages, 1)
    const currentPage = Math.min(Math.max(filePagination.page, 1), pageCount)
    const rangeStart = Math.min(start, totalItems)
    const rangeEnd = Math.min(end, totalItems)
    const prevDisabled = currentPage <= 1
    const nextDisabled = currentPage >= pageCount

    container.innerHTML = `
        <div class="pagination-info">Ukazují se ${rangeStart}-${rangeEnd} z ${totalItems}</div>
        <div class="pagination-controls">
            <button type="button" class="btn btn-secondary" data-action="prev" ${prevDisabled ? 'disabled' : ''}>
                Previous
            </button>
            <div class="pagination-page">Page ${currentPage} / ${pageCount}</div>
            <button type="button" class="btn btn-secondary" data-action="next" ${nextDisabled ? 'disabled' : ''}>
                Next
            </button>
        </div>
    `

    container.querySelector('[data-action="prev"]')?.addEventListener('click', () => {
        if (filePagination.page > 1) {
            filePagination.page -= 1
            renderFiles()
        }
    })

    container.querySelector('[data-action="next"]')?.addEventListener('click', () => {
        const maxPage = Math.max(pageCount, 1)
        if (filePagination.page < maxPage) {
            filePagination.page += 1
            renderFiles()
        }
    })
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
        showAlert(`Region "${newRegion.name}" was successfully added (ID: ${newRegion.id})`)
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
        showAlert(`School "${newSchool.name}" was successfully added (ID: ${newSchool.id})`)
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
        showAlert('Region was successfully deleted')
    } catch (error) {
        console.error('Error deleting region:', error)
        showAlert(error.message || 'Failed to delete region', 'error')
    }
}

async function retryFile(id) {
    if (!confirm('Are you sure you want to refresh the analysis of this file?')) return

    try {
        await filesApi.retry(id)
        showAlert('Analysis was successfully refreshed', 'success')
        await loadData()
    } catch (err) {
        console.error('Error refreshing analysis:', err)
        showAlert('Failed to refresh analysis', 'error')
    }
}

async function deleteSchool(id) {
    if (!confirm('Are you sure you want to delete this school?')) {
        return
    }

    try {
        await schoolsApi.remove(id)
        await loadData()
        showAlert('School was successfully deleted')
    } catch (error) {
        console.error('Error deleting school:', error)
        showAlert(error.message || 'Failed to delete school', 'error')
    }
}

function setupForms() {
    const regionForm = document.getElementById('region-form')
    const schoolForm = document.getElementById('school-form')
    const schoolsRegionFilter = document.getElementById('schools-region-filter')
    const schoolsPageSizeSelect = document.getElementById('schools-page-size')
    const filesRegionFilter = document.getElementById('files-region-filter')
    const filesSchoolFilter = document.getElementById('files-school-filter')
    const filesDocTypeFilter = document.getElementById('files-doc-type-filter')
    const filesFormatFilter = document.getElementById('files-format-filter')
    const filesStatusFilter = document.getElementById('files-status-filter')
    const filesPageSizeSelect = document.getElementById('files-page-size')

    regionForm?.addEventListener('submit', async (e) => {
        e.preventDefault()
        const nameInput = document.getElementById('region-name')
        const name = nameInput.value.trim()
        if (!name) return
        await addRegion(name)
        nameInput.value = ''
    })
    schoolsRegionFilter?.addEventListener('change', () => {
        schoolPagination.page = 1
        renderSchools()
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

    filesRegionFilter?.addEventListener('change', () => {
        filePagination.page = 1
        renderSchoolFilterSelect()
        renderSchools()
        renderFiles()
    })
    filesSchoolFilter?.addEventListener('change', () => {
        filePagination.page = 1
        renderFiles()
    })
    filesDocTypeFilter?.addEventListener('change', () => {
        filePagination.page = 1
        renderFiles()
    })
    filesFormatFilter?.addEventListener('change', () => {
        filePagination.page = 1
        renderFiles()
    })
    filesStatusFilter?.addEventListener('change', () => {
        filePagination.page = 1
        renderFiles()
    })

    if (filesPageSizeSelect) {
        const parsedValue = Number(filesPageSizeSelect.value)
        if (!Number.isNaN(parsedValue) && parsedValue > 0) {
            filePagination.pageSize = parsedValue
        }

        filesPageSizeSelect.addEventListener('change', (event) => {
            const newSize = Number(event.target.value)
            filePagination.pageSize = !Number.isNaN(newSize) && newSize > 0
                ? newSize
                : DEFAULT_FILES_PAGE_SIZE
            filePagination.page = 1
            renderFiles()
        })
    }

    if (schoolsPageSizeSelect) {
        const parsedValue = Number(schoolsPageSizeSelect.value)
        if (!Number.isNaN(parsedValue) && parsedValue > 0) {
            schoolPagination.pageSize = parsedValue
        }

        schoolsPageSizeSelect.addEventListener('change', (event) => {
            const newSize = Number(event.target.value)
            schoolPagination.pageSize = !Number.isNaN(newSize) && newSize > 0
                ? newSize
                : DEFAULT_SCHOOLS_PAGE_SIZE
            schoolPagination.page = 1
            renderSchools()
        })
    }
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
