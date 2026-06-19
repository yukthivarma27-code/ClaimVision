import { NextResponse } from 'next/server';
import { writeFile, unlink, mkdir } from 'fs/promises';
import { existsSync } from 'fs';
import path from 'path';
import { spawn } from 'child_process';

const UPLOAD_DIR = path.join(process.cwd(), 'tmp_uploads');
const ALLOWED_MIME_TYPES = ['image/jpeg', 'image/png', 'image/webp'];

export async function POST(req: Request) {
  try {
    const formData = await req.formData();
    
    const user_claim = formData.get('user_claim') as string;
    const claim_object = formData.get('claim_object') as string;
    const files = formData.getAll('images') as File[];

    if (!user_claim || !claim_object) {
      return NextResponse.json({ error: 'Missing claim details.' }, { status: 400 });
    }

    if (!files || files.length === 0) {
      return NextResponse.json({ error: 'No images uploaded.' }, { status: 400 });
    }

    if (!existsSync(UPLOAD_DIR)) {
      await mkdir(UPLOAD_DIR, { recursive: true });
    }

    const savedPaths: string[] = [];

    // Validation & Save
    for (const file of files) {
      if (!ALLOWED_MIME_TYPES.includes(file.type)) {
        return NextResponse.json({ error: `Unsupported file format: ${file.type}. Allowed formats: JPEG, PNG, WEBP.` }, { status: 400 });
      }

      if (file.size === 0) {
        return NextResponse.json({ error: 'Corrupted or empty file uploaded.' }, { status: 400 });
      }

      const buffer = Buffer.from(await file.arrayBuffer());
      const uniqueName = `${Date.now()}_${file.name.replace(/[^a-zA-Z0-9.-]/g, '_')}`;
      const filePath = path.join(UPLOAD_DIR, uniqueName);
      
      await writeFile(filePath, buffer);
      savedPaths.push(filePath);
    }

    // Call Python script
    const payload = {
      user_id: 'demo_user',
      user_claim,
      claim_object,
      image_paths: savedPaths.join(';')
    };

    const pythonScript = path.join(process.cwd(), '..', 'code', 'live_predict.py');

    return new Promise<NextResponse>((resolve) => {
      const pyProcess = spawn('python', [pythonScript]);
      let dataString = '';

      pyProcess.stdout.on('data', (data) => {
        dataString += data.toString();
      });

      pyProcess.stderr.on('data', (data) => {
        console.error(`Python Error: ${data}`);
      });

      pyProcess.on('close', async (code) => {
        // Cleanup temp files
        for (const filePath of savedPaths) {
          try {
            await unlink(filePath);
          } catch (e) {
            console.error(`Failed to delete temp file: ${filePath}`, e);
          }
        }

        try {
          const result = JSON.parse(dataString);
          if (result.error) {
             resolve(NextResponse.json({ error: result.error }, { status: 400 }));
          } else {
             resolve(NextResponse.json(result));
          }
        } catch (err) {
          console.error("Failed to parse Python output", err, dataString);
          resolve(NextResponse.json({ error: 'Internal server error while processing AI analysis.' }, { status: 500 }));
        }
      });

      // Write payload to stdin
      pyProcess.stdin.write(JSON.stringify(payload));
      pyProcess.stdin.end();
    });

  } catch (error: any) {
    console.error("API error:", error);
    return NextResponse.json({ error: 'Failed to process request.' }, { status: 500 });
  }
}
