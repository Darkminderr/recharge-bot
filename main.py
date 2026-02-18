import os, asyncio, logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from playwright.async_api import async_playwright
from flask import Flask
from threading import Thread

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
            # മൊബൈൽ വ്യൂ ഉറപ്പാക്കാൻ കൃത്യമായ viewport നൽകുന്നു
            browser = await p.chromium.launch(args=['--no-sandbox', '--disable-dev-shm-usage'])
            # iPhone 13 വലിപ്പത്തിലുള്ള സ്ക്രീൻ സെറ്റ് ചെയ്യുന്നു
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
                viewport={'width': 390, 'height': 844}
            )
            page = await context.new_page()
            
            await page.goto(URL, wait_until="domcontentloaded", timeout=60000)
            
            # 1. ആദ്യത്തെ കറുത്ത ബട്ടൺ ക്ലിക്ക് ചെയ്യുന്നു (Force Click ഉപയോഗിക്കുന്നു)
            # ലോഗ് പ്രകാരം 'checkout-proceed-cta' എന്ന ക്ലാസ്സാണ് ഇതിനുള്ളത്
            btn_selector = 'button.checkout-proceed-cta'
            await page.wait_for_selector(btn_selector, timeout=15000)
            await page.click(btn_selector, force=True) 
            
            await msg.edit_text("📝 വിവരങ്ങൾ നൽകുന്നു...")
            
            # 2. വിവരങ്ങൾ പൂരിപ്പിക്കുന്നു
            await page.wait_for_selector('input[type="email"]', timeout=10000)
            await page.fill('input[type="email"]', 'sanjuchacko682@gmail.com')
            await page.fill('input[type="tel"]', '9188897019')
            
            # 3. രണ്ടാമത്തെ ക്ലിക്ക് (വിവരങ്ങൾ നൽകിയ ശേഷം)
            await page.click(btn_selector, force=True)
            
            await msg.edit_text("📸 പെയ്‌മെന്റ് പേജ് ലോഡ് ആകുന്നു...")
            
            # പെയ്‌മെന്റ് പേജ് വരാൻ അല്പം കൂടുതൽ സമയം നൽകുന്നു
            await asyncio.sleep(12) 
            
            # സ്ക്രീൻഷോട്ട് എടുക്കുന്നു
            await page.screenshot(path="payment.png", full_page=False)
            await update.message.reply_photo(photo=open("payment.png", 'rb'), caption="✅ പെയ്‌മെന്റ് പൂർത്തിയാക്കൂ.")
            
        except Exception as e:
            # എറർ വന്നാൽ എന്താണ് സംഭവിക്കുന്നത് എന്ന് കാണാൻ ഒരു ഫോട്ടോ എടുക്കുന്നു
            try:
                await page.screenshot(path="error_snap.png")
                await update.message.reply_photo(photo=open("error_snap.png", 'rb'), caption=f"Error Snap: {str(e)}")
            except:
                await update.message.reply_text(f"ക്ഷമിക്കണം, ഒരു എറർ വന്നു: {str(e)}")
        finally:
            await browser.close()

if __name__ == '__main__':
    Thread(target=run_flask).start()
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("recharge", get_qr))
    print("Bot Starting...")
    application.run_polling()
