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
    await update.message.reply_text("ഹലോ! റീചാർജ് ചെയ്യാൻ നിങ്ങളുടെ മൊബൈൽ നമ്പർ ചേർത്ത് ടൈപ്പ് ചെയ്യുക.\nഉദാഹരണം: /recharge 9876543210")

async def process_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ ദയവായി നിങ്ങളുടെ മൊബൈൽ നമ്പർ കൂടി നൽകുക.\nഉദാഹരണം: /recharge 9876543210")
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
            
            # 1. ഇമെയിൽ നൽകുന്നു
            all_inputs = page.locator('input')
            await all_inputs.first.wait_for(state="visible", timeout=15000)
            await all_inputs.first.click(force=True)
            await page.keyboard.type("sanjuchacko628@gmail.com", delay=50)
            
            await asyncio.sleep(1)
            
            # 2. Get it now ക്ലിക്ക് ചെയ്യുന്നു
            get_btn = page.locator('button.checkout-proceed-cta')
            await get_btn.last.click(force=True)
            
            await msg.edit_text("⏳ പെയ്‌മെന്റ് ഗേറ്റ്‌വേയിലേക്ക് കണക്ട് ചെയ്യുന്നു...")
            await asyncio.sleep(6) 
            
            # 3. UPI ഓപ്ഷൻ ക്ലിക്ക് ചെയ്യുന്നു
            await page.locator('text="UPI"').last.click(force=True)
            await asyncio.sleep(2)
            
            # 4. കൃത്യമായി മൊബൈൽ നമ്പർ നൽകുന്നു (രണ്ടാമത്തെ ബോക്സിൽ)
            upi_input = page.locator('input[placeholder*="Mobile No."]').last
            await upi_input.click(force=True)
            await page.keyboard.type(user_upi_id, delay=100)
            
            await asyncio.sleep(2)
            
            # Verify എന്ന ലിങ്ക് നീല നിറത്തിൽ ഉണ്ടെങ്കിൽ അതൊന്ന് ക്ലിക്ക് ചെയ്യുന്നു
            try:
                verify_link = page.locator('text="Verify"').last
                if await verify_link.is_visible(timeout=2000):
                    await verify_link.click(force=True)
                    await asyncio.sleep(3) # വെരിഫൈ ആയി പച്ച ടിക്ക് വരാൻ കാത്തിരിക്കുന്നു
            except:
                pass
            
            # 5. Proceed ബട്ടൺ കൃത്യമായി ക്ലിക്ക് ചെയ്യുന്നു (യെല്ലോ ബട്ടൺ ഫിക്സ്)
            # .last ഉപയോഗിച്ച് ഏറ്റവും താഴെയുള്ള കാണാൻ കഴിയുന്ന Proceed ബട്ടൺ മാത്രം എടുക്കുന്നു
            proceed_btn = page.locator('button:has-text("Proceed"):visible').last
            await proceed_btn.wait_for(state="visible", timeout=10000)
            await proceed_btn.click(force=True)
            
            await msg.edit_text("⏳ പെയ്‌മെന്റ് ടൈമർ വിൻഡോ ലോഡ് ആകുന്നു...")
            
            # 6. "PAGE EXPIRES IN" എന്ന ടൈമർ സ്ക്രീനിൽ വരുന്നതുവരെ കാത്തിരിക്കുന്നു
            try:
                await page.wait_for_selector('text="PAGE EXPIRES IN"', timeout=15000)
            except:
                # ഒരുവേള ആദ്യത്തെ ക്ലിക്ക് വർക്ക് ആയില്ലെങ്കിൽ ഒന്നുകൂടി ബട്ടൺ അമർത്തുന്നു
                if await proceed_btn.is_visible():
                    await proceed_btn.click(force=True)
                    await page.wait_for_selector('text="PAGE EXPIRES IN"', timeout=15000)
                
            # 7. ടൈമർ സ്ക്രീൻഷോട്ട് എടുത്ത് യൂസർക്ക് അയക്കുന്നു
            await page.screenshot(path="timer.png")
            await update.message.reply_photo(
                photo=open("timer.png", 'rb'), 
                caption=f"✅ നിങ്ങളുടെ നമ്പറിലേക്ക് ( {user_upi_id} ) പെയ്‌മെന്റ് റിക്വസ്റ്റ് അയച്ചിട്ടുണ്ട്!\n\nദയവായി നിങ്ങളുടെ ആപ്പ് തുറന്ന് സമയം തീരുന്നതിന് മുൻപ് പെയ്‌മെന്റ് പൂർത്തിയാക്കുക (8 മിനിറ്റ് സമയം)."
            )
            
            # 8. പെയ്‌മെന്റ് സക്സസ് ആകാൻ 8 മിനിറ്റ് കാത്തിരിക്കുന്നു 
            try:
                await page.wait_for_selector('text="Purchase successful", text="Payment made successfully", text="Payment Successful"', timeout=490000)
                
                await asyncio.sleep(2) 
                await page.screenshot(path="success.png")
                
                await update.message.reply_photo(
                    photo=open("success.png", 'rb'),
                    caption="🎉 പെയ്‌മെന്റ് വിജയകരം! Payment Successful ആയിട്ടുണ്ട്. നിങ്ങളുടെ ഗെയിമിലേക്ക് റീചാർജ് തുക ആഡ് ചെയ്തു."
                )
                
            except Exception as wait_err:
                await update.message.reply_text("⏰ 8 മിനിറ്റ് സമയം കഴിഞ്ഞു! പെയ്‌മെന്റ് ലഭിച്ചില്ല. ദയവായി വീണ്ടും ശ്രമിക്കുക.")
            
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
