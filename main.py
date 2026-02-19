import os, asyncio, logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from playwright.async_api import async_playwright
from flask import Flask
from threading import Thread

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

app = Flask('')
@app.route('/')
def home(): return "UPI Request Bot is Running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

TOKEN = '7510297537:AAEeCr_pl4CndrNCpBpr7Ac8mL3jlFKpyRk'
URL = "https://superprofile.bio/vp/6994a964b7a14d00133409f7"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ഹലോ! റീചാർജ് ചെയ്യാൻ നിങ്ങളുടെ യുപിഐ ഐഡി അല്ലെങ്കിൽ മൊബൈൽ നമ്പർ ചേർത്ത് ടൈപ്പ് ചെയ്യുക.\nഉദാഹരണം: /recharge 9876543210")

async def process_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ ദയവായി നിങ്ങളുടെ UPI ഐഡി അല്ലെങ്കിൽ മൊബൈൽ നമ്പർ കൂടി നൽകുക.\nഉദാഹരണം: /recharge 9876543210")
        return
        
    user_upi_id = context.args[0]
    msg = await update.message.reply_text("⏳ ഡീറ്റെയിൽസ് എന്റർ ചെയ്യുന്നു...")
    
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(args=['--no-sandbox', '--disable-dev-shm-usage'])
            browser_context = await browser.new_context(viewport={'width': 1366, 'height': 768})
            page = await browser_context.new_page()
            
            await page.goto(URL, wait_until="networkidle", timeout=60000)
            await asyncio.sleep(4)
            
            # 1. ഇമെയിൽ നൽകുന്നു (ഇത് ഇപ്പോൾ കൃത്യമായി വർക്ക് ചെയ്യുന്നുണ്ട്)
            all_inputs = page.locator('input')
            await all_inputs.first.wait_for(state="visible", timeout=15000)
            await all_inputs.first.click(force=True)
            await page.keyboard.type("sanjuchacko628@gmail.com", delay=50)
            
            await asyncio.sleep(1)
            
            # 2. Get it now ക്ലിക്ക് ചെയ്യുന്നു (Error Fixed - .last ഉപയോഗിക്കുന്നു)
            get_btn = page.locator('button.checkout-proceed-cta')
            await get_btn.last.click(force=True)
            
            await msg.edit_text("⏳ പെയ്‌മെന്റ് ഗേറ്റ്‌വേയിലേക്ക് കണക്ട് ചെയ്യുന്നു...")
            await asyncio.sleep(6) 
            
            # 3. UPI ഓപ്ഷൻ ക്ലിക്ക് ചെയ്യുന്നു
            await page.locator('text="UPI"').last.click(force=True)
            await asyncio.sleep(2)
            
            # 4. യൂസർ ടെലിഗ്രാമിൽ തന്ന നമ്പർ ടൈപ്പ് ചെയ്യുന്നു
            upi_input = page.locator('input[placeholder*="Mobile No."], input[placeholder*="UPI"], input[placeholder*="VPA"]').first
            await upi_input.click(force=True)
            await page.keyboard.type(user_upi_id, delay=50)
            
            # 5. VERIFY ബട്ടൺ ഉണ്ടെങ്കിൽ ക്ലിക്ക് ചെയ്യുന്നു
            verify_btn = page.locator('text="Verify"')
            if await verify_btn.is_visible():
                await verify_btn.first.click()
                await asyncio.sleep(3)
            
            # 6. Proceed ബട്ടൺ ക്ലിക്ക് ചെയ്യുന്നു
            await page.locator('button:has-text("Proceed")').first.click(force=True)
            
            # റിക്വസ്റ്റ് വിൻഡോ (ടൈമർ) വരാൻ കുറച്ചു സമയം കാത്തിരിക്കുന്നു
            await asyncio.sleep(4)
            
            # 7. ടൈമർ വിൻഡോയുടെ സ്ക്രീൻഷോട്ട് എടുത്ത് യൂസർക്ക് അയക്കുന്നു
            await page.screenshot(path="timer.png")
            await update.message.reply_photo(
                photo=open("timer.png", 'rb'), 
                caption=f"✅ നിങ്ങളുടെ നമ്പറിലേക്ക് ( {user_upi_id} ) പെയ്‌മെന്റ് റിക്വസ്റ്റ് അയച്ചിട്ടുണ്ട്!\n\nദയവായി നിങ്ങളുടെ പേയ്മെൻറ് ആപ്പ് തുറന്ന് ഈ സമയം തീരുന്നതിന് മുൻപ് പെയ്‌മെന്റ് പൂർത്തിയാക്കുക."
            )
            
            # 8. പെയ്‌മെന്റ് സക്സസ് ആകാൻ കാത്തിരിക്കുന്നു 
            try:
                await page.wait_for_selector('text="Payment Successful"', timeout=300000) # 5 മിനിറ്റ് വരെ കാത്തിരിക്കും
                # സക്സസ് ആയാൽ മാത്രം ഈ മെസ്സേജ് വരും
                await update.message.reply_text("🎉 പെയ്‌മെന്റ് വിജയകരം! Payment Successful ആയിട്ടുണ്ട്. നിങ്ങളുടെ ഗെയിമിലേക്ക് റീചാർജ് തുക ആഡ് ചെയ്തിട്ടുണ്ട്.")
            except Exception as wait_err:
                await update.message.reply_text("⏰ സമയം കഴിഞ്ഞു! പെയ്‌മെന്റ് ലഭിച്ചില്ല. ദയവായി വീണ്ടും ശ്രമിക്കുക.")
            
        except Exception as e:
            await page.screenshot(path="error.png")
            await update.message.reply_photo(photo=open("error.png", 'rb'), caption=f"❌ ഒരു തടസ്സം നേരിട്ടു: {str(e)}")
        finally:
            await browser.close()

if __name__ == '__main__':
    Thread(target=run_flask).start()
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("recharge", process_payment))
    print("UPI Request Bot is Starting...")
    application.run_polling()
