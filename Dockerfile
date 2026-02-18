FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# പോർട്ട് സെറ്റിംഗ്സ്
ENV PORT 8080
EXPOSE 8080

CMD ["python", "main.py"]
