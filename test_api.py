import requests
import json
import os

url = "http://127.0.0.1:8001/api/analyze"

def analyze_resume(file_path):
    with open(file_path, "rb") as f:
        files = {"resume": (os.path.basename(file_path), f, "application/pdf")}
        response = requests.post(url, files=files)
        return response.json()

if __name__ == "__main__":
    print("Testing Java Resume...")
    java_res = analyze_resume("backend/tests/data/java_resume.pdf")
    with open("java_response.json", "w") as f:
        json.dump(java_res, f, indent=2)
    
    print("Testing Data Analyst Resume...")
    data_res = analyze_resume("backend/tests/data/data_resume.pdf")
    with open("data_response.json", "w") as f:
        json.dump(data_res, f, indent=2)
    
    print("Done. Responses saved to java_response.json and data_response.json")
