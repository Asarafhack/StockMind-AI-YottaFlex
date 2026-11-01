import React, { useState } from 'react';
import { triggerGeneratorJob, fetchGeneratorJobStatus } from '../services/api';
import { Database, Play, CheckCircle2, ShieldCheck, Terminal, Cpu } from 'lucide-react';

export const DataGeneratorConsole: React.FC = () => {
  const [profile, setProfile] = useState<'starter' | 'full'>('starter');
  const [seed, setSeed] = useState<number>(20261022);
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<any | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [polling, setPolling] = useState<boolean>(false);

  const handleStartGeneration = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await triggerGeneratorJob(profile, seed);
      setJobId(res.job_id);
      setJobStatus(res);
      startPolling(res.job_id);
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Generation start failed');
    } finally {
      setLoading(false);
    }
  };

  const startPolling = (id: string) => {
    setPolling(true);
    const interval = setInterval(async () => {
      try {
        const status = await fetchGeneratorJobStatus(id);
        setJobStatus(status);
        if (status.status === 'COMPLETED' || status.status === 'FAILED') {
          clearInterval(interval);
          setPolling(false);
        }
      } catch (err) {
        clearInterval(interval);
        setPolling(false);
      }
    }, 1500);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
          <Database className="w-5 h-5 text-cyan-400" />
          Deterministic Synthetic Data Generation Console
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Generate starter or full scale datasets (up to 5,000 SKUs, 100 Locations, 1,000,000 Movements, 50,000 Orders) with verified fixed-seed reproducibility.
        </p>
      </div>

      <form onSubmit={handleStartGeneration} className="p-6 rounded-2xl bg-[#090e1d] border border-slate-800 shadow-xl space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-mono text-slate-400 mb-1">GENERATION PROFILE</label>
            <select
              value={profile}
              onChange={(e) => setProfile(e.target.value as any)}
              className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-xs font-mono text-white focus:outline-none focus:border-cyan-500"
            >
              <option value="starter">STARTER (100 SKUs, 10 Locations, 1,000 Movements, 100 Orders)</option>
              <option value="full">FULL SCALE (5,000 SKUs, 100 Locations, 1,000,000 Movements, 50,000 Orders)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-mono text-slate-400 mb-1">FIXED REPRODUCIBILITY SEED</label>
            <input
              type="number"
              value={seed}
              onChange={(e) => setSeed(Number(e.target.value))}
              className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-xs font-mono text-white focus:outline-none focus:border-cyan-500"
              required
            />
          </div>
        </div>

        <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 text-xs text-slate-400 space-y-2">
          <div className="flex items-center gap-2 text-cyan-400 font-mono text-xs">
            <CheckCircle2 className="w-4 h-4" />
            <span>Deterministic SHA-256 Guarantee</span>
          </div>
          <p>
            The identical seed produces byte-identical entity identifiers, dependency ordering, and verified checksums across Parquet, CSV, and SQL outputs.
          </p>
        </div>

        <button
          type="submit"
          disabled={loading || polling}
          className="w-full py-2.5 rounded-lg text-xs font-semibold bg-gradient-to-r from-cyan-600 to-blue-600 text-white hover:from-cyan-500 hover:to-blue-500 transition-all flex items-center justify-center gap-2 shadow-lg shadow-cyan-500/20"
        >
          <Play className="w-4 h-4 fill-current" />
          {polling ? 'Pipeline Actively Streaming Records...' : 'Execute Data Generation Pipeline'}
        </button>
      </form>

      {/* Progress View */}
      {jobStatus && (
        <div className="p-6 rounded-2xl bg-[#090e1d] border border-cyan-900/50 shadow-2xl space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <span className="text-[10px] font-mono text-cyan-400">ACTIVE TASK: {jobStatus.job_id}</span>
              <div className="text-sm font-bold text-white font-mono mt-0.5">
                STATUS: <span className={jobStatus.status === 'COMPLETED' ? 'text-emerald-400' : 'text-amber-400'}>{jobStatus.status}</span>
              </div>
            </div>
            <div className="text-right font-mono text-xs text-slate-400">
              {jobStatus.elapsed_seconds}s ELAPSED
            </div>
          </div>

          {/* Progress Bar */}
          <div className="space-y-1.5">
            <div className="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden">
              <div
                className="bg-cyan-500 h-full transition-all duration-300"
                style={{ width: `${jobStatus.progress_pct}%` }}
              ></div>
            </div>
            <div className="flex justify-between text-[11px] font-mono text-slate-400">
              <span>{jobStatus.message}</span>
              <span>{jobStatus.progress_pct}%</span>
            </div>
          </div>

          {jobStatus.records_generated && Object.keys(jobStatus.records_generated).length > 0 && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2">
              {Object.entries(jobStatus.records_generated).map(([k, v]: any) => (
                <div key={k} className="p-2.5 rounded bg-slate-900/80 border border-slate-800 text-center">
                  <div className="text-[10px] font-mono text-slate-400 uppercase">{k}</div>
                  <div className="text-sm font-bold text-white font-mono">{v.toLocaleString()}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
