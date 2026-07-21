import httpx
import sys

filename = "backend/uploads/aivar res.pdf"

with open(filename, "rb") as f:
    files = {"resume": (filename, f, "application/pdf")}
    try:
        r = httpx.post("http://127.0.0.1:8000/api/analyze", files=files, timeout=60.0)
        print("Status:", r.status_code)
        print("Response:", r.text[:500])
    except Exception as e:
        print("Error:", e)
