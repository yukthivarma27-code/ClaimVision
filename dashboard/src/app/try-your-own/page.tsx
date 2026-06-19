'use client';

import { useState } from 'react';

export default function TryYourOwnClaim() {
  const [images, setImages] = useState<File[]>([]);
  const [claimObject, setClaimObject] = useState('car');
  const [userClaim, setUserClaim] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setImages(Array.from(e.target.files));
    }
  };

  const handleAnalyze = async () => {
    if (!userClaim.trim() || images.length === 0) {
      setError('Please provide both images and a claim description.');
      return;
    }
    
    setLoading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append('claim_object', claimObject);
    formData.append('user_claim', userClaim);
    images.forEach(img => formData.append('images', img));

    try {
      const response = await fetch('/api/analyze', {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Failed to analyze claim.');
      }
      setResult(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <header className="mb-10">
        <h1 className="text-4xl font-extrabold tracking-tight mb-2 text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400">
          Try Your Own Claim
        </h1>
        <p className="text-neutral-400">Upload live multi-modal evidence to test the AI verification pipeline.</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
        {/* Input Panel */}
        <div className="bg-neutral-900 border border-neutral-800 rounded-2xl p-6 shadow-xl space-y-6">
          <div>
            <label className="block text-sm font-medium text-neutral-300 mb-2">Upload Evidence Images (JPEG/PNG/WEBP)</label>
            <input 
              type="file" 
              multiple 
              accept="image/jpeg, image/png, image/webp" 
              onChange={handleImageUpload}
              className="block w-full text-sm text-neutral-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-500/10 file:text-blue-400 hover:file:bg-blue-500/20"
            />
            {images.length > 0 && (
              <div className="mt-4 grid grid-cols-3 gap-2">
                {images.map((img, idx) => (
                  <div key={idx} className="relative aspect-square rounded-lg overflow-hidden border border-neutral-700">
                    <img src={URL.createObjectURL(img)} alt="Preview" className="object-cover w-full h-full" />
                  </div>
                ))}
              </div>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-neutral-300 mb-2">Claimed Object</label>
            <select 
              value={claimObject} 
              onChange={(e) => setClaimObject(e.target.value)}
              className="w-full bg-neutral-950 border border-neutral-800 text-neutral-200 rounded-lg p-3 outline-none focus:border-blue-500 transition-colors"
            >
              <option value="car">Car</option>
              <option value="laptop">Laptop</option>
              <option value="package">Package</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-neutral-300 mb-2">Claim Description</label>
            <textarea 
              rows={4}
              value={userClaim}
              onChange={(e) => setUserClaim(e.target.value)}
              placeholder="E.g., My front bumper has a huge dent."
              className="w-full bg-neutral-950 border border-neutral-800 text-neutral-200 rounded-lg p-3 outline-none focus:border-blue-500 transition-colors"
            />
          </div>

          <button 
            onClick={handleAnalyze} 
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-500 disabled:bg-blue-900/50 text-white font-bold py-3 px-4 rounded-xl transition-all shadow-lg shadow-blue-900/20"
          >
            {loading ? 'Analyzing Multimodal Evidence...' : 'Run AI Verification'}
          </button>
          
          {error && (
            <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm">
              {error}
            </div>
          )}
        </div>

        {/* Explanation Panel */}
        <div className="bg-neutral-900 border border-neutral-800 rounded-2xl p-6 shadow-xl">
          <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
            Investigation Report
          </h2>

          {result ? (
            <div className="space-y-6">
              <div className="flex justify-between items-start">
                <div>
                  <span className="text-neutral-500 text-sm block mb-1">Final Verdict</span>
                  <span className={`px-4 py-1.5 text-sm font-bold rounded-full ${
                    result.claim_status === 'supported' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 
                    result.claim_status === 'contradicted' ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' : 
                    'bg-slate-500/20 text-slate-400 border border-slate-500/30'
                  }`}>
                    {result.claim_status?.replace(/_/g, ' ').toUpperCase()}
                  </span>
                </div>
                <div className="text-right">
                  <span className="text-neutral-500 text-sm block mb-1">AI Confidence</span>
                  <span className={`text-lg font-bold ${(result.confidence ?? 1.0) >= 0.8 ? 'text-emerald-400' : (result.confidence ?? 1.0) >= 0.6 ? 'text-blue-400' : 'text-rose-400'}`}>
                    {((result.confidence ?? 1.0) * 100).toFixed(1)}%
                  </span>
                </div>
              </div>

              <div className="bg-neutral-950 p-4 rounded-xl border border-neutral-800">
                <span className="text-neutral-500 text-sm block mb-2">AI Reasoning</span>
                <p className="text-sm text-neutral-300">{result.claim_status_justification}</p>
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="bg-neutral-950 p-4 rounded-xl border border-neutral-800">
                  <span className="text-neutral-500 block mb-1">Detected Issue</span>
                  <span className="font-semibold text-neutral-200 capitalize">{result.issue_type?.replace(/_/g, ' ')}</span>
                </div>
                <div className="bg-neutral-950 p-4 rounded-xl border border-neutral-800">
                  <span className="text-neutral-500 block mb-1">Object Part</span>
                  <span className="font-semibold text-neutral-200 capitalize">{result.object_part?.replace(/_/g, ' ')}</span>
                </div>
              </div>

              <div className="bg-neutral-950 p-4 rounded-xl border border-neutral-800">
                <span className="text-neutral-500 block mb-2 text-sm">Risk Flags</span>
                <div className="flex flex-wrap gap-2">
                  {result.risk_flags === 'none' ? (
                    <span className="font-medium text-emerald-500 text-xs px-2 py-1 bg-emerald-500/10 rounded">No Risk Detected</span>
                  ) : (
                    result.risk_flags?.split(';').map((flag: string, idx: number) => (
                      <span key={idx} className="inline-block px-2 py-1 bg-rose-500/10 text-rose-400 rounded border border-rose-500/20 text-xs tracking-wide">
                        {flag.trim()}
                      </span>
                    ))
                  )}
                </div>
              </div>
              
              <div className="bg-neutral-950 p-4 rounded-xl border border-neutral-800">
                 <span className="text-neutral-500 block mb-2 text-sm">Evidence Sufficiency</span>
                 <p className="text-sm text-neutral-300">{result.evidence_standard_met_reason}</p>
              </div>
            </div>
          ) : (
            <div className="h-full min-h-[300px] flex flex-col items-center justify-center text-neutral-600 border-2 border-dashed border-neutral-800 rounded-xl">
              <svg className="w-12 h-12 mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
              <p>Upload evidence and run verification to see results.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
