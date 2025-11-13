// Admin panel logic backed by the real API

import { regionsApi, schoolsApi } from './api.js'

let regions = []
let schools = []

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
        const [regionData, schoolData] = await Promise.all([
            regionsApi.list(),
            schoolsApi.list()
        ])
        regions = regionData
        schools = schoolData
        renderRegions()
        renderSchools()
        renderRegionSelect()
    } catch (error) {
        console.error('Failed to load admin data:', error)
        showAlert('Unable to load data from backend. Check console for details.', 'error')
    }
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
                    <div class="list-item-meta">Region: ${region ? region.name : 'Unknown'} | ID: ${school.id}</div>
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

async function init() {
    setupForms()
    await loadData()
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => init())
} else {
    init()
}
