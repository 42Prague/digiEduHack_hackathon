import { Storage, Bucket, File } from '@google-cloud/storage';
import mime from 'mime-types';
import { Readable } from 'stream';

/**
 * Define GCSMetadata based on the 'metadata' property of the exported File object.
 * This provides strong typing without needing to manually define the interface.
 */
type GCSMetadata = File['metadata'];

/**
 * Configuration interface for the GCS Manager.
 */
export interface GCSConfig {
  projectId: string;
  keyFilename: string;
  bucketName: string;
}

/**
 * Interface for file metadata returned by list and upload operations.
 */
export interface FileDetails {
  name: string;
  size: number;
  contentType: string | null;
  created: string | null;
  updated: string | null;
}

/**
 * Helper function to determine content type.
 */
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
 * Manages CRUD operations for a Google Cloud Storage bucket.
 */
export class GCSManager {
  private storage: Storage;
  private bucket: Bucket;

  constructor(config: GCSConfig) {
    this.storage = new Storage({
      projectId: config.projectId,
      keyFilename: config.keyFilename,
    });
    this.bucket = this.storage.bucket(config.bucketName);
  }

  /**
   * Constructs the full path (blob name) for a file in the bucket.
   */
  private constructBlobName(filename: string, folder?: string): string {
    if (folder) {
      // Normalize folder path (remove leading/trailing slashes)
      return `${folder.replace(/^\/+|\/+$/g, '')}/${filename}`;
    }
    return filename;
  }

  /**
   * Helper to format GCS metadata into FileDetails interface.
   */
  private formatMetadata(metadata: GCSMetadata): FileDetails {
    // We use nullish coalescing (??) for safety.
    return {
      name: metadata.name ?? '',
      // The size property in GCS API metadata is typically returned as a string.
      // We ensure it's treated as a string before parsing.
      size: metadata.size ? parseInt(String(metadata.size), 10) : 0,
      contentType: metadata.contentType ?? null,
      created: metadata.timeCreated ?? null,
      updated: metadata.updated ?? null,
    };
  }

  /**
   * CREATE / UPDATE: Uploads a file to the GCS bucket.
   * If the file already exists, it will be overwritten.
   *
   * @param filename The name of the file.
   * @param buffer The file content as a Buffer.
   * @param folder Optional folder path within the bucket.
   * @param contentType Optional explicit content type.
   */
  public async uploadFile(
    filename: string,
    buffer: Buffer,
    folder?: string,
    contentType?: string
  ): Promise<FileDetails> {
    const blobName = this.constructBlobName(filename, folder);
    const finalContentType = getContentType(filename, contentType);
    const blob = this.bucket.file(blobName);

    return new Promise((resolve, reject) => {
      const blobStream = blob.createWriteStream({
        // Set resumable to false when uploading from a buffer already in memory.
        resumable: false,
        metadata: {
          contentType: finalContentType,
        },
      });

      blobStream.on('error', (err) => {
        console.error('GCS Upload error:', err);
        reject(new Error(`Upload failed: ${err.message}`));
      });

      blobStream.on('finish', async () => {
        // Fetch metadata after upload to confirm details.
        // The metadata returned here conforms to GCSMetadata.
        try {
          const [metadata] = await blob.getMetadata();
          resolve(this.formatMetadata(metadata));
        } catch (metaError: any) {
          reject(new Error(`Upload finished, but failed to fetch metadata: ${metaError.message}`));
        }
      });

      blobStream.end(buffer);
    });
  }

  /**
   * READ: Downloads a file from the GCS bucket as a Buffer.
   *
   * @param filePath The full path to the file in the bucket (e.g., "folder/file.txt").
   */
  public async downloadFileAsBuffer(filePath: string): Promise<Buffer> {
    const blob = this.bucket.file(filePath);

    try {
      const [data] = await blob.download();
      return data;
    } catch (error: any) {
      // Handle specific GCS error codes
      if (error.code === 404) {
        throw new Error(`File '${filePath}' not found`);
      }
      throw error;
    }
  }

  /**
   * READ: Creates a readable stream for a file in the GCS bucket.
   * Useful for piping large files (e.g., directly to an HTTP response).
   *
   * @param filePath The full path to the file in the bucket.
   */
  public async getFileStream(filePath: string): Promise<{ stream: Readable, metadata: FileDetails }> {
    const blob = this.bucket.file(filePath);

    // Fetch metadata first to ensure the file exists and to get details like Content-Type.
    try {
      const [metadata] = await blob.getMetadata();
      const stream = blob.createReadStream();
      return { stream, metadata: this.formatMetadata(metadata) };
    } catch (error: any) {
      if (error.code === 404) {
        throw new Error(`File '${filePath}' not found`);
      }
      throw error;
    }
  }

  /**
   * READ: Lists files in the GCS bucket.
   *
   * @param prefix Optional prefix to filter files (e.g., a folder path).
   */
  public async listFiles(prefix?: string): Promise<FileDetails[]> {
    const [files] = await this.bucket.getFiles({ prefix });

    // The metadata is included in the File object (file.metadata).
    // We filter to ensure metadata exists before formatting.
    return files.filter(file => file.metadata).map(file => this.formatMetadata(file.metadata));
  }

  /**
   * DELETE: Deletes a file from the GCS bucket.
   *
   * @param filePath The full path to the file in the bucket.
   */
  public async deleteFile(filePath: string): Promise<void> {
    const blob = this.bucket.file(filePath);

    try {
      // By default, this throws an error if the file does not exist.
      await blob.delete();
    } catch (error: any) {
      if (error.code === 404) {
        throw new Error(`File '${filePath}' not found`);
      }
      throw error;
    }
  }
}