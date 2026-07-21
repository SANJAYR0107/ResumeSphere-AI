import httpx

r = httpx.post(
    "http://127.0.0.1:8000/api/recommendations", 
    json={"resume_skills": ["Python"], "resume_text": "Hello World"}
)
print("Status:", r.status_code)
print("Body:", r.text)

r2 = httpx.post(
    "http://127.0.0.1:8000/api/ats-score", 
    json={"resume_text": "Hello World"}
)
print("Status:", r2.status_code)
print("Body:", r2.text)
