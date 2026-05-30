"use client";

import { useState, useEffect } from "react";

export default function Home() {
  const [issueUrl, setIssueUrl] = useState("");
  const [githubToken, setGithubToken] = useState("");
  const [jobs, setJobs] = useState<any[]>([]);
  const [statusMessage, setStatusMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    // Fetch jobs periodically
    const fetchJobs = async () => {
      try {
        const res = await fetch("http://localhost:8000/api/jobs");
        if (res.ok) {
          const data = await res.json();
          setJobs(data.jobs || []);
        }
      } catch (e) {
        console.error("Failed to fetch jobs", e);
      }
    };
    fetchJobs();
    const interval = setInterval(fetchJobs, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setStatusMessage("");
    try {
      const res = await fetch("http://localhost:8000/api/fix", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          issue_url: issueUrl,
          github_token: githubToken,
          skip_tests: false,
          dry_run: true, // We will use dry_run to stop before PR
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        setStatusMessage(data.detail || data.error || "Failed to start job");
      } else {
        setStatusMessage("Job started! Tracking progress below...");
        setIssueUrl("");
      }
    } catch (err) {
      setStatusMessage("Error connecting to server.");
    }
    setIsLoading(false);
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 p-8 font-sans">
      <div className="max-w-6xl mx-auto space-y-8">
        
        {/* Header */}
        <header className="flex items-center justify-between border-b border-slate-700 pb-6">
          <h1 className="text-4xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-teal-400">
            RepoRepair 10/10
          </h1>
          <div className="text-sm text-slate-400">AI Engineer Agent Dashboard</div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Left Column: Input Form */}
          <div className="col-span-1 space-y-6">
            <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-xl">
              <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                🚀 Submit Task
              </h2>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-400 mb-1">GitHub PAT (Token)</label>
                  <input
                    type="password"
                    required
                    value={githubToken}
                    onChange={(e) => setGithubToken(e.target.value)}
                    placeholder="ghp_..."
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-slate-200 focus:ring-2 focus:ring-blue-500 outline-none"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-400 mb-1">Issue URL</label>
                  <input
                    type="url"
                    required
                    value={issueUrl}
                    onChange={(e) => setIssueUrl(e.target.value)}
                    placeholder="https://github.com/owner/repo/issues/123"
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-slate-200 focus:ring-2 focus:ring-blue-500 outline-none"
                  />
                </div>
                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 text-white font-bold py-3 px-4 rounded-lg transition-all transform hover:scale-[1.02] disabled:opacity-50 disabled:scale-100"
                >
                  {isLoading ? "Starting..." : "Run AI Agent"}
                </button>
              </form>
              {statusMessage && (
                <div className="mt-4 p-3 rounded-lg bg-slate-900 border border-blue-900 text-blue-300 text-sm">
                  {statusMessage}
                </div>
              )}
            </div>
          </div>

          {/* Right Column: Active Jobs & Reasoning */}
          <div className="col-span-1 lg:col-span-2 space-y-6">
            <h2 className="text-2xl font-bold border-b border-slate-700 pb-2">Active Jobs & Agent Reasoning</h2>
            
            {jobs.length === 0 ? (
              <div className="text-slate-500 italic p-8 text-center bg-slate-800 rounded-xl border border-slate-700">
                No jobs currently running. Submit an issue to see the agent in action!
              </div>
            ) : (
              <div className="space-y-6">
                {jobs.map((job) => (
                  <div key={job.job_id} className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden shadow-lg transition-all hover:border-slate-600">
                    <div className="p-5 border-b border-slate-700 bg-slate-800/50 flex justify-between items-center">
                      <div>
                        <h3 className="font-bold text-lg text-blue-300">{job.owner}/{job.repo} #{job.issue_number}</h3>
                        <div className="text-xs text-slate-400 mt-1">ID: {job.job_id}</div>
                      </div>
                      <div className={`px-3 py-1 rounded-full text-xs font-bold ${
                        job.status === 'completed' ? 'bg-green-900 text-green-300' :
                        job.status === 'error' ? 'bg-red-900 text-red-300' :
                        'bg-blue-900 text-blue-300 animate-pulse'
                      }`}>
                        {job.status.toUpperCase()}
                      </div>
                    </div>
                    
                    <div className="p-5 space-y-4">
                      {/* Current Progress Status */}
                      <div className="flex items-center gap-3">
                        <div className="w-2 h-2 rounded-full bg-teal-400 animate-ping"></div>
                        <span className="text-sm font-medium text-slate-300">{job.progress || "Initializing..."}</span>
                      </div>

                      {/* Agent Reasoning Blocks */}
                      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 mt-4">
                        {/* Planner */}
                        <div className={`p-4 rounded border transition-colors ${job.reasoning?.planner ? 'bg-slate-800 border-blue-500' : 'bg-slate-900 border-slate-700 opacity-50'}`}>
                          <div className="text-xs font-bold text-slate-400 mb-2">PLANNER</div>
                          {job.reasoning?.planner ? (
                            <div className="text-sm space-y-2">
                              <p className="text-blue-300 font-medium">Strategy formulated.</p>
                              <div className="text-xs text-slate-400 bg-slate-900 p-2 rounded max-h-32 overflow-y-auto">
                                {job.reasoning.planner.strategy}
                              </div>
                            </div>
                          ) : <div className="text-sm italic">Waiting...</div>}
                        </div>

                        {/* Searcher */}
                        <div className={`p-4 rounded border transition-colors ${job.reasoning?.searcher ? 'bg-slate-800 border-purple-500' : 'bg-slate-900 border-slate-700 opacity-50'}`}>
                          <div className="text-xs font-bold text-slate-400 mb-2">SEARCHER</div>
                          {job.reasoning?.searcher ? (
                            <div className="text-sm space-y-2">
                              <p className="text-purple-300 font-medium">Found {job.reasoning.searcher.files_found?.length || 0} files.</p>
                              <ul className="text-xs text-slate-400 list-disc list-inside">
                                {job.reasoning.searcher.files_found?.slice(0, 3).map((f: str, i: number) => <li key={i} className="truncate">{f}</li>)}
                                {(job.reasoning.searcher.files_found?.length || 0) > 3 && <li>...</li>}
                              </ul>
                            </div>
                          ) : <div className="text-sm italic">Waiting...</div>}
                        </div>

                        {/* Coder */}
                        <div className={`p-4 rounded border transition-colors ${job.reasoning?.coder ? 'bg-slate-800 border-orange-500' : 'bg-slate-900 border-slate-700 opacity-50'}`}>
                          <div className="text-xs font-bold text-slate-400 mb-2">CODER</div>
                          {job.reasoning?.coder ? (
                            <div className="text-sm space-y-2">
                              <p className="text-orange-300 font-medium">Generated patch.</p>
                              <ul className="text-xs text-slate-400">
                                {job.reasoning.coder.changes?.map((c: any, i: number) => (
                                  <li key={i} className="truncate">• {c.file} ({c.lines_changed > 0 ? '+' : ''}{c.lines_changed} lines)</li>
                                ))}
                              </ul>
                            </div>
                          ) : <div className="text-sm italic">Waiting...</div>}
                        </div>

                        {/* Validator */}
                        <div className={`p-4 rounded border transition-colors ${job.reasoning?.validator ? (job.reasoning.validator.success ? 'bg-slate-800 border-green-500' : 'bg-slate-800 border-red-500') : 'bg-slate-900 border-slate-700 opacity-50'}`}>
                          <div className="text-xs font-bold text-slate-400 mb-2">VALIDATOR</div>
                          {job.reasoning?.validator ? (
                            <div className="text-sm space-y-2">
                              <p className={job.reasoning.validator.success ? "text-green-400 font-medium" : "text-red-400 font-medium"}>
                                {job.reasoning.validator.success ? "Tests Passed ✅" : "Tests Failed ❌"}
                              </p>
                              <div className="text-xs text-slate-400 bg-slate-900 p-2 rounded max-h-24 overflow-y-auto whitespace-pre-wrap">
                                {job.reasoning.validator.output?.slice(0, 200)}...
                              </div>
                            </div>
                          ) : <div className="text-sm italic">Waiting...</div>}
                        </div>
                      </div>

                      {job.error && (
                        <div className="p-3 bg-red-950 border border-red-900 rounded-lg text-sm text-red-200 mt-4">
                          <strong>Error:</strong> {job.error}
                        </div>
                      )}
                      
                      {/* PR Preview Block */}
                      {job.status === 'completed' && job.files_changed && (
                        <div className="mt-6 p-4 border border-teal-800 bg-teal-950/30 rounded-lg">
                          <h4 className="font-bold text-teal-400 mb-2">Review Patches</h4>
                          <ul className="text-sm text-slate-300 list-disc list-inside mb-4">
                            {job.files_changed.map((f: string, i: number) => <li key={i}>{f}</li>)}
                          </ul>
                          {job.dry_run ? (
                            <div className="flex gap-3">
                              <button 
                                onClick={async () => {
                                  await fetch(`http://localhost:8000/api/jobs/${job.job_id}/approve`, { method: "POST" });
                                }}
                                className="bg-teal-600 hover:bg-teal-500 text-white px-4 py-2 rounded text-sm font-bold transition-colors">
                                Approve & Create PR
                              </button>
                              <button 
                                onClick={async () => {
                                  // Just a local dismiss for now, or could call a reject endpoint
                                  alert("Rejected patches.");
                                }}
                                className="bg-slate-700 hover:bg-slate-600 text-white px-4 py-2 rounded text-sm font-bold transition-colors">
                                Reject
                              </button>
                            </div>
                          ) : job.pr_url ? (
                            <div className="text-sm text-green-400 font-bold">
                              PR Created! <a href={job.pr_url} target="_blank" rel="noreferrer" className="underline">{job.pr_url}</a>
                            </div>
                          ) : null}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
