import React, { useState } from 'react';
import { Upload, Database, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { db } from '../lib/firebase';
import { doc, setDoc, collection, writeBatch } from 'firebase/firestore';
import { cn } from '../lib/utils';

export const DataImporter: React.FC = () => {
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setStatus('loading');
    setError(null);
    setProgress(0);

    const reader = new FileReader();
    reader.onload = async (e) => {
      try {
        const json = JSON.parse(e.target?.result as string);
        const nodes = json.nodes || [];

        if (nodes.length === 0) throw new Error("No nodes found in JSON file.");

        let batch = writeBatch(db);
        let count = 0;
        const BATCH_SIZE = 100; // Safer batch size for large imports with subcollections

        for (const node of nodes) {
          const { id, citations, ...nodeData } = node;
          const nodeId = id || `node_${count}`;
          const nodeRef = doc(db, 'nodes', nodeId);
          
          batch.set(nodeRef, {
            ...nodeData,
            updatedAt: new Date().toISOString()
          });

          if (citations && Array.isArray(citations)) {
            for (const cit of citations) {
              const citRef = doc(collection(db, `nodes/${nodeId}/citations`));
              batch.set(citRef, cit);
            }
          }

          count++;
          if (count % BATCH_SIZE === 0) {
            await batch.commit();
            // Small delay to prevent write stream exhaustion
            await new Promise(resolve => setTimeout(resolve, 200));
            batch = writeBatch(db);
            setProgress(Math.round((count / nodes.length) * 100));
          }
        }

        await batch.commit();
        setProgress(100);
        setStatus('success');
      } catch (err) {
        console.error(err);
        setError(err instanceof Error ? err.message : 'Failed to parse JSON');
        setStatus('error');
      }
    };
    reader.readAsText(file);
  };

  return (
    <div className="p-8 bg-slate-900/40 border border-slate-800 rounded-2xl">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-3 bg-blue-600/20 rounded-xl">
          <Database className="w-6 h-6 text-blue-400" />
        </div>
        <div>
          <h2 className="text-xl font-bold">Bulk Data Import</h2>
          <p className="text-xs text-slate-500">Upload your fitlib_export.json to sync 2000+ nodes.</p>
        </div>
      </div>

      <div className="relative group">
        <label className={cn(
          "flex flex-col items-center justify-center w-full h-40 border-2 border-dashed rounded-2xl cursor-pointer transition-all",
          status === 'loading' ? 'border-blue-500 bg-blue-500/5' : 
          status === 'success' ? 'border-green-500 bg-green-500/5' :
          'border-slate-800 bg-slate-950/50 hover:border-slate-700 hover:bg-slate-900/50'
        )}>
          <div className="flex flex-col items-center justify-center pt-5 pb-6">
            {status === 'loading' ? (
              <>
                <Loader2 className="w-10 h-10 text-blue-500 animate-spin mb-3" />
                <p className="text-sm text-blue-400 font-bold">Importing... {progress}%</p>
              </>
            ) : status === 'success' ? (
              <>
                <CheckCircle2 className="w-10 h-10 text-green-500 mb-3" />
                <p className="text-sm text-green-400 font-bold">Import Successful!</p>
                <p className="text-[10px] text-slate-500 mt-1">Database is now synced.</p>
              </>
            ) : (
              <>
                <Upload className="w-10 h-10 text-slate-600 mb-3 group-hover:text-blue-500 transition-colors" />
                <p className="text-sm text-slate-400 group-hover:text-slate-200">
                  <span className="font-bold">Click to upload</span> or drag and drop
                </p>
                <p className="text-[10px] text-slate-600 mt-1 uppercase tracking-widest">fitlib_export.json</p>
              </>
            )}
          </div>
          <input 
            type="file" 
            className="hidden" 
            accept=".json"
            onChange={handleFileUpload}
            disabled={status === 'loading'}
          />
        </label>

        {status === 'error' && (
          <div className="mt-4 p-4 bg-red-500/10 border border-red-500/20 rounded-xl flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-500 shrink-0" />
            <div className="text-xs text-red-400">
              <p className="font-bold mb-1">Import Failed</p>
              <p>{error}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
