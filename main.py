import os, asyncio, logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from playwright.async_api import async_playwright
from flask import Flask
from threading import Thread

# ലോഗ്സ് കാണാൻ
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

app = Flask('')
@app.route('/')
def home(): return "Bot is Alive and Running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

TOKEN = '7510297537:AAEeCr_pl4CndrNCpBpr7Ac8mL3jlFKpyRk'
URL = "https://superprofile.bio/vp/6994a964b7a14d00133409f7"

async def get_qr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("⏳ സൂപ്പർ പ്രൊഫൈലിലേക്ക് കണക്ട് ചെയ്യുന്നു...")
    async with async_playwright() as p:
        try:
            # ബ്രൗസർ ലോഞ്ച് ചെയ്യുന്നു
            browser = await p.chromium.launch(args=['--no-sandbox', '--disable-dev-shm-usage', '--single-process'])
            page = await browser.new_page()
            
            # സൂപ്പർ പ്രൊഫൈൽ ഓട്ടോമേഷൻ
            await page.goto(URL, timeout=60000)
            await page.click('button:has-text("Get it now")')
            await page.fill('input[type="email"]', 'sanjuchacko682@gmail.com')
            await page.fill('input[type="tel"]', '9188897019')
            await page.click('button:has-text("Get it now")')
            
            # പെയ്‌മെന്റ് പേജ് വരാൻ കാത്തിരിക്കുന്നു
            await asyncio.sleep(10) 
            
            # സ്ക്രീൻഷോട്ട് എടുക്കുന്നു
            await page.screenshot(path="payment.png")
            await update.message.reply_photo(photo=open("payment.png", 'rb'), caption="✅ പെയ്‌മെന്റ് പൂർത്തിയാക്കൂ. (ഇത് പെയ്‌മെന്റ് പേജ് അല്ലെങ്കിൽ ലോഗ്സ് നോക്കൂ)")
            
        except Exception as e:
            await update.message.reply_text(f"ക്ഷമിക്കണം, ഒരു എറർ വന്നു: {str(e)}")
        finally:
            await browser.close()

if __name__ == '__main__':
    Thread(target=run_flask).start()
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("recharge", get_qr))
    print("Bot Starting...")
    application.run_polling()
