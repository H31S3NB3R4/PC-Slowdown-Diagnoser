"use client";

import React from "react";
import { Issue } from "@/lib/types";

interface IssueCardProps {
  issue: Issue;
  index: number;
}

export function IssueCard({ issue, index }: IssueCardProps) {
  // Quiet gray tonal scale & font weight for severity per spec:
  // High = dark gray (#171717 / font-semibold/bold)
  // Medium = mid gray (#525252 / font-medium)
  // Low = light gray (#737373 / font-normal)
  const getSeverityClasses = (severity: string) => {
    switch (severity) {
      case "high":
        return {
          titleWeight: "font-semibold text-stone-950",
          tagClass: "text-stone-900 font-semibold border-stone-400 bg-stone-100",
          label: "HIGH",
        };
      case "medium":
        return {
          titleWeight: "font-medium text-stone-800",
          tagClass: "text-stone-600 font-medium border-stone-300 bg-stone-50",
          label: "MEDIUM",
        };
      case "low":
      default:
        return {
          titleWeight: "font-normal text-stone-700",
          tagClass: "text-stone-500 font-normal border-stone-200 bg-stone-50",
          label: "LOW",
        };
    }
  };

  const sev = getSeverityClasses(issue.severity);

  return (
    <div className="py-5 border-b border-stone-200 last:border-b-0">
      {/* Header Line: Severity indicator + Issue Title + Evidence */}
      <div className="flex items-baseline justify-between gap-4 mb-1.5">
        <div className="flex items-baseline gap-2.5">
          <span className="text-xs font-mono text-stone-400">
            {String(index + 1).padStart(2, "0")}.
          </span>
          <h3 className={`text-base leading-snug ${sev.titleWeight}`}>
            {issue.issue}
          </h3>
        </div>

        <span className={`text-[10px] tracking-wider uppercase px-1.5 py-0.5 border ${sev.tagClass} shrink-0 font-mono`}>
          {sev.label}
        </span>
      </div>

      {/* Evidence Subtext */}
      <div className="text-xs text-stone-500 mb-3 pl-7 font-mono">
        Evidence: {issue.evidence}
      </div>

      {/* Recommended Solution Text Block */}
      <div className="pl-7 text-xs text-[#1A1A1A] leading-relaxed">
        <span className="font-semibold text-stone-700 block mb-0.5">
          Recommended Action:
        </span>
        <p className="text-stone-700">{issue.fix}</p>

        {/* Top Program Offenders (Plain Text) */}
        {issue.top_offenders && issue.top_offenders.length > 0 && (
          <div className="mt-2 text-[11px] text-stone-500">
            <span className="font-medium text-stone-600">Top processes: </span>
            <span className="font-mono text-stone-800">
              {issue.top_offenders.join(", ")}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
