# Playwright-ന്റെ ഒഫീഷ്യൽ ഇമേജ് ഉപയോഗിക്കുന്നു (v1.58.0)
FROM mcr.microsoft.com/playwright/python:v1.58.0-jammy

# വർക്കിംഗ് ഡയറക്ടറി സെറ്റ് ചെയ്യുന്നു
WORKDIR /app

# ആവശ്യമായ ലൈബ്രറികൾ ഇൻസ്റ്റാൾ ചെയ്യുന്നു
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# നമ്മുടെ കോഡ് ഫയലുകൾ കോപ്പി ചെയ്യുന്നു
COPY . .

# ക്രോമിയം ബ്രൗസറും അതിന്റെ ഡിപ്പൻഡൻസികളും ഇൻസ്റ്റാൾ ചെയ്യുന്നു
RUN playwright install chromium --with-deps

# പോർട്ട് സെറ്റ് ചെയ്യുന്നു
ENV PORT 8080
EXPOSE 8080

# കോഡ് റൺ ചെയ്യുന്നു
CMD ["python", "main.py"]
