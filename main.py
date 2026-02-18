import os, asyncio, logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from playwright.async_api import async_playwright
from flask import Flask
from threading import Thread

# ലോഗിൻ വിവരങ്ങൾ ലോഗ് ചെയ്യാൻ
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

app = Flask('')
@app.route('/')
def home(): return "Bot is Alive!"

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
            # മൊബൈൽ വ്യൂ കൃത്യമായി സെറ്റ് ചെയ്യുന്നു
            browser_context = await browser.new_context(
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
                viewport={'width': 390, 'height': 844}
            )
            page = await browser_context.new_page()
            
            # 1. സൈറ്റ് തുറക്കുന്നു
            await page.goto(URL, wait_until="networkidle", timeout=60000)
            
            # 2. ആദ്യത്തെ ബട്ടൺ ക്ലിക്ക്
            btn_selector = 'button.checkout-proceed-cta'
            await page.wait_for_selector(btn_selector, timeout=20000)
            await page.click(btn_selector, force=True) 
            
            await msg.edit_text("📝 വിവരങ്ങൾ കൃത്യമായി പൂരിപ്പിക്കുന്നു...")
            await asyncio.sleep(4) # ഫോം വരാൻ സമയം നൽകുന്നു
            
            # 3. ഇമെയിൽ നൽകുന്നു (sanjuchacko628@gmail.com)
            email_field = page.locator('input[type="email"], input[placeholder*="Email"]')
            await email_field.wait_for(state="visible", timeout=15000)
            await email_field.click()
            await email_field.fill("") # പഴയത് ഉണ്ടെങ്കിൽ ക്ലിയർ ചെയ്യുന്നു
            await page.keyboard.type("sanjuchacko628@gmail.com", delay=100)
            
            # 4. ഫോൺ നമ്പർ നൽകുന്നു (തുടക്കത്തിൽ 91 നിർബന്ധമായും ചേർക്കുന്നു)
            phone_field = page.locator('input[type="tel"]')
            await phone_field.click()
            await phone_field.fill("")
            await page.keyboard.type("9188897019", delay=100)
            
            # 5. വിവരങ്ങൾ നൽകിയ ശേഷം ബട്ടൺ വീണ്ടും ക്ലിക്ക് ചെയ്യുന്നു
            # സ്ക്രീനിൽ കാണുന്ന അവസാനത്തെ ബട്ടൺ തന്നെ ക്ലിക്ക് ചെയ്യാൻ
            final_btn = page.locator(btn_selector).last
            await final_btn.click(force=True)
            
            await msg.edit_text("📸 പെയ്‌മെന്റ് പേജിലേക്ക് മാറുന്നു (Wait 15s)...")
            await asyncio.sleep(15) 
            
            # പെയ്‌മെന്റ് ലിങ്കും സ്ക്രീൻഷോട്ടും
            final_url = page.url
            screenshot_path = "payment_final.png"
            await page.screenshot(path=screenshot_path)
            
            await update.message.reply_photo(
                photo=open(screenshot_path, 'rb'), 
                caption=f"✅ പെയ്‌മെന്റ് പേജ് റെഡിയാണ്!\n\n🔗 പെയ്‌മെന്റ് ലിങ്ക്: {final_url}"
            )
            
        except Exception as e:
            await page.screenshot(path="error_debug.png")
            await update.message.reply_photo(photo=open("error_debug.png", 'rb'), caption=f"Error: {str(e)}")
        finally:
            await browser.close()

if __name__ == '__main__':
    # Flask സ്റ്റാർട്ട് ചെയ്യുന്നു
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    # ബോട്ട് സ്റ്റാർട്ട് ചെയ്യുന്നു
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("recharge", get_qr))
    print("Bot is Starting...")
    application.run_polling()
