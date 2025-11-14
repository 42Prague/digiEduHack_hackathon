// Backend data access + lightweight caching for regions and schools

import { regionsApi, schoolsApi } from './api.js'

let cachedRegions = []
let cachedSchools = []
let regionsSnapshot = '[]'
let schoolsSnapshot = '[]'
let pollTimer = null

/**
 * Load regions from backend and cache them locally
 * @returns {Promise<Array>}
 */
export async function loadRegions() {
    cachedRegions = await regionsApi.list()
    regionsSnapshot = JSON.stringify(cachedRegions)
    return cachedRegions
}

/**
 * Load schools from backend and cache them locally
 * @returns {Promise<Array>}
 */
export async function loadSchools() {
    cachedSchools = await schoolsApi.list()
    schoolsSnapshot = JSON.stringify(cachedSchools)
    return cachedSchools
}

/**
 * Force refresh both caches simultaneously
 * @returns {Promise<{regions: Array, schools: Array}>}
 */
export async function refreshData() {
    const [regions, schools] = await Promise.all([regionsApi.list(), schoolsApi.list()])
    cachedRegions = regions
    cachedSchools = schools
    regionsSnapshot = JSON.stringify(cachedRegions)
    schoolsSnapshot = JSON.stringify(cachedSchools)
    return { regions: cachedRegions, schools: cachedSchools }
}

/**
 * Get cached regions without hitting the backend
 * @returns {Array}
 */
export function getCachedRegions() {
    return cachedRegions
}

/**
 * Get cached schools without hitting the backend
 * @returns {Array}
 */
export function getCachedSchools() {
    return cachedSchools
}

/**
 * Poll backend for updates and notify callback when data changes
 * @param {Function} callback
 * @param {number} intervalMs
 */
export function watchStorageChanges(callback, intervalMs = 15000) {
    if (pollTimer) {
        clearInterval(pollTimer)
    }

    pollTimer = setInterval(async () => {
        try {
            const [regions, schools] = await Promise.all([regionsApi.list(), schoolsApi.list()])
            const nextRegionsSnapshot = JSON.stringify(regions)
            const nextSchoolsSnapshot = JSON.stringify(schools)

            if (nextRegionsSnapshot !== regionsSnapshot || nextSchoolsSnapshot !== schoolsSnapshot) {
                cachedRegions = regions
                cachedSchools = schools
                regionsSnapshot = nextRegionsSnapshot
                schoolsSnapshot = nextSchoolsSnapshot
                callback({ regions: cachedRegions, schools: cachedSchools })
            }
        } catch (error) {
            console.error('Failed to poll backend for regions/schools:', error)
        }
    }, intervalMs)
}
