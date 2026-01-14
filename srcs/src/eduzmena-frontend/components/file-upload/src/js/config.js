// Application configuration

const DEFAULT_API_BASE_URL = window.__APP_CONFIG?.apiBaseUrl || 'http://localhost:8000'
const DEFAULT_TUS_ENDPOINT = window.__APP_CONFIG?.tusEndpoint || 'http://localhost:1080/files/'

function ensureNoTrailingSlash(url) {
    return url.endsWith('/') ? url.slice(0, -1) : url
}

function ensureTrailingSlash(url) {
    return url.endsWith('/') ? url : `${url}/`
}

export const config = {
    apiBaseUrl: ensureNoTrailingSlash(DEFAULT_API_BASE_URL),
    tusEndpoint: ensureTrailingSlash(DEFAULT_TUS_ENDPOINT),
    retryDelays: [0, 1000, 3000, 5000],
    chunkSize: 5 * 1024 * 1024, // 5MB
    resume: true,
    maxNumberOfFiles: null, // null = unlimited
    maxFileSize: null, // null = unlimited
    allowedFileTypes: null // null = all types
}
