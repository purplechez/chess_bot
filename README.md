# Embedded Browser Proxy (pnpm)

This small project provides an "embedded browser" UI served on port 8080 and a proxy endpoint at `/proxy` that fetches target pages and rewrites links so they can be displayed inside an iframe.

Quick start (requires pnpm and Node 18+):

```bash
pnpm install
pnpm start
# then open http://localhost:8080
```

Notes and limitations:
- This is a simple demo proxy. Sites that rely heavily on client-side navigation, complex CSPs, or websockets may not work.
- Some sites set authentication or overlay protections; use responsibly and respect terms of service.
- The proxy rewrites common attributes (href, src, srcset, form actions) but may miss edge cases.

If you want an Electron-based embedded browser (desktop Chromium), say so and I can scaffold an Electron app instead.
