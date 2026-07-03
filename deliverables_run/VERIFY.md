# VERIFY

Purpose: Steps an examiner should run to verify the deliverable is functional.

1) Docker verification (recommended)

   docker load -i docker_image.tar
   docker run --rm -p 8000:8000 --name smartglasses_demo smartglasses:deliverable

   curl -sS http://127.0.0.1:8000/health
   # Expected: JSON response similar to {"status":"ok","demo":"ready"}

   Example demo call:
   curl -sS "http://127.0.0.1:8000/demo/route?from=31.04,31.37"

2) Binary fallback (if no Docker)

   Linux/macOS:
     chmod +x bin/app_demo
     ./bin/app_demo --demo-mode

   Windows (PowerShell):
     .\bin\app_demo.exe --demo-mode

   Expected stdout: contains "DEMO READY" and the service listens on localhost:8000

3) Verify checksums and signature

   sha256sum -c checksums.sha256
   gpg --verify checksums.sha256.sig checksums.sha256

4) Decrypt full source (NDA required)

   gpg --output full_source.tar.gz --decrypt full_source_encrypted.tar.gpg
   tar -xzf full_source.tar.gz

If any step fails, collect logs and send to the author with the command output.
