import requests
import json

url = "http://127.0.0.1:8001/api/skill-gap"

payload = {
    "resume_text": "I am a Java developer with 5 years experience in Spring Boot and REST API.",
    "job_description": "Looking for a Software Engineer with Java, Spring Boot, Microservices, and SQL experience."
}

try:
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")
