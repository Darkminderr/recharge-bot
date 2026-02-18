import os, asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from playwright.async_api import async_playwright
from flask import Flask
from threading import Thread

# Render-ന് വേണ്ടിയുള്ള വെബ് സെർവർ
app = Flask('')
@app.route('/')
def home(): return "Bot is Online!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    Thread(target=run).start()

# നിങ്ങളുടെ ടോക്കണും ലിങ്കും ഇവിടെ നൽകുക
TOKEN = 'YOUR_BOT_TOKEN'
URL = "YOUR_URL"

async def get_qr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("⚡ കണക്ട് ചെയ്യുന്നു...")
    async with async_playwright() as p:
        try:
            # ബ്രൗസർ സെറ്റിംഗ്സ്
            browser = await p.chromium.launch(args=['--no-sandbox', '--disable-setuid-sandbox'])
            page = await browser.new_page()
            
            # വിവരങ്ങൾ നൽകുന്ന പ്രക്രിയ
            await page.goto(URL, timeout=60000)
            await page.click('button:has-text("Get it now")')
            
            # വിവരങ്ങൾ പൂരിപ്പിക്കുന്നു (ഇമെയിലും ഫോണും)
            await page.fill('input[type="email"]', 'sanjuchacko682@gmail.com')
            await page.fill('input[type="tel"]', '9188897019')
            await page.click('button:has-text("Get it now")')
            
            # QR കോഡ് ലോഡ് ആകാൻ കാത്തിരിക്കുന്നു
            await asyncio.sleep(8) 
            
            # സ്ക്രീൻഷോട്ട് എടുക്കുന്നു
            await page.screenshot(path="payment.png")
            await update.message.reply_photo(photo=open("payment.png", 'rb'), caption="✅ പേയ്മെന്റ് പൂർത്തിയാക്കൂ.")
            
        except Exception as e:
            await update.message.reply_text(f"Error: {str(e)}")
        finally:
            await browser.close()

if __name__ == '__main__':
    keep_alive()
    ApplicationBuilder().token(TOKEN).build().add_handler(CommandHandler("recharge", get_qr)).run_polling()
