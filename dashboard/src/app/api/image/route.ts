import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const imagePath = searchParams.get('path');

  if (!imagePath) {
    return new NextResponse('Path parameter is missing', { status: 400 });
  }

  // Ensure path is relative to dataset or absolute to workspace
  const rootDir = path.join(process.cwd(), '..');
  let absolutePath = imagePath;
  if (!path.isAbsolute(imagePath)) {
     absolutePath = path.join(rootDir, 'dataset', imagePath);
  }

  if (!fs.existsSync(absolutePath)) {
    return new NextResponse('Image not found', { status: 404 });
  }

  const ext = path.extname(absolutePath).toLowerCase();
  let contentType = 'image/jpeg';
  if (ext === '.png') contentType = 'image/png';
  else if (ext === '.webp') contentType = 'image/webp';
  else if (ext === '.gif') contentType = 'image/gif';

  const imageBuffer = fs.readFileSync(absolutePath);

  return new NextResponse(imageBuffer, {
    headers: {
      'Content-Type': contentType,
      'Cache-Control': 'public, max-age=31536000, immutable',
    },
  });
}
