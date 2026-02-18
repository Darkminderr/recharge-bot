# പുതിയ വേർഷൻ (v1.58.0) ഉപയോഗിക്കുന്നു
FROM mcr.microsoft.com/playwright/python:v1.58.0-jammy

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# ബ്രൗസർ ഇൻസ്റ്റാൾ ചെയ്യുന്നു
RUN playwright install chromium --with-deps

ENV PORT 8080
EXPOSE 8080

CMD ["python", "main.py"]
