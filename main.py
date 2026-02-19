import os, asyncio, logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from playwright.async_api import async_playwright
from flask import Flask
from threading import Thread

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

app = Flask('')
@app.route('/')
def home(): return "UPI Request Bot is Running in High Speed Mode!"

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
    msg = await update.message.reply_text("⚡ അതിവേഗം പെയ്‌മെന്റ് റിക്വസ്റ്റ് തയ്യാറാക്കുന്നു...")
    
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(args=['--no-sandbox', '--disable-dev-shm-usage'])
            browser_context = await browser.new_context(viewport={'width': 1366, 'height': 768})
            page = await browser_context.new_page()
            
            # networkidle-ന് പകരം domcontentloaded ഉപയോഗിച്ചു - പേജ് വളരെ വേഗം ലോഡ് ആകും
            await page.goto(URL, wait_until="domcontentloaded", timeout=60000)
            
            # 1. ഇമെയിൽ അതിവേഗം നൽകുന്നു (fill ഉപയോഗിച്ച്)
            all_inputs = page.locator('input')
            await all_inputs.first.wait_for(state="visible", timeout=10000)
            await all_inputs.first.fill("sanjuchacko628@gmail.com")
            
            # 2. Get it now ക്ലിക്ക് ചെയ്യുന്നു 
            get_btn = page.locator('button.checkout-proceed-cta').last
            await get_btn.click(force=True)
            
            # 3. UPI ഓപ്ഷൻ വന്നയുടനെ ക്ലിക്ക് ചെയ്യുന്നു
            upi_option = page.locator('text="UPI"').last
            await upi_option.wait_for(state="visible", timeout=10000)
            await upi_option.click(force=True)
            
            # 4. മൊബൈൽ നമ്പർ ഒറ്റയടിക്ക് നൽകുന്നു 
            upi_input = page.locator('input[placeholder*="Mobile No."]').last
            await upi_input.wait_for(state="visible", timeout=5000)
            await upi_input.fill(user_upi_id) 
            
            # Verify ലിങ്ക് വന്നാൽ ഉടൻ ക്ലിക്ക് ചെയ്യാൻ
            try:
                verify_link = page.locator('text="Verify"').last
                if await verify_link.is_visible(timeout=1000):
                    await verify_link.click(force=True)
                    await asyncio.sleep(1) # പച്ച ടിക്ക് വരാൻ ഒരു സെക്കൻഡ് മാത്രം
            except:
                pass
            
            # 5. Proceed ബട്ടൺ ക്ലിക്ക് ചെയ്യുന്നു
            proceed_btn = page.locator('button:has-text("Proceed"):visible').last
            await proceed_btn.wait_for(state="visible", timeout=5000)
            await proceed_btn.click(force=True)
            
            # 6. ടൈമർ വിൻഡോ വരാൻ കാത്തിരിക്കുന്നു
            try:
                await page.wait_for_selector('text="PAGE EXPIRES IN"', timeout=8000)
            except:
                if await proceed_btn.is_visible():
                    await proceed_btn.click(force=True)
                    await page.wait_for_selector('text="PAGE EXPIRES IN"', timeout=8000)
                
            # 7. ടൈമർ സ്ക്രീൻഷോട്ട് യൂസർക്ക് അയക്കുന്നു
            await page.screenshot(path="timer.png")
            # പഴയ ലോഡിങ് മെസ്സേജ് മായ്ക്കുന്നു (കൂടുതൽ വൃത്തിക്ക്)
            try: await msg.delete() 
            except: pass
            
            await update.message.reply_photo(
                photo=open("timer.png", 'rb'), 
                caption=f"✅ നിങ്ങളുടെ നമ്പറിലേക്ക് ( {user_upi_id} ) പെയ്‌മെന്റ് റിക്വസ്റ്റ് അയച്ചിട്ടുണ്ട്!\n\nദയവായി നിങ്ങളുടെ ആപ്പ് തുറന്ന് 8 മിനിറ്റിനുള്ളിൽ പെയ്‌മെന്റ് പൂർത്തിയാക്കുക."
            )
            
            # ---------------------------------------------------------
            # 8. പെയ്‌മെന്റ് സക്സസ് അതിവേഗം സ്കാൻ ചെയ്യുന്നു (ഓരോ 2 സെക്കൻഡിലും)
            # ---------------------------------------------------------
            payment_success = False
            
            for _ in range(240): # 240 തവണ x 2 സെക്കൻഡ് = 8 മിനിറ്റ്
                await asyncio.sleep(2) 
                
                try:
                    page_text = await page.content()
                    if any(success_text in page_text for success_text in ["Payment Successful", "Purchase successful", "Payment made successfully", "Successful"]):
                        payment_success = True
                        break 
                except:
                    pass
            
            if payment_success:
                await page.screenshot(path="success.png")
                await update.message.reply_photo(
                    photo=open("success.png", 'rb'),
                    caption="🎉 പെയ്‌മെന്റ് വിജയകരം! നിങ്ങളുടെ ഗെയിമിലേക്ക് റീചാർജ് തുക ആഡ് ചെയ്തു."
                )
            else:
                await update.message.reply_text("⏰ സമയം കഴിഞ്ഞു! പെയ്‌മെന്റ് ലഭിച്ചില്ല.")
            
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
    print("UPI Request Bot is Starting (High Speed Mode)...")
    application.run_polling()
