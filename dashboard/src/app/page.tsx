import fs from 'fs';
import path from 'path';
import Papa from 'papaparse';

export const dynamic = 'force-dynamic';

export default async function Dashboard() {
  const csvPath = path.join(process.cwd(), '..', 'output.csv');
  let data: any[] = [];
  
  if (fs.existsSync(csvPath)) {
    const fileContent = fs.readFileSync(csvPath, 'utf-8');
    const parsed = Papa.parse(fileContent, { header: true, skipEmptyLines: true });
    data = parsed.data;
  }

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-50 font-sans p-8">
      <div className="max-w-7xl mx-auto">
        <header className="mb-10">
          <h1 className="text-4xl font-extrabold tracking-tight mb-2 text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400">
            ClaimVision
          </h1>
          <p className="text-neutral-400 mb-2 font-medium">AI-Powered Damage Claim Verification & Evidence Intelligence Platform</p>
          <p className="text-neutral-500 text-sm">Reviewing {data.length} processed multimodal claims.</p>
        </header>

        <div className="grid gap-6">
          {data.map((row, i) => (
            <div key={i} className="bg-neutral-900 border border-neutral-800 rounded-2xl p-6 shadow-xl transition-all hover:border-neutral-700">
              <div className="flex justify-between items-start mb-6">
                <div>
                  <h2 className="text-xl font-semibold mb-1 flex items-center gap-3">
                    Claim: {row.user_id}
                    <span className={`px-3 py-1 text-xs font-medium rounded-full ${row.claim_status === 'supported' ? 'bg-emerald-500/20 text-emerald-400' : row.claim_status === 'contradicted' ? 'bg-red-500/20 text-red-400' : 'bg-amber-500/20 text-amber-400'}`}>
                      {row.claim_status?.replace(/_/g, ' ').toUpperCase()}
                    </span>
                  </h2>
                  <p className="text-sm text-neutral-500">Object: <span className="text-neutral-300 font-medium capitalize">{row.claim_object}</span></p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs px-2 py-1 bg-neutral-800 rounded-md border border-neutral-700">Severity: {row.severity}</span>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div className="space-y-4">
                  <div className="bg-neutral-950/50 p-4 rounded-xl border border-neutral-800/50">
                    <h3 className="text-sm font-semibold text-neutral-400 mb-2">User Claim Transcript</h3>
                    <p className="text-sm text-neutral-300 whitespace-pre-wrap">{row.user_claim}</p>
                  </div>
                  
                  <div className="bg-neutral-950/50 p-4 rounded-xl border border-neutral-800/50">
                    <h3 className="text-sm font-semibold text-neutral-400 mb-2">VLM Reasoning</h3>
                    <p className="text-sm text-neutral-300 mb-3">{row.claim_status_justification}</p>
                    
                    <div className="grid grid-cols-2 gap-4 text-xs mt-4 pt-4 border-t border-neutral-800">
                      <div>
                        <span className="text-neutral-500 block mb-1">Issue Type</span>
                        <span className="font-medium">{row.issue_type}</span>
                      </div>
                      <div>
                        <span className="text-neutral-500 block mb-1">Object Part</span>
                        <span className="font-medium">{row.object_part}</span>
                      </div>
                      <div>
                        <span className="text-neutral-500 block mb-1">Risk Flags</span>
                        <span className="font-medium text-amber-400">{row.risk_flags}</span>
                      </div>
                      <div>
                        <span className="text-neutral-500 block mb-1">Supporting Images</span>
                        <span className="font-medium">{row.supporting_image_ids}</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="text-sm font-semibold text-neutral-400 mb-3">Submitted Evidence</h3>
                  <div className="grid grid-cols-2 gap-3">
                    {row.image_paths?.split(';').map((img: string, idx: number) => (
                      <div key={idx} className="relative aspect-video bg-neutral-800 rounded-xl overflow-hidden border border-neutral-700 flex items-center justify-center">
                        <img 
                          src={`/api/image?path=${encodeURIComponent(img)}`} 
                          alt={`Evidence ${idx + 1}`}
                          className="object-cover w-full h-full"
                        />
                        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-2">
                          <span className="text-[10px] text-neutral-300 truncate block">{img.split('/').pop()}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ))}
          
          {data.length === 0 && (
            <div className="text-center py-20 bg-neutral-900 border border-neutral-800 rounded-2xl">
              <p className="text-neutral-400">No data found. Please run the CLI pipeline to generate output.csv</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
