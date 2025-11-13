// Application configuration

export const config = {
    tusEndpoint: 'http://127.0.0.1:1080/files/',
    retryDelays: [0, 1000, 3000, 5000],
    chunkSize: 5 * 1024 * 1024, // 5MB
    resume: true,
    maxNumberOfFiles: null, // null = unlimited
    maxFileSize: null, // null = unlimited
    allowedFileTypes: null // null = all types
}

// Storage keys
export const STORAGE_KEY_REGIONS = 'admin_regions'
export const STORAGE_KEY_SCHOOLS = 'admin_schools'

