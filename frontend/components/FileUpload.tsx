"use client";

import React, { useRef, useState } from "react";
import { CollectorReport } from "@/lib/types";
import { SAMPLE_REPORTS } from "@/lib/sampleData";

interface FileUploadProps {
  onReportLoaded: (report: CollectorReport, name: string) => void;
  isLoading: boolean;
}

export function FileUpload({ onReportLoaded, isLoading }: FileUploadProps) {
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = (file: File) => {
    setError(null);
    if (!file.name.endsWith(".json")) {
      setError("Please upload a valid JSON report file (e.g. report.json).");
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const text = e.target?.result as string;
        const parsed = JSON.parse(text) as CollectorReport;
        onReportLoaded(parsed, file.name);
      } catch (err) {
        setError("Invalid JSON format. Could not parse telemetry report.");
      }
    };
    reader.readAsText(file);
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  return (
    <div className="w-full my-6">
      {/* Minimal Dashed Drop Zone */}
      <div
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`border border-dashed p-8 text-center cursor-pointer transition ${
          dragActive
            ? "border-[#4A6FA5] bg-stone-100/60"
            : "border-stone-300 hover:border-stone-400 bg-stone-50/50"
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".json"
          className="hidden"
          onChange={(e) => {
            if (e.target.files?.[0]) handleFile(e.target.files[0]);
          }}
        />

        <div className="max-w-sm mx-auto">
          <p className="text-sm font-medium text-[#1A1A1A] mb-1">
            Upload Diagnostic Telemetry File
          </p>
          <p className="text-xs text-stone-500 mb-3">
            Drop your <code className="font-mono text-stone-700 bg-stone-200/60 px-1 py-0.5 rounded">report.json</code> file here, or click to choose file.
          </p>

          <button
            type="button"
            className="px-3.5 py-1.5 bg-[#4A6FA5] hover:bg-[#3B5984] text-white text-xs font-medium transition cursor-pointer"
          >
            Select report.json
          </button>
        </div>
      </div>

      {error && (
        <div className="mt-3 text-xs text-stone-800 bg-stone-100 p-2.5 border border-stone-300">
          {error}
        </div>
      )}

      {/* Preset Demo Reports */}
      <div className="mt-6 pt-4 border-t border-stone-200">
        <p className="text-xs text-stone-500 mb-2">
          Or view sample diagnostic reports:
        </p>

        <div className="flex flex-col sm:flex-row gap-2">
          {Object.entries(SAMPLE_REPORTS).map(([key, item]) => (
            <button
              key={key}
              disabled={isLoading}
              onClick={() => onReportLoaded(item.report, `${item.label}.json`)}
              className="text-left py-2 px-3 border border-stone-200 hover:border-stone-400 bg-white text-xs text-stone-700 hover:text-[#1A1A1A] transition disabled:opacity-50 cursor-pointer"
            >
              <div className="font-semibold text-stone-800">{item.label}</div>
              <div className="text-[11px] text-stone-500 truncate max-w-xs">
                {item.description}
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
