"use client";

import React from "react";
import { CollectorReport } from "@/lib/types";

interface SystemOverviewProps {
  report: CollectorReport;
}

export function SystemOverview({ report }: SystemOverviewProps) {
  const ramUsed = report.ram?.used_percent ?? 0;
  const cpuUsed = report.cpu?.usage_percent ?? 0;
  const diskFree = report.disk?.free_percent ?? 100;
  const diskUsed = 100 - diskFree;
  const startupCount = report.startup?.count ?? 0;
  const uptimeHours = report.os?.uptime_hours ?? 0;
  const uptimeDays = (uptimeHours / 24).toFixed(1);

  return (
    <div className="border-b border-stone-200 pb-6 mb-6">
      <div className="text-xs font-semibold uppercase tracking-wider text-stone-500 mb-3">
        System Telemetry Summary
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-5 gap-4 text-xs text-[#1A1A1A]">
        <div>
          <span className="text-stone-500 block text-[11px]">RAM Usage</span>
          <span className="font-semibold text-sm">{ramUsed.toFixed(0)}%</span>
          <span className="text-stone-400 block text-[10px]">
            {report.ram?.total_gb ? `${report.ram.total_gb} GB` : ""}
          </span>
        </div>

        <div>
          <span className="text-stone-500 block text-[11px]">CPU Load</span>
          <span className="font-semibold text-sm">{cpuUsed.toFixed(0)}%</span>
          <span className="text-stone-400 block text-[10px] truncate">
            {report.cpu?.model ? report.cpu.model.split(" ")[0] : ""}
          </span>
        </div>

        <div>
          <span className="text-stone-500 block text-[11px]">Disk Space</span>
          <span className="font-semibold text-sm">{diskUsed.toFixed(0)}% used</span>
          <span className="text-stone-400 block text-[10px]">
            {diskFree}% free ({report.disk?.type || "Drive"})
          </span>
        </div>

        <div>
          <span className="text-stone-500 block text-[11px]">Autostart Programs</span>
          <span className="font-semibold text-sm">{startupCount} apps</span>
          <span className="text-stone-400 block text-[10px]">At boot</span>
        </div>

        <div>
          <span className="text-stone-500 block text-[11px]">System Uptime</span>
          <span className="font-semibold text-sm">{uptimeDays} days</span>
          <span className="text-stone-400 block text-[10px]">Continuous</span>
        </div>
      </div>
    </div>
  );
}
