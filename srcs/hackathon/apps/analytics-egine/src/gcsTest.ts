import {GCSManager, type GCSConfig} from "./gcsManager.js"; // Adjust the import path as needed

// Configuration (ideally loaded from environment variables)
const config: GCSConfig = {
  projectId: '1015067005262', // Use the Project ID from your setup
  bucketName: 'eduzmena',
  // IMPORTANT: Ensure the path to your service account key file is correct
  keyFilename: './so-concrete.json',
};

// Initialize the manager
const gcsManager = new GCSManager(config);

async function main() {
  try {
    // 1. Create/Update (Upload)
    const fileContent = Buffer.from('Hello, GCP!', 'utf-8');
    const uploadResult = await gcsManager.uploadFile('example.txt', fileContent, 'test-folder');
    console.log('File uploaded:', uploadResult);

    // 2. Read (List)
    const files = await gcsManager.listFiles('test-folder/');
    console.log('Files in test-folder:', files);

    // 3. Read (Download as Buffer)
    const downloadedData = await gcsManager.downloadFileAsBuffer('test-folder/example.txt');
    console.log('Downloaded content:', downloadedData.toString('utf-8'));

    // 4. Delete
    await gcsManager.deleteFile('test-folder/example.txt');
    console.log('File deleted successfully.');

  } catch (error) {
    console.error('An error occurred:', error);
  }
}

await main();