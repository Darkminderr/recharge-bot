import os, asyncio, logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from playwright.async_api import async_playwright
from flask import Flask
from threading import Thread

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

app = Flask('')
@app.route('/')
def home(): return "Playwright Bot is Running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

TOKEN = '7510297537:AAEeCr_pl4CndrNCpBpr7Ac8mL3jlFKpyRk'
URL = "https://superprofile.bio/vp/6994a964b7a14d00133409f7"

async def get_qr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("⏳ സൈറ്റ് ലോഡ് ചെയ്യുന്നു...")
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(args=['--no-sandbox', '--disable-dev-shm-usage'])
            browser_context = await browser.new_context(
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
                viewport={'width': 390, 'height': 844}
            )
            page = await browser_context.new_page()
            
            await page.goto(URL, wait_until="networkidle", timeout=60000)
            
            # 1. ആദ്യത്തെ ബട്ടൺ ക്ലിക്ക് ചെയ്യുന്നു (കാണാൻ കഴിയുന്നത് മാത്രം)
            btn_locator = page.locator('button.checkout-proceed-cta:visible')
            await btn_locator.first.wait_for(timeout=15000)
            await btn_locator.first.click(force=True) 
            
            await msg.edit_text("📝 വിവരങ്ങൾ പൂരിപ്പിക്കുന്നു...")
            await asyncio.sleep(4) 
            
            # 2. ഇമെയിൽ നൽകുന്നു 
            email_field = page.locator('input[type="email"]:visible, input[placeholder*="Email"]:visible').first
            await email_field.wait_for(timeout=15000)
            await email_field.fill("sanjuchacko628@gmail.com")
            
            # 3. ഫോൺ നമ്പർ നൽകുന്നു
            phone_field = page.locator('input[type="tel"]:visible').first
            await phone_field.fill("9188897019")
            
            # 4. പെയ്‌മെന്റ് പേജിലേക്കുള്ള ബട്ടൺ വീണ്ടും ക്ലിക്ക് ചെയ്യുന്നു
            await btn_locator.last.click(force=True)
            
            await msg.edit_text("📸 പെയ്‌മെന്റ് ക്യുആർ എടുക്കുന്നു (Wait 15s)...")
            await asyncio.sleep(15) 
            
            # സ്ക്രീൻഷോട്ട് സേവ് ചെയ്യുന്നു
            screenshot_path = "payment_final.png"
            await page.screenshot(path=screenshot_path)
            
            await update.message.reply_photo(
                photo=open(screenshot_path, 'rb'), 
                caption="✅ പെയ്‌മെന്റ് ക്യുആർ റെഡിയാണ്! സ്കാൻ ചെയ്ത് പെയ്‌മെന്റ് പൂർത്തിയാക്കൂ."
            )
            
        except Exception as e:
            # എന്തെങ്കിലും എറർ വന്നാൽ അതിന്റെ ഫോട്ടോ അയക്കാൻ
            await page.screenshot(path="error_debug.png")
            await update.message.reply_photo(photo=open("error_debug.png", 'rb'), caption=f"Error: {str(e)}")
        finally:
            await browser.close()

if __name__ == '__main__':
    Thread(target=run_flask).start()
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("recharge", get_qr))
    print("Bot is Starting...")
    application.run_polling()
