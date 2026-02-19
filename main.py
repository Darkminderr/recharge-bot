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
    await update.message.reply_text("ഹലോ! റീചാർജ് ചെയ്യാൻ നിങ്ങളുടെ യുപിഐ ഐഡി അല്ലെങ്കിൽ ഫോൺ നമ്പർ ചേർത്ത് ടൈപ്പ് ചെയ്യുക.\nഉദാഹരണം: /recharge 9876543210")

async def process_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # യൂസർ നമ്പർ തന്നിട്ടുണ്ടോ എന്ന് നോക്കുന്നു
    if not context.args:
        await update.message.reply_text("⚠️ ദയവായി നിങ്ങളുടെ UPI നമ്പർ കൂടി നൽകുക.\nഉദാഹരണം: /recharge 9876543210")
        return
        
    user_upi_id = context.args[0]
    msg = await update.message.reply_text("⏳ നിങ്ങളുടെ പേയ്മെന്റ് റിക്വസ്റ്റ് തയ്യാറാക്കുന്നു...")
    
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(args=['--no-sandbox', '--disable-dev-shm-usage'])
            # നിങ്ങളുടെ വീഡിയോയിലെ പോലെ ഡെസ്ക്ടോപ്പ് വ്യൂ സെറ്റ് ചെയ്യുന്നു
            browser_context = await browser.new_context(viewport={'width': 1366, 'height': 768})
            page = await browser_context.new_page()
            
            await page.goto(URL, wait_until="networkidle", timeout=60000)
            
            # 1. ബട്ടൺ ക്ലിക്ക് ചെയ്യുന്നു
            btn_locator = page.locator('button:has-text("Get it now")')
            await btn_locator.first.wait_for(state="visible", timeout=15000)
            await btn_locator.first.click(force=True) 
            
            await asyncio.sleep(2)
            
            # 2. ഇമെയിലും ഫോണും ഓട്ടോമാറ്റിക്കായി നൽകുന്നു
            email_field = page.locator('input[placeholder*="Email"]').first
            await email_field.fill("sanjuchacko628@gmail.com")
            
            phone_field = page.locator('input[type="tel"]').first
            await phone_field.fill("9188897019")
            
            # 3. വീണ്ടും Get it now ക്ലിക്ക് ചെയ്യുന്നു
            await btn_locator.last.click(force=True)
            
            await msg.edit_text("⏳ UPI ഗേറ്റ്‌വേയിലേക്ക് കണക്ട് ചെയ്യുന്നു...")
            await asyncio.sleep(8) # പെയ്‌മെന്റ് ബോക്സ് ലോഡ് ആകാൻ
            
            # 4. UPI ഓപ്ഷൻ ക്ലിക്ക് ചെയ്യുന്നു (വീഡിയോയിൽ കണ്ടതുപോലെ)
            await page.locator('text="UPI"').last.click()
            await asyncio.sleep(2)
            
            # 5. യൂസർ തന്ന നമ്പർ ടൈപ്പ് ചെയ്യുന്നു
            upi_input = page.locator('input[placeholder*="Mobile No."]')
            await upi_input.fill(user_upi_id)
            
            # 6. Proceed ബട്ടൺ ക്ലിക്ക് ചെയ്യുന്നു
            await page.locator('button:has-text("Proceed")').click()
            
            # റിക്വസ്റ്റ് അയച്ച വിവരം യൂസറെ അറിയിക്കുന്നു
            await msg.edit_text(f"✅ നിങ്ങളുടെ ആപ്പിലേക്ക് ( {user_upi_id} ) പെയ്‌മെന്റ് റിക്വസ്റ്റ് അയച്ചിട്ടുണ്ട്!\n\nദയവായി ആപ്പ് തുറന്ന് ഇപ്പോൾ തന്നെ പെയ്‌മെന്റ് പൂർത്തിയാക്കുക. (സമയം: 5 മിനിറ്റ്)")
            
            # 7. പെയ്‌മെന്റ് സക്സസ് ആകാൻ കാത്തിരിക്കുന്നു (പരമാവധി 5 മിനിറ്റ്)
            try:
                # സ്ക്രീനിൽ "Payment Successful" വരുന്നുണ്ടോ എന്ന് നോക്കുന്നു
                await page.wait_for_selector('text="Payment Successful"', timeout=300000) 
                
                # സക്സസ് ആയാൽ യൂസർക്ക് മെസ്സേജ്!
                await update.message.reply_text("🎉 പെയ്‌മെന്റ് വിജയകരം! നിങ്ങളുടെ ഗെയിമിലേക്ക് റീചാർജ് തുക ആഡ് ചെയ്തിട്ടുണ്ട്.")
                
                # -----------------------------------------------------------------
                # സഞ്ജു, ഇവിടെയാണ് ഗെയിമിലേക്ക് ക്യാഷ് ആഡ് ചെയ്യാനുള്ള കോഡ് നമ്മൾ എഴുതേണ്ടത്!
                # -----------------------------------------------------------------
                
            except Exception as wait_err:
                await update.message.reply_text("⏰ സമയം കഴിഞ്ഞു! പെയ്‌മെന്റ് ലഭിച്ചില്ല. ദയവായി വീണ്ടും ശ്രമിക്കുക.")
            
        except Exception as e:
            await update.message.reply_text(f"❌ ഒരു തടസ്സം നേരിട്ടു: {str(e)}")
            await page.screenshot(path="error.png")
            await update.message.reply_photo(photo=open("error.png", 'rb'))
        finally:
            await browser.close()

if __name__ == '__main__':
    Thread(target=run_flask).start()
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("recharge", process_payment))
    print("UPI Request Bot is Starting...")
    application.run_polling()
