import { connectToHackathlonDB, closeMongo, CLOUD_COLLECTION_NAME } from "@/database";
import { Db } from 'mongodb';
import { NextRequest, NextResponse } from 'next/server';

export async function GET(req: NextRequest) {
  let db: Db | undefined;

  try {
    // Connect to the Database
    db = await connectToHackathlonDB();
    if (!db) {
      throw new Error("Failed to connect to database");
    }
    const collection = db.collection(CLOUD_COLLECTION_NAME);

    // Fetch all interventions, sorted by most recent first
    const interventions = await collection
      .find({})
      .sort({ createdAt: -1 })
      .toArray();

    // Return the list of interventions
    return NextResponse.json({ 
      interventions,
      count: interventions.length 
    }, { status: 200 });

  } catch (error) {
    console.error("Database Fetch Error:", error);
    return NextResponse.json({ message: 'Internal Server Error during data fetching' }, { status: 500 });
  }
}

export async function POST(req: NextRequest) {
  let body;
  try {
    body = await req.json();
  } catch (error) {
    return NextResponse.json({ message: 'Invalid JSON body' }, { status: 400 });
  }

  let db: Db | undefined;
  const validatedData = body;

  try {
    db = await connectToHackathlonDB();
    if (!db) {
      throw new Error("Failed to connect to database");
    }
    const collection = db.collection(CLOUD_COLLECTION_NAME);

    const docToInsert = {
        ...validatedData,
        createdAt: new Date(),
    };

    const result = await collection.insertOne(docToInsert);
    
    return NextResponse.json({ 
        message: 'Intervention successfully saved', 
        id: result.insertedId 
    }, { status: 201 });

  } catch (error) {
    console.error("Database Save Error:", error);
    return NextResponse.json({ message: 'Internal Server Error during data saving' }, { status: 500 });
  }
}
