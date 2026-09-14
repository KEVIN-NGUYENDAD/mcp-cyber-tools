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
    "Find alternate data streams (ADS) in the folders where they actually appear",
    {
      path: z.string().optional(),
      limit: z.coerce.number().optional()
    },
    async ({ path, limit = 200 }) => {
      // Mac dinh cu la "C:\\", va `Get-Item -Path "C:\\" -Stream *` chi soi DUNG
      // MOT muc: chinh thu muc goc. No khong de quy, khong nhin vao file nao ca.
      // Nen tool nay khong bao gio tim duoc ADS o bat cu dau — no luon tra ve
      // rong, va cai rong do bi doc nham thanh "may sach".
      //
      // Mac dinh moi: dung nhung thu muc ma ADS thuc su xuat hien — file tai ve
      // mang Zone.Identifier, va %TEMP% la noi thu duoc tha xuong. Quet ca o dia
      // thi dung han trong 30 giay, nen pham vi phai co gioi han va phai noi ro.
      const targets = path
        ? [path]
        : ["$env:USERPROFILE\\Downloads", "$env:USERPROFILE\\Desktop",
           "$env:USERPROFILE\\Documents", "$env:TEMP"];
      const psList = targets.map(t => `"${t}"`).join(", ");

      const result = runPowerShell(`
        $ErrorActionPreference = 'SilentlyContinue'
        $scanned = New-Object System.Collections.ArrayList
        $rows = New-Object System.Collections.ArrayList

        foreach ($target in @(${psList})) {
          $full = $ExecutionContext.InvokeCommand.ExpandString($target)
          if (-not (Test-Path $full)) { continue }
          [void]$scanned.Add($full)
          $items = if ((Get-Item $full -ErrorAction SilentlyContinue).PSIsContainer) {
            Get-ChildItem -Path $full -File -Recurse -Depth 2 -Force -ErrorAction SilentlyContinue
          } else {
            Get-Item -Path $full -ErrorAction SilentlyContinue
          }
          foreach ($item in $items) {
            Get-Item -Path $item.FullName -Stream * -ErrorAction SilentlyContinue |
              Where-Object { $_.Stream -ne ':$DATA' } |
              ForEach-Object {
                [void]$rows.Add([PSCustomObject]@{
                  File = $item.FullName
                  Stream = [string]$_.Stream
                  Length = [int64]$_.Length
                  # Zone.Identifier la dau vet tai tu mang — rat pho bien va gan
                  # nhu luon vo hai. Danh dau no thay vi loc bo: mot tool ten la
                  # "tim ADS" phai tim ra ADS, viec phan xet la cua cuoc san.
                  IsZoneIdentifier = ([string]$_.Stream -eq 'Zone.Identifier')
                })
              }
          }
        }

        $limited = @($rows | Select-Object -First ${limit})
        [PSCustomObject]@{
          ScannedPaths = @($scanned)
          Total = $rows.Count
          Streams = $limited
        } | ConvertTo-Json -Depth 5 -Compress
        exit 0
      `);

      if (!result.success) return formatResponse(result.success, result.data, result.error);

      let payload = null;
      try {
        payload = JSON.parse(result.data);
      } catch (error) {
        return formatResponse(false, "", `Khong phan tich duoc ket qua ADS: ${error.message}`);
      }

      const streams = payload.Streams || [];
      const unusual = streams.filter(s => !s.IsZoneIdentifier);
      return formatResponse(true, JSON.stringify({
        scannedPaths: payload.ScannedPaths || [],
        total: payload.Total,
        returned: streams.length,
        truncated: payload.Total > streams.length,
        zoneIdentifierCount: streams.length - unusual.length,
        unusualCount: unusual.length,
        summary: `${payload.Total} ADS tren ${(payload.ScannedPaths || []).length} thu muc; `
          + `${unusual.length} khong phai Zone.Identifier`,
        streams
      }, null, 2));
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

