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
            
            # 4. കൃത്യമായി മൊബൈൽ നമ്പർ നൽകുന്നു
            upi_input = page.locator('input[placeholder*="Mobile No."]').last
            await upi_input.click(force=True)
            await page.keyboard.type(user_upi_id, delay=100)
            
            await asyncio.sleep(2)
            
            try:
                verify_link = page.locator('text="Verify"').last
                if await verify_link.is_visible(timeout=2000):
                    await verify_link.click(force=True)
                    await asyncio.sleep(3) 
            except:
                pass
            
            # 5. Proceed ബട്ടൺ ക്ലിക്ക് ചെയ്യുന്നു 
            proceed_btn = page.locator('button:has-text("Proceed"):visible').last
            await proceed_btn.wait_for(state="visible", timeout=10000)
            await proceed_btn.click(force=True)
            
            # 6. ടൈമർ വിൻഡോ വരാൻ കാത്തിരിക്കുന്നു
            try:
                await page.wait_for_selector('text="PAGE EXPIRES IN"', timeout=15000)
            except:
                if await proceed_btn.is_visible():
                    await proceed_btn.click(force=True)
                    await asyncio.sleep(4)
                
            # 7. ടൈമർ സ്ക്രീൻഷോട്ട് എടുത്ത് യൂസർക്ക് അയക്കുന്നു
            await page.screenshot(path="timer.png")
            await update.message.reply_photo(
                photo=open("timer.png", 'rb'), 
                caption=f"✅ നിങ്ങളുടെ നമ്പറിലേക്ക് ( {user_upi_id} ) പെയ്‌മെന്റ് റിക്വസ്റ്റ് അയച്ചിട്ടുണ്ട്!\n\nദയവായി നിങ്ങളുടെ ആപ്പ് തുറന്ന് സമയം തീരുന്നതിന് മുൻപ് പെയ്‌മെന്റ് പൂർത്തിയാക്കുക (8 മിനിറ്റ് സമയം)."
            )
            
            # ---------------------------------------------------------
            # 8. പെയ്‌മെന്റ് സക്സസ് ആകാൻ 8 മിനിറ്റ് കാത്തിരിക്കുന്നു (NEW LOGIC)
            # ---------------------------------------------------------
            payment_success = False
            
            # ഓരോ 5 സെക്കൻഡിലും പേജ് സ്കാൻ ചെയ്യുന്നു (പരമാവധി 100 തവണ = 8 മിനിറ്റിലധികം)
            for _ in range(100):
                await asyncio.sleep(5) 
                
                try:
                    # പേജിലുള്ള എല്ലാ അക്ഷരങ്ങളും (content) സ്കാൻ ചെയ്ത് സക്സസ് ആണോ എന്ന് നോക്കുന്നു
                    page_text = await page.content()
                    
                    if "Payment Successful" in page_text or "Purchase successful" in page_text or "Payment made successfully" in page_text or "Successful" in page_text:
                        payment_success = True
                        break # സക്സസ് കണ്ടാൽ ഉടൻ തന്നെ ലൂപ്പ് നിർത്തുന്നു
                except:
                    pass
            
            if payment_success:
                await asyncio.sleep(2) # സക്സസ് പേജ് പൂർണ്ണമായി തെളിയാൻ 2 സെക്കൻഡ് കാത്തിരിക്കുന്നു
                await page.screenshot(path="success.png")
                
                await update.message.reply_photo(
                    photo=open("success.png", 'rb'),
                    caption="🎉 പെയ്‌മെന്റ് വിജയകരം! Payment Successful ആയിട്ടുണ്ട്. നിങ്ങളുടെ ഗെയിമിലേക്ക് റീചാർജ് തുക ആഡ് ചെയ്തു."
                )
            else:
                # 8 മിനിറ്റ് കഴിഞ്ഞിട്ടും സക്സസ് വന്നില്ലെങ്കിൽ
                await update.message.reply_text("⏰ 8 മിനിറ്റ് സമയം കഴിഞ്ഞു! പെയ്‌മെന്റ് ലഭിച്ചില്ല അഥവാ യൂസർ പെയ്‌മെന്റ് ചെയ്തില്ല.")
            
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
