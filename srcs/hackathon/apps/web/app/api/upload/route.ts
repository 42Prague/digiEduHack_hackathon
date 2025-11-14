// [project]/apps/reg-form-ui/app/api/upload/route.ts

import { uploadFile } from './server';// <-- Verify this path!
import { NextResponse } from 'next/server';
// import * as formidable from 'formidable'; // No longer needed for this simplified approach
// import * as fs from 'fs/promises';     // No longer needed for this simplified approach
import * as path from 'path';

// You DO NOT need to export const config = { api: { bodyParser: false } } 
// when using request.formData() in the App Router.

// 🚨 FIX: Change 'export default async function handler(...)' 
// to the named export for the POST method.
export async function POST(request: Request) {
    try {
        // 1. Get FormData from the incoming request
        const data = await request.formData();
        
        // 2. Extract file and folder
        const file = data.get('file') as File | null;
        const folder = data.get('folder') as string | null;

        if (!file) {
            return NextResponse.json({ status: 'error', message: 'No file uploaded.' }, { status: 400 });
        }

        // 3. Convert the web File object to a Node.js Buffer
        const fileBuffer = Buffer.from(await file.arrayBuffer());
        const fileName = file.name;

        // 4. Call your GCS function
        const uploadResult = await uploadFile(
            fileBuffer,
            fileName,
            { folder: folder || undefined, contentType: file.type || undefined }
        );
        
        // 5. Respond to the client
        if (uploadResult.status === 'success') {
            return NextResponse.json({ 
                status: 'success', 
                message: uploadResult.message,
                blob_name: uploadResult.blobName, // Crucial reference for the client
            });
        } else {
            return NextResponse.json({ status: 'error', message: uploadResult.message }, { status: 500 });
        }

    } catch (error: any) {
        console.error('API Upload Error:', error);
        return NextResponse.json({ status: 'error', message: `Server error: ${error.message}` }, { status: 500 });
    }
}