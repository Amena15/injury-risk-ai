# Fix: Video Upload Timeout at 98% (Fetch Failed)

## Root Cause
- Base64 encoding makes video upload 33% larger (memory-heavy)
- No server-side timeout handling
- Default uvicorn worker timeout kills long-running requests
- Progress bar fake-stops at 98% (incrementing by 5% each 200ms) making it appear stuck

## Steps

### Step 1: [Backend] Add timeout handling to `main.py`
- Add `asyncio.timeout` wrapper around video processing
- Add file size validation before base64 decode
- Return proper timeout error (408) to frontend

### Step 2: [Backend] Update uvicorn startup timeout config
- The `__init__.py` likely starts uvicorn — increase timeout_keep_alive and add request timeout

### Step 3: [Frontend] Switch from base64 JSON → multipart FormData upload
- Change `sendVideo` to use `FormData` with the `/analyze` multipart endpoint
- Remove memory-heavy `FileSystem.readAsStringAsync` call
- Use `blob` / `FormData` approach for much faster upload

### Step 4: [Frontend] Update API_URL to point to `/analyze`
- Change endpoint from `/analyze-json` to `/analyze`

### Step 5: [Frontend] Improve progress reporting
- Use actual upload progress from XMLHttpRequest or fetch
- Better timeout detection

### Step 6: Test
- Verify backend starts with increased timeout
- Verify frontend upload completes without timeout

