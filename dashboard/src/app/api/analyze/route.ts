import { NextResponse } from 'next/server';
import { writeFile, unlink, mkdir } from 'fs/promises';
import { existsSync } from 'fs';
import path from 'path';
import { spawn } from 'child_process';
import os from 'os';

const UPLOAD_DIR = path.join(os.tmpdir(), 'claimvision_uploads');
const ALLOWED_MIME_TYPES = ['image/jpeg', 'image/png', 'image/webp'];

function getPythonCommand() {
  return os.platform() === 'win32' ? 'py' : 'python3';
}

export async function POST(req: Request) {
  try {
    console.log("[Analyze API] Received request.");
    const formData = await req.formData();
    
    const user_claim = formData.get('user_claim') as string;
    const claim_object = formData.get('claim_object') as string;
    const files = formData.getAll('images') as File[];

    console.log(`[Analyze API] claim_object: ${claim_object}, user_claim: ${user_claim}`);
    
    if (!user_claim || !claim_object) {
      console.error("[Analyze API] Missing claim details.");
      return NextResponse.json({ error: 'Missing claim details.' }, { status: 400 });
    }

    if (!files || files.length === 0) {
      console.error("[Analyze API] No images uploaded.");
      return NextResponse.json({ error: 'No images uploaded.' }, { status: 400 });
    }

    if (!existsSync(UPLOAD_DIR)) {
      console.log(`[Analyze API] Creating temp upload dir: ${UPLOAD_DIR}`);
      await mkdir(UPLOAD_DIR, { recursive: true });
    }

    const savedPaths: string[] = [];

    // Validation & Save
    for (const file of files) {
      console.log(`[Analyze API] Processing file: ${file.name} (${file.type}, ${file.size} bytes)`);
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
      console.log(`[Analyze API] Saved temp file to: ${filePath}`);
    }

    // Call Python script
    const payload = {
      user_id: 'demo_user',
      user_claim,
      claim_object,
      image_paths: savedPaths.join(';')
    };

    const pythonScript = path.resolve(process.cwd(), '..', 'code', 'live_predict.py');
    const pythonCmd = getPythonCommand();
    console.log(`[Analyze API] Spawning python: ${pythonCmd} ${pythonScript}`);

    return new Promise<NextResponse>((resolve) => {
      const pyProcess = spawn(pythonCmd, [pythonScript]);
      let dataString = '';
      let errorString = '';

      pyProcess.stdout.on('data', (data) => {
        dataString += data.toString();
      });

      pyProcess.stderr.on('data', (data) => {
        errorString += data.toString();
        console.error(`[Python STDERR]: ${data.toString().trim()}`);
      });

      pyProcess.on('error', async (error) => {
        console.error(`[Analyze API] Failed to spawn Python process:`, error);
        // Cleanup temp files
        for (const filePath of savedPaths) {
          try { await unlink(filePath); } catch (e) {}
        }
        resolve(NextResponse.json({ error: `Backend failure: Could not start Python process. (${error.message})` }, { status: 500 }));
      });

      pyProcess.on('close', async (code) => {
        console.log(`[Analyze API] Python process exited with code ${code}`);
        
        // Cleanup temp files
        for (const filePath of savedPaths) {
          try {
            await unlink(filePath);
            console.log(`[Analyze API] Deleted temp file: ${filePath}`);
          } catch (e) {
            console.error(`[Analyze API] Failed to delete temp file: ${filePath}`, e);
          }
        }

        try {
          // If no stdout at all but there is stderr
          if (!dataString.trim() && errorString.trim()) {
            resolve(NextResponse.json({ error: `Python execution failed. Details: ${errorString.substring(0, 200)}...` }, { status: 500 }));
            return;
          }

          const result = JSON.parse(dataString);
          if (result.error) {
             console.error(`[Analyze API] Received explicit error from Python: ${result.error}`);
             resolve(NextResponse.json({ error: result.error }, { status: 400 }));
          } else {
             console.log(`[Analyze API] Sending successful result back to client.`);
             resolve(NextResponse.json(result));
          }
        } catch (err: any) {
          console.error("[Analyze API] Failed to parse Python output", err, "RAW:", dataString);
          const excerpt = errorString ? errorString.substring(0, 300) : "No stderr available.";
          resolve(NextResponse.json({ error: `Internal server error. Failed to parse AI analysis. Check backend logs. Python stderr: ${excerpt}` }, { status: 500 }));
        }
      });

      // Write payload to stdin
      try {
        pyProcess.stdin.write(JSON.stringify(payload));
        pyProcess.stdin.end();
      } catch (err: any) {
        console.error("[Analyze API] Failed to write to stdin", err);
      }
    });

  } catch (error: any) {
    console.error("[Analyze API] Unhandled API route error:", error);
    return NextResponse.json({ error: `Failed to process request: ${error.message}` }, { status: 500 });
  }
}
