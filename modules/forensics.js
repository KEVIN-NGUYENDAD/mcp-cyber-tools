import { z } from "zod";
import fs from "fs";
import { execSync } from "child_process";
import { runPowerShell, formatResponse } from "./shared.js";

export function registerForensicsTools(server) {
  // 1. CHECKHASH
  server.tool(
    "checkHash",
    "Calculate SHA256 hash of file",
    {
      path: z.string()
    },
    async ({ path }) => {
      const result = runPowerShell(`Get-FileHash -Path "${path}" -Algorithm SHA256 | ConvertTo-Json`);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 2. READLOGFILE
  server.tool(
    "readLogFile",
    "Read content of log file",
    {
      path: z.string(),
      lines: z.coerce.number().optional()
    },
    async ({ path, lines = 100 }) => {
      try {
        const content = fs.readFileSync(path, "utf8");
        const allLines = content.split("\\n");
        const output = allLines.slice(-lines).join("\\n");
        return formatResponse(true, output);
      } catch (err) {
        return formatResponse(false, "", err.message);
      }
    }
  );

  // 3. FILEMETADATA
  server.tool(
    "fileMetadata",
    "Get file metadata (timestamps, size, permissions)",
    {
      path: z.string()
    },
    async ({ path }) => {
      const result = runPowerShell(`
        $file = Get-Item "${path}" -Force -ErrorAction SilentlyContinue;
        if ($file) {
          @{
            FullPath = $file.FullName;
            Size = $file.Length;
            CreationTime = $file.CreationTime;
            LastWriteTime = $file.LastWriteTime;
            LastAccessTime = $file.LastAccessTime;
            Attributes = $file.Attributes;
            Owner = (Get-Acl $file.FullName).Owner;
          } | ConvertTo-Json
        } else {
          "File not found"
        }
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 4. RECENTFILES
  server.tool(
    "recentFiles",
    "Get recently accessed files",
    {
      limit: z.coerce.number().optional()
    },
    async ({ limit = 50 }) => {
      const result = runPowerShell(`
        Get-ChildItem -Path "$env:APPDATA\\Microsoft\\Windows\\Recent" -ErrorAction SilentlyContinue |
        Sort-Object LastAccessTime -Descending |
        Select-Object -First ${limit} Name, LastAccessTime, FullName |
        ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 5. DOWNLOADSFOLDER
  server.tool(
    "downloadsFolder",
    "List files in Downloads folder",
    {
      limit: z.coerce.number().optional()
    },
    async ({ limit = 50 }) => {
      const result = runPowerShell(`
        Get-ChildItem -Path "$env:USERPROFILE\\Downloads" -Recurse -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First ${limit} FullName, Length, LastWriteTime |
        ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 6. DESKTOPFILES
  server.tool(
    "desktopFiles",
    "List files on Desktop",
    {},
    async () => {
      const result = runPowerShell(`
        Get-ChildItem -Path "$env:USERPROFILE\\Desktop" -Recurse -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object FullName, Length, LastWriteTime |
        ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 7. TEMPFILES
  server.tool(
    "tempFiles",
    "List files in TEMP directory",
    {
      limit: z.coerce.number().optional()
    },
    async ({ limit = 50 }) => {
      const result = runPowerShell(`
        Get-ChildItem -Path "$env:TEMP" -Recurse -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First ${limit} FullName, Length, LastWriteTime |
        ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 8. RECYCLEBIN
  server.tool(
    "recycleBin",
    "List files in Recycle Bin",
    {
      limit: z.coerce.number().optional()
    },
    async ({ limit = 50 }) => {
      const result = runPowerShell(`
        $shell = New-Object -ComObject Shell.Application;
        $recycleBin = $shell.NameSpace(10);
        $recycleBin.Items() |
        Select-Object -First ${limit} Name, Size |
        ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 9. ALTERNATEDATASTREAMS
  server.tool(
    "alternateDataStreams",
    "Find alternate data streams (ADS)",
    {
      path: z.string().optional()
    },
    async ({ path = "C:\\" }) => {
      const result = runPowerShell(`
        Get-Item -Path "${path}" -Stream * -ErrorAction SilentlyContinue |
        Where-Object { $_.Stream -ne ':$DATA' } |
        Select-Object PSPath, Stream, Length |
        ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );

  // 10. SUSPICIOUSEXECUTABLES
  server.tool(
    "suspiciousExecutables",
    "Find potentially suspicious executables",
    {
      path: z.string().optional()
    },
    async ({ path = "$env:USERPROFILE\\Downloads" }) => {
      const result = runPowerShell(`
        $suspExtensions = @('.exe', '.dll', '.scr', '.bat', '.cmd', '.vbs', '.ps1');
        Get-ChildItem -Path "${path}" -Recurse -ErrorAction SilentlyContinue |
        Where-Object { $_.Extension -in $suspExtensions } |
        Select-Object FullName, Length, LastWriteTime, @{Name='FileType';Expression={$_.Extension}} |
        ConvertTo-Json
      `);
      return formatResponse(result.success, result.data, result.error);
    }
  );
}

