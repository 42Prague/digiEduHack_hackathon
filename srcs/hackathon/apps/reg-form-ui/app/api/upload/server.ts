// gcs-functions.ts

import { Storage } from '@google-cloud/storage';
import mime from 'mime-types';
import path from 'path';
// import { Readable } from 'stream';
import * as fs from 'fs';

// Configuration
// Get variables from environment
const PROJECT_ID = process.env.GCP_PROJECT_ID;
const BUCKET_NAME = process.env.GCS_BUCKET_NAME;
const SA_KEY_JSON = process.env.GCP_SA_KEY_JSON;

// Essential check
if (!SA_KEY_JSON || !PROJECT_ID || !BUCKET_NAME) {
  throw new Error("Missing GCP environment variables for Storage initialization.");
}

// 1. Parse the JSON string from the environment variable
const credentials = JSON.parse(SA_KEY_JSON);

// Initialize Google Cloud Storage
const storage = new Storage({
  projectId: PROJECT_ID,
  // 2. Use the parsed credentials object directly
  credentials: credentials
});

const bucket = storage.bucket(BUCKET_NAME);
// Types
interface UploadOptions {
  folder?: string;
  contentType?: string;
}

interface UploadResult {
  status: 'success' | 'error';
  message: string;
  fileName?: string;
  blobName?: string;
  size?: number;
  contentType?: string;
}

interface FileInfo {
  name: string;
  size: number;
  content_type: string | null;
  created: string | null;
  updated: string | null;
}

interface ListResult {
  status: 'success' | 'error';
  message?: string;
  count?: number;
  files?: FileInfo[];
}

interface DeleteResult {
  status: 'success' | 'error';
  message: string;
}

interface DownloadResult {
  status: 'success' | 'error';
  message?: string;
  buffer?: Buffer;
  contentType?: string;
  fileName?: string;
}

// Helper function to determine content type
function getContentType(filename: string, providedType?: string): string {
  if (providedType) {
    return providedType;
  }
  
  const detectedType = mime.lookup(filename);
  if (detectedType) {
    return detectedType;
  }
  
  return 'application/octet-stream';
}

/**
 * Upload a file to Google Cloud Storage
 * @param fileBuffer - Buffer containing the file data
 * @param fileName - Original filename
 * @param options - Upload options (folder, contentType)
 * @returns Promise<UploadResult>
 */
export async function uploadFile(
  fileBuffer: Buffer,
  fileName: string,
  options: UploadOptions = {}
): Promise<UploadResult> {
  try {
    const { folder, contentType } = options;

    // Construct blob name
    const blobName = folder
      ? `${folder.replace(/^\/+|\/+$/g, '')}/${fileName}`
      : fileName;

    // Determine content type
    const finalContentType = getContentType(fileName, contentType);

    // Create blob and upload
    const blob = bucket.file(blobName);
    
    await blob.save(fileBuffer, {
      resumable: false,
      metadata: {
        contentType: finalContentType
      }
    });

    return {
      status: 'success',
      message: 'File uploaded successfully',
      fileName: fileName,
      blobName: blobName,
      size: fileBuffer.length,
      contentType: finalContentType
    };
  } catch (error: any) {
    return {
      status: 'error',
      message: `Upload failed: ${error.message}`
    };
  }
}

/**
 * Upload a file from local filesystem to Google Cloud Storage
 * @param localFilePath - Path to local file
 * @param options - Upload options (folder, contentType)
 * @returns Promise<UploadResult>
 */
export async function uploadFileFromPath(
  localFilePath: string,
  options: UploadOptions = {}
): Promise<UploadResult> {
  try {
    const fileBuffer = fs.readFileSync(localFilePath);
    const fileName = path.basename(localFilePath);
    return await uploadFile(fileBuffer, fileName, options);
  } catch (error: any) {
    return {
      status: 'error',
      message: `Upload failed: ${error.message}`
    };
  }
}

/**
 * Download a file from Google Cloud Storage
 * @param filePath - Path to file in GCS bucket
 * @returns Promise<DownloadResult>
 */
export async function downloadFile(filePath: string): Promise<DownloadResult> {
  try {
    if (!filePath) {
      return {
        status: 'error',
        message: 'File path is required'
      };
    }

    const blob = bucket.file(filePath);

    // Check if file exists
    const [exists] = await blob.exists();
    if (!exists) {
      return {
        status: 'error',
        message: `File '${filePath}' not found`
      };
    }

    // Get file metadata
    const [metadata] = await blob.getMetadata();
    const fileName = path.basename(filePath);

    // Download the file
    const [buffer] = await blob.download();

    return {
      status: 'success',
      buffer: buffer,
      contentType: metadata.contentType || 'application/octet-stream',
      fileName: fileName
    };
  } catch (error: any) {
    return {
      status: 'error',
      message: `Download failed: ${error.message}`
    };
  }
}

/**
 * Download a file from GCS and save to local filesystem
 * @param filePath - Path to file in GCS bucket
 * @param localDestPath - Local destination path
 * @returns Promise<DownloadResult>
 */
export async function downloadFileToPath(
  filePath: string,
  localDestPath: string
): Promise<DownloadResult> {
  try {
    const result = await downloadFile(filePath);
    
    if (result.status === 'error' || !result.buffer) {
      return result;
    }

    fs.writeFileSync(localDestPath, result.buffer);

    return {
      status: 'success',
      message: `File downloaded to ${localDestPath}`,
      fileName: result.fileName,
      contentType: result.contentType
    };
  } catch (error: any) {
    return {
      status: 'error',
      message: `Download failed: ${error.message}`
    };
  }
}

/**
 * List files in Google Cloud Storage bucket
 * @param prefix - Optional prefix to filter files
 * @returns Promise<ListResult>
 */
export async function listFiles(prefix?: string): Promise<ListResult> {
  try {
    const [files] = await bucket.getFiles({ prefix });

    const fileList: FileInfo[] = files.map(file => ({
      name: file.name,
      size: file.metadata.size ? parseInt(file.metadata.size) : 0,
      content_type: file.metadata.contentType || null,
      created: file.metadata.timeCreated || null,
      updated: file.metadata.updated || null
    }));

    return {
      status: 'success',
      count: fileList.length,
      files: fileList
    };
  } catch (error: any) {
    return {
      status: 'error',
      message: `List failed: ${error.message}`
    };
  }
}

/**
 * Delete a file from Google Cloud Storage
 * @param filePath - Path to file in GCS bucket
 * @returns Promise<DeleteResult>
 */
export async function deleteFile(filePath: string): Promise<DeleteResult> {
  try {
    if (!filePath) {
      return {
        status: 'error',
        message: 'File path is required'
      };
    }

    const blob = bucket.file(filePath);

    // Check if file exists
    const [exists] = await blob.exists();
    if (!exists) {
      return {
        status: 'error',
        message: `File '${filePath}' not found`
      };
    }

    // Delete the file
    await blob.delete();

    return {
      status: 'success',
      message: `File '${filePath}' deleted successfully`
    };
  } catch (error: any) {
    return {
      status: 'error',
      message: `Delete failed: ${error.message}`
    };
  }
}

/**
 * Check if a file exists in Google Cloud Storage
 * @param filePath - Path to file in GCS bucket
 * @returns Promise<boolean>
 */
export async function fileExists(filePath: string): Promise<boolean> {
  try {
    const blob = bucket.file(filePath);
    const [exists] = await blob.exists();
    return exists;
  } catch (error) {
    return false;
  }
}

/**
 * Get file metadata from Google Cloud Storage
 * @param filePath - Path to file in GCS bucket
 * @returns Promise with metadata or error
 */
export async function getFileMetadata(filePath: string): Promise<any> {
  try {
    const blob = bucket.file(filePath);
    const [exists] = await blob.exists();
    
    if (!exists) {
      return {
        status: 'error',
        message: `File '${filePath}' not found`
      };
    }
    
    const [metadata] = await blob.getMetadata();
    return {
      status: 'success',
      metadata: metadata
    };
  } catch (error: any) {
    return {
      status: 'error',
      message: `Failed to get metadata: ${error.message}`
    };
  }
}
