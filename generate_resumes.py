import os
from reportlab.pdfgen import canvas

def create_resume(filename, name, text):
    c = canvas.Canvas(filename)
    c.drawString(50, 800, name)
    y = 750
    for line in text.split('\n'):
        c.drawString(50, y, line.strip())
        y -= 20
    c.save()

java_text = """
Experienced Java Backend Developer with 5 years of experience.
Skills: Java, Spring Boot, SQL, REST API, Microservices, Docker, AWS.
Experience:
- Software Engineer at Tech Corp (2018-2023)
- Built microservices using Spring Boot and Java.
- Managed AWS infrastructure and Docker containers.
Education: BS Computer Science.
"""

data_text = """
Data Analyst with 3 years of experience.
Skills: SQL, Python, Data Visualization, Excel, Tableau, Pandas.
Experience:
- Data Analyst at Analytics Inc (2020-2023)
- Analyzed large datasets using Python, Pandas, and SQL.
- Created interactive dashboards in Tableau.
Education: BS Mathematics.
"""

output_dir = "backend/tests/data"
os.makedirs(output_dir, exist_ok=True)
create_resume(os.path.join(output_dir, "java_resume.pdf"), "John Java", java_text)
create_resume(os.path.join(output_dir, "data_resume.pdf"), "Alice Data", data_text)

devops_text = """
DevOps Engineer with 4 years of experience.
Skills: AWS, Docker, Kubernetes, CI/CD, Terraform, Linux, Python, Jenkins.
Experience:
- Site Reliability Engineer at CloudWorks (2019-2023)
- Automated infrastructure provisioning using Terraform and AWS.
- Maintained CI/CD pipelines with Jenkins and Docker.
Education: BS Information Technology.
"""
create_resume(os.path.join(output_dir, "devops_resume.pdf"), "David DevOps", devops_text)

print("Generated resumes successfully.")
