# PROJECT READY STATE

**Ngày:** 2026-09-15
**Chế độ:** Production Monitoring (freeze)

Tệp này viết tay và là nguồn sự thật cho chiến lược runtime. `HANDOFF.md` được
`scripts/generate_handoff.py` ghi đè mỗi lần chạy, nên mọi quyết định lâu dài
nằm ở đây.

---

## Runtime Strategy

### PRIMARY

`sentinel_agent.exe`

- Self-contained: nhúng sẵn Node v22.23.2, không cần Node.js cài trên máy đích.
- UI (`index.html`, `app.js`) nhúng trong snapshot của pkg.
- `state/` và `daily_brief/` đọc từ đĩa thật cạnh `.exe` (qua `process.execPath`),
  không phải từ snapshot.
- Độc lập với thư mục làm việc — chạy được từ bất kỳ đâu.
- Build: `npm run build:agent` (esbuild ESM→CJS, rồi pkg `node22-win-x64`).

### FALLBACK

`sentinel_agent.cmd`

- Batch wrapper gọi `node web/server.js`.
- **Yêu cầu:** Node.js trên PATH + cây `web/` và `node_modules/` còn nguyên.
- Tự dò được cả hai layout: cài đặt (`{app}\web\`) và repo (`dist\..\web\`).
- Chỉ dùng khi `.exe` không khởi động được. Wrapper in cảnh báo khi chạy.

### Fallback Removal Criteria

Xoá `sentinel_agent.cmd` khi **cả ba** điều kiện dưới đây đạt:

| # | Tiêu chí | Trạng thái |
|---|---|---|
| 1 | 7 ngày Production Monitoring | Bắt đầu 2026-09-15 |
| 2 | 0 lần cần dùng fallback | Chưa đo |
| 3 | 0 crash của `sentinel_agent.exe` | Chưa đo |

Sớm nhất có thể xoá: **2026-09-22**.

Nếu có bất kỳ lần dùng fallback hoặc crash nào, đồng hồ 7 ngày reset và phải
ghi nguyên nhân vào `docs/project/AUDIT_QUEUE.md` trước.

---

## Packaging

| Thành phần | Nguồn |
|---|---|
| Entry point | `web/server.js` |
| Bundle trung gian | `dist/bundle.cjs` (esbuild, CJS) |
| Executable | `dist/sentinel_agent.exe` (~89.6 MB) |
| Installer | `installer.iss` — ship cả PRIMARY lẫn FALLBACK |
| Startup task | `schtasks /tn SentinelOpsAgent` → trỏ vào `.exe` |

**Lưu ý phát hành:**

- `dist/` nằm trong `.gitignore` (dòng 45) → `.exe` **không** được commit.
  Phát hành qua release artifact, không qua git.
- pkg build **không** byte-deterministic: hai lần build cho hai SHA256 khác
  nhau. SHA256 công bố phải lấy từ đúng artifact được phát hành.
- Phải chạy `npm run build:agent` **trước** khi compile `installer.iss`, nếu
  không Inno Setup sẽ báo thiếu `dist\sentinel_agent.exe`.

### Vì sao phải bundle ESM→CJS

Project là `"type": "module"`. Snapshot filesystem của pkg chỉ hook CommonJS
`require`; ESM loader của Node bỏ qua hook đó hoàn toàn, nên `import` một đường
dẫn trong snapshot luôn hỏng với `ERR_MODULE_NOT_FOUND`. Đây là giới hạn kiến
trúc của pkg, không phải thiếu công cụ build. Cách xử lý: esbuild bundle sang
CJS + shim `import.meta.url` trước khi đưa vào pkg.

Target phải là `node22-win-x64`. `node18-win-x64` không có prebuilt → pkg tự
build Node từ source → cần `patch` + MSVC, cả hai đều không có trên máy build.
