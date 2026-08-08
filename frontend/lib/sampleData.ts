import { CollectorReport } from "./types";

export const SAMPLE_REPORTS: Record<string, { label: string; description: string; report: CollectorReport }> = {
  slow_pc: {
    label: "Critical Bottlenecks (Low RAM + Full Disk)",
    description: "Machine with 94% RAM used, spinning HDD, 8% disk space left, and 18 startup apps.",
    report: {
      collected_at: "2026-08-08T20:30:00Z",
      cpu: {
        model: "Intel Core i5-8250U CPU @ 1.60GHz",
        cores_logical: 8,
        usage_percent: 86.4,
        temp_celsius: 78.5,
      },
      ram: {
        total_gb: 8.0,
        used_percent: 94.2,
        top_processes: [
          { name: "chrome.exe", memory_mb: 2450 },
          { name: "ms-teams.exe", memory_mb: 1200 },
          { name: "antivirus_service.exe", memory_mb: 850 },
          { name: "slack.exe", memory_mb: 620 },
        ],
      },
      disk: {
        type: "HDD",
        total_gb: 465.0,
        free_percent: 8.5,
        read_write_speed: "Slow (Spinning disk)",
      },
      startup: {
        count: 18,
        programs: [
          { name: "Spotify.exe" },
          { name: "Steam.exe" },
          { name: "OneDrive.exe" },
          { name: "Discord.exe" },
          { name: "Cortana.exe" },
        ],
      },
      os: {
        name: "Microsoft Windows 11 Home",
        version: "10.0.22631",
        uptime_hours: 192.5,
        pending_updates: 14,
      },
      background: {
        process_count: 284,
        top_cpu_processes: [
          { name: "chrome.exe", cpu_percent: 42.1 },
          { name: "searchindexer.exe", cpu_percent: 24.0 },
        ],
      },
    },
  },
  startup_heavy: {
    label: "High Startup Apps & Old Uptime",
    description: "Machine running for 10 days straight with 16 background autostart programs.",
    report: {
      collected_at: "2026-08-08T18:00:00Z",
      cpu: {
        model: "AMD Ryzen 5 3600 6-Core Processor",
        cores_logical: 12,
        usage_percent: 45.0,
        temp_celsius: 62.0,
      },
      ram: {
        total_gb: 16.0,
        used_percent: 78.0,
        top_processes: [
          { name: "chrome.exe", memory_mb: 4100 },
          { name: "docker.exe", memory_mb: 3200 },
        ],
      },
      disk: {
        type: "SSD",
        total_gb: 512.0,
        free_percent: 24.0,
        read_write_speed: "Fast (NVMe SSD)",
      },
      startup: {
        count: 16,
        programs: [
          { name: "EpicGamesLauncher.exe" },
          { name: "Dropbox.exe" },
          { name: "Zoom.exe" },
          { name: "AdobeCreativeCloud.exe" },
        ],
      },
      os: {
        name: "Windows 10 Pro",
        version: "10.0.19045",
        uptime_hours: 245.0,
        pending_updates: 4,
      },
      background: {
        process_count: 195,
        top_cpu_processes: [
          { name: "chrome.exe", cpu_percent: 18.0 },
        ],
      },
    },
  },
  healthy_pc: {
    label: "Healthy PC (No Issues)",
    description: "Clean machine with fast SSD, 35% RAM usage, 2 startup apps, and recent restart.",
    report: {
      collected_at: "2026-08-08T20:00:00Z",
      cpu: {
        model: "Intel Core i7-13700K",
        cores_logical: 24,
        usage_percent: 12.5,
        temp_celsius: 42.0,
      },
      ram: {
        total_gb: 32.0,
        used_percent: 34.8,
        top_processes: [
          { name: "browser.exe", memory_mb: 850 },
        ],
      },
      disk: {
        type: "SSD",
        total_gb: 1024.0,
        free_percent: 68.2,
        read_write_speed: "Ultra Fast (NVMe Gen4)",
      },
      startup: {
        count: 2,
        programs: [{ name: "Windows Security" }],
      },
      os: {
        name: "Windows 11 Pro",
        version: "10.0.22631",
        uptime_hours: 14.2,
        pending_updates: 0,
      },
      background: {
        process_count: 98,
        top_cpu_processes: [
          { name: "system", cpu_percent: 2.1 },
        ],
      },
    },
  },
};
