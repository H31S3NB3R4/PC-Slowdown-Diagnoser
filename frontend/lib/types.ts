export interface Issue {
  issue: string;
  severity: "high" | "medium" | "low";
  evidence: string;
  fix: string;
  top_offenders: string[];
}

export interface DiagnoseResponse {
  collected_at: string | null;
  issue_count: number;
  issues: Issue[];
  rewritten: boolean;
  engine_version: string;
}

export interface CpuTelemetry {
  model?: string;
  cores_logical?: number;
  usage_percent?: number;
  temp_celsius?: number | null;
}

export interface RamTelemetry {
  total_gb?: number;
  used_percent?: number;
  top_processes?: Array<{ name: string; memory_mb?: number }>;
}

export interface DiskTelemetry {
  type?: string;
  total_gb?: number;
  free_percent?: number;
  read_write_speed?: string;
}

export interface StartupTelemetry {
  count?: number;
  programs?: Array<{ name: string }>;
}

export interface OsTelemetry {
  name?: string;
  version?: string;
  uptime_hours?: number;
  pending_updates?: number | null;
}

export interface BackgroundTelemetry {
  process_count?: number;
  top_cpu_processes?: Array<{ name: string; cpu_percent?: number }>;
}

export interface CollectorReport {
  collected_at?: string;
  cpu?: CpuTelemetry;
  ram?: RamTelemetry;
  disk?: DiskTelemetry;
  startup?: StartupTelemetry;
  os?: OsTelemetry;
  background?: BackgroundTelemetry;
  [key: string]: unknown;
}
