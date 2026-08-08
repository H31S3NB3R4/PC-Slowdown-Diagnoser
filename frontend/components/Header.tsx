"use client";

import React from "react";

export function Header() {
  const handleDownloadCollector = () => {
    const scriptContent = `@echo off
echo ================================================
echo      PC Slowdown Diagnoser Telemetry Collector
echo ================================================
echo Running diagnostic collector script...
python ..\\collector\\collect.py
echo.
echo Collection complete! Check report.json in collector folder.
pause
`;
    const blob = new Blob([scriptContent], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "run_diagnoser.bat";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <header className="w-full border-b border-stone-200 bg-[#FAFAF9]">
      <div className="max-w-3xl mx-auto px-4 py-5 flex items-center justify-between">
        <div>
          <h1 className="text-base font-semibold text-[#1A1A1A] tracking-tight">
            PC Diagnostic Report
          </h1>
          <p className="text-xs text-stone-500 font-normal">
            Deterministic Telemetry &amp; Analysis
          </p>
        </div>

        <button
          onClick={handleDownloadCollector}
          className="text-xs font-medium text-[#4A6FA5] hover:text-[#3B5984] hover:underline transition bg-transparent p-0 border-0 cursor-pointer"
        >
          Download Collector Script (.bat)
        </button>
      </div>
    </header>
  );
}
