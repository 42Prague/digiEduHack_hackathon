// app/api/interventions/route.ts

import { connectToHackathlonDB, closeMongo, CLOUD_COLLECTION_NAME } from "@/database";
import { Db } from 'mongodb';
import { NextRequest, NextResponse } from 'next/server'; // Import Next specific types
import z from 'zod';

// Define the Zod Schema (keep it the same)
const InterventionSchema = z.object({
  schoolName: z.string(),
  regionName: z.string(),
  guideName: z.string(),
  interventionType: z.string(),
  listOfParticipants: z.any().optional(), 
  attachedDocuments: z.array(z.string()).describe("Array of GCS blob names/paths"),
});

// Use a NAMED export for the POST method
export async function POST(req: NextRequest) {
  
  // 1. Get and validate the incoming data
  let body;
  try {
    body = await req.json();
  } catch (error) {
    return NextResponse.json({ message: 'Invalid JSON body' }, { status: 400 });
  }

//    const validationResult = InterventionSchema.safeParse(body);

   const validationResult = body;

//   if (!validationResult.success) {
//     console.error("Validation Error:", validationResult.error);
//     return NextResponse.json({ 
//         message: 'Invalid data format', 
//         errors: validationResult.error.format() 
//     }, { status: 400 });
//   }

//    const validatedData = validationResult.data;
   let db: Db | undefined;

   const validatedData = body;

  try {
    // 2. Connect to the Database
    db = await connectToHackathlonDB();
    if (!db) {
      throw new Error("Failed to connect to database");
    }
    const collection = db.collection(CLOUD_COLLECTION_NAME);

    // 3. Prepare the document for insertion
    // const filesForDB = validatedData.attachedDocuments.map(blobName => ({
    //     fileName: blobName,
    //     uploadedAt: new Date().toISOString(),
    // }));

    const docToInsert = {
        ...validatedData,
        // listOfFiles: {
        //     reports: filesForDB,
        // },
        createdAt: new Date(),
    };

    // 4. Insert into MongoDB
    const result = await collection.insertOne(docToInsert);
    
    // 5. Success response (using NextResponse)
    return NextResponse.json({ 
        message: 'Intervention successfully saved', 
        id: result.insertedId 
    }, { status: 201 });

  } catch (error) {
    console.error("Database Save Error:", error);
    return NextResponse.json({ message: 'Internal Server Error during data saving' }, { status: 500 });
  }
}