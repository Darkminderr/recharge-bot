import os
import requests
import uuid
import logging
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ലോഗ്സ് കാണാൻ
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

app = Flask('')
@app.route('/')
def home():
    return "API Bot is Running Perfectly!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

TOKEN = '7510297537:AAEeCr_pl4CndrNCpBpr7Ac8mL3jlFKpyRk'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ഹലോ! റീചാർജ് ചെയ്യാൻ /recharge എന്ന് ടൈപ്പ് ചെയ്യുക.")

async def get_payment_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loading_msg = await update.message.reply_text("⏳ പെയ്‌മെന്റ് ലിങ്ക് ഉണ്ടാക്കുന്നു... ദയവായി കാത്തിരിക്കുക ⚡")
    
    url = "https://prod.api.cosmofeed.com/api/muneem/payin"
    
    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9,en-IN;q=0.8",
        "content-type": "application/json",
        "origin": "https://superprofile.bio",
        "referer": "https://superprofile.bio/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "cosmofeed-request-id": str(uuid.uuid4())
    }
    
    # തൽക്കാലം നമ്മൾ ടെസ്റ്റ് ചെയ്ത ഇമെയിലും നമ്പറും ഉപയോഗിക്കുന്നു
    email = "sanjuchacko628@gmail.com"
    phone = "9188897019"
    
    payload = {
        "productId": "6994a964b7a14d00133409f7",
        "creatorId": "67fcc4cc1dd543001325d435",
        "referralCode": "",
        "productType": "page",
        "bookingData": {
            "inputFields": [
                {"_id": "3b64ec34-f9e7-443c-8195-40617c560c0e", "fieldName": "Email", "value": email, "fieldType": "email"},
                {"_id": "69940406b7a14d00130c0984", "fieldName": "Phone number", "value": phone, "fieldType": "phone", "countryCode": "+91"}
            ],
            "bookingType": "page",
            "amountPaid": 1000,
            "selectedQuantity": 1,
            "selectedProducts": [
                {"_id": "699403af99272700139424c8", "productType": 1, "priceType": 1, "price": 1000, "quantity": 1}
            ],
            "paymentProvider": "paytm",
            "timeZone": "Asia/Calcutta",
            "email": email,
            "phone": phone
        },
        "oneClickCheckout": False
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        data = response.json()
        
        # പെയ്‌മെന്റ് ലിങ്ക് കണ്ടുപിടിക്കാൻ ശ്രമിക്കുന്നു
        payment_url = None
        if 'data' in data:
            # സാധാരണയായി paymentUrl അല്ലെങ്കിൽ url എന്ന പേരിലായിരിക്കും ലിങ്ക് വരിക
            payment_url = data['data'].get('paymentUrl') or data['data'].get('url') or data['data'].get('payment_link')
            
        if payment_url:
            await loading_msg.edit_text(f"✅ പെയ്‌മെന്റ് ലിങ്ക് തയ്യാർ!\n\n🔗 ലിങ്ക്: {payment_url}\n\nഈ ലിങ്കിൽ ക്ലിക്ക് ചെയ്ത് പെയ്‌മെന്റ് പൂർത്തിയാക്കൂ.")
        else:
            # ചിലപ്പോൾ ഡാറ്റയിൽ ലിങ്ക് വരുന്ന പേര് വേറെയായിരിക്കും. അത് കണ്ടെത്താൻ:
            safe_data = str(data)[:1500]
            await loading_msg.edit_text(f"✅ സെർവർ കണക്ട് ആയി! പക്ഷേ ലിങ്കിന്റെ ശരിയായ പേര് കണ്ടെത്താൻ കഴിഞ്ഞില്ല. താഴെ കാണുന്ന കോഡ് എനിക്ക് (ജെമിനിക്ക്) കോപ്പി ചെയ്ത് അയച്ചു തരൂ:\n\n`{safe_data}`")
            
    except Exception as e:
        await loading_msg.edit_text(f"❌ ഒരു ചെറിയ എറർ വന്നു: {str(e)}")

if __name__ == '__main__':
    Thread(target=run_flask).start()
    print("Bot is Starting with API mode...")
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("recharge", get_payment_link))
    
    application.run_polling()
