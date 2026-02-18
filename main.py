import os, asyncio, logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from playwright.async_api import async_playwright
from flask import Flask
from threading import Thread

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

app = Flask('')
@app.route('/')
def home(): return "Bot is Online!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

TOKEN = '7510297537:AAEeCr_pl4CndrNCpBpr7Ac8mL3jlFKpyRk'
URL = "https://superprofile.bio/vp/6994a964b7a14d00133409f7"

async def get_qr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("⏳ പെയ്‌മെന്റ് പേജിലേക്ക് കണക്ട് ചെയ്യുന്നു...")
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(args=['--no-sandbox', '--disable-dev-shm-usage'])
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
                viewport={'width': 390, 'height': 844}
            )
            page = await context.new_page()
            
            # 1. സൈറ്റ് തുറക്കുന്നു
            await page.goto(URL, wait_until="networkidle", timeout=60000)
            
            # 2. ആദ്യത്തെ 'Get it now' ക്ലിക്ക്
            btn_selector = 'button.checkout-proceed-cta'
            await page.wait_for_selector(btn_selector, timeout=15000)
            await page.click(btn_selector, force=True) 
            
            await msg.edit_text("📝 വിവരങ്ങൾ പൂരിപ്പിക്കുന്നു...")
            await asyncio.sleep(2) # വിൻഡോ തെളിയാൻ സമയം
            
            # 3. ഇമെയിൽ നൽകുന്നു (നിങ്ങൾ തന്ന പുതിയ ഇമെയിൽ)
            email_field = page.locator('input[type="email"], input[placeholder*="Email"]')
            await email_field.wait_for(state="visible", timeout=10000)
            await email_field.click()
            await email_field.fill("") # പഴയത് ഉണ്ടെങ്കിൽ മായ്ക്കുന്നു
            await email_field.type('sanjuchacko628@gmail.com', delay=50)
            
            # 4. ഫോൺ നമ്പർ നൽകുന്നു
            phone_field = page.locator('input[type="tel"]')
            await phone_field.click()
            await phone_field.fill("") 
            await phone_field.type('9188897019', delay=50)
            
            # 5. ബട്ടൺ ക്ലിക്ക് ചെയ്യുന്നു (പെയ്‌മെന്റ് പേജിലേക്ക്)
            await page.click(btn_selector, force=True)
            
            await msg.edit_text("📸 പെയ്‌മെന്റ് പേജ് എടുക്കുന്നു...")
            
            # പെയ്‌മെന്റ് പേജ് ലോഡ് ആകാൻ കാത്തിരിക്കുന്നു
            await asyncio.sleep(15) 
            
            # ലിങ്ക് എടുക്കുന്നു
            payment_url = page.url
            
            # സ്ക്രീൻഷോട്ട് എടുക്കുന്നു
            screenshot_path = "payment_final.png"
            await page.screenshot(path=screenshot_path)
            
            # യൂസർക്ക് അയക്കുന്നു
            await update.message.reply_photo(
                photo=open(screenshot_path, 'rb'), 
                caption=f"✅ പെയ്‌മെന്റ് പേജ് തയ്യാർ!\n\n🔗 ലിങ്ക്: {payment_url}"
            )
            
        except Exception as e:
            await page.screenshot(path="error_debug.png")
            await update.message.reply_photo(photo=open("error_debug.png", 'rb'), caption=f"എറർ: {str(e)}")
        finally:
            await browser.close()

if __name__ == '__main__':
    Thread(target=run_flask).start()
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("recharge", get_qr))
    print("Bot Starting...")
    application.run_polling()
