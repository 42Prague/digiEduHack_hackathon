// Minimal API client for the backend service

import { config } from './config.js'

/**
 * Build a backend URL by combining the base URL and provided path
 * @param {string} path
 * @returns {string}
 */
function buildUrl(path) {
    if (path.startsWith('http')) {
        return path
    }
    const normalizedBase = config.apiBaseUrl.replace(/\/$/, '')
    const normalizedPath = path.startsWith('/') ? path : `/${path}`
    return `${normalizedBase}${normalizedPath}`
}

/**
 * Perform a fetch call against the backend service
 * @param {string} path
 * @param {RequestInit} options
 * @returns {Promise<any>}
 */
async function request(path, options = {}) {
    const response = await fetch(buildUrl(path), {
        headers: {
            'Content-Type': 'application/json',
            ...(options.headers || {})
        },
        ...options
    })

    if (!response.ok) {
        const errorText = await response.text().catch(() => 'Unknown error')
        throw new Error(`Request failed (${response.status}): ${errorText}`)
    }

    if (response.status === 204) {
        return null
    }

    const text = await response.text()
    return text ? JSON.parse(text) : null
}

export const regionsApi = {
    list: () => request('/regions'),
    create: (payload) => request('/regions', { method: 'POST', body: JSON.stringify(payload) }),
    update: (id, payload) => request(`/regions/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
    remove: (id) => request(`/regions/${id}`, { method: 'DELETE' })
}

export const schoolsApi = {
    list: (regionId = null) => {
        const query = regionId ? `?region_id=${encodeURIComponent(regionId)}` : ''
        return request(`/schools${query}`)
    },
    create: (payload) => request('/schools', { method: 'POST', body: JSON.stringify(payload) }),
    update: (id, payload) => request(`/schools/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
    remove: (id) => request(`/schools/${id}`, { method: 'DELETE' })
}

export const filesApi = {
    list: () => request('/files'),
    create: (payload) => request('/files', { method: 'POST', body: JSON.stringify(payload) })
}
