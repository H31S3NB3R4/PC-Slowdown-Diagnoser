"use client";

import React, { useState } from "react";
import { DiagnoseResponse } from "@/lib/types";
import { IssueCard } from "./IssueCard";

interface DiagnosticsDashboardProps {
  data: DiagnoseResponse;
  fileName: string;
  isAiRewrite: boolean;
  onToggleAiRewrite: () => void;
  onReset: () => void;
  isLoading: boolean;
}

export function DiagnosticsDashboard({
  data,
  fileName,
  isAiRewrite,
  onToggleAiRewrite,
  onReset,
  isLoading,
}: DiagnosticsDashboardProps) {
  const [severityFilter, setSeverityFilter] = useState<"all" | "high" | "medium" | "low">("all");

  const highCount = data.issues.filter((i) => i.severity === "high").length;
  const mediumCount = data.issues.filter((i) => i.severity === "medium").length;
  const lowCount = data.issues.filter((i) => i.severity === "low").length;

  const filteredIssues = data.issues.filter((issue) => {
    if (severityFilter === "all") return true;
    return issue.severity === severityFilter;
  });

  return (
    <div className="w-full">
      {/* Action & Filter Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 mb-4 border-b border-stone-200 text-xs">
        {/* Severity Filter Tabs */}
        <div className="flex items-center gap-4 text-stone-500 font-medium">
          <button
            onClick={() => setSeverityFilter("all")}
            className={`transition cursor-pointer ${
              severityFilter === "all" ? "text-[#1A1A1A] font-semibold underline underline-offset-4" : "hover:text-stone-800"
            }`}
          >
            All Findings ({data.issues.length})
          </button>
          <button
            onClick={() => setSeverityFilter("high")}
            className={`transition cursor-pointer ${
              severityFilter === "high" ? "text-[#1A1A1A] font-semibold underline underline-offset-4" : "hover:text-stone-800"
            }`}
          >
            High ({highCount})
          </button>
          <button
            onClick={() => setSeverityFilter("medium")}
            className={`transition cursor-pointer ${
              severityFilter === "medium" ? "text-[#1A1A1A] font-semibold underline underline-offset-4" : "hover:text-stone-800"
            }`}
          >
            Medium ({mediumCount})
          </button>
          <button
            onClick={() => setSeverityFilter("low")}
            className={`transition cursor-pointer ${
              severityFilter === "low" ? "text-[#1A1A1A] font-semibold underline underline-offset-4" : "hover:text-stone-800"
            }`}
          >
            Low ({lowCount})
          </button>
        </div>

        {/* Controls: AI Mode Toggle & Reset */}
        <div className="flex items-center gap-4">
          <button
            onClick={onToggleAiRewrite}
            disabled={isLoading}
            className="text-[#4A6FA5] hover:text-[#3B5984] hover:underline font-medium transition cursor-pointer disabled:opacity-50"
          >
            {isAiRewrite ? "View Raw Rules Engine Output" : "View Plain-English (AI) Output"}
          </button>

          <span className="text-stone-300">|</span>

          <button
            onClick={onReset}
            className="text-stone-500 hover:text-stone-800 hover:underline transition cursor-pointer"
          >
            Upload New File
          </button>
        </div>
      </div>

      {/* Flat List of Issues */}
      {filteredIssues.length === 0 ? (
        <div className="py-12 text-center text-xs text-stone-500 border-b border-stone-200">
          No diagnostic findings match the selected filter.
        </div>
      ) : (
        <div className="divide-y divide-stone-200">
          {filteredIssues.map((issue, idx) => (
            <IssueCard key={idx} issue={issue} index={idx} />
          ))}
        </div>
      )}

      {/* Report Footer Note */}
      <div className="mt-8 pt-4 border-t border-stone-200 flex items-center justify-between text-[11px] text-stone-400">
        <span>Report file: {fileName}</span>
        <span>
          {data.rewritten ? "Plain-English explanations active (Gemini 2.5)" : "Raw engine outputs active"}
        </span>
      </div>
    </div>
  );
}
