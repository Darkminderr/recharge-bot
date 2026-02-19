import os, asyncio, logging, re, requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from playwright.async_api import async_playwright
from flask import Flask, jsonify
from threading import Thread

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

app = Flask('')
TOKEN = '7510297537:AAEeCr_pl4CndrNCpBpr7Ac8mL3jlFKpyRk'
URL = "https://superprofile.bio/vp/6994a964b7a14d00133409f7"

# എപ്പോഴും /start അടിക്കുന്നത് ഒഴിവാക്കാൻ ഐഡി സേവ് ചെയ്യുന്നു
def get_admin_id():
    try:
        with open("admin_chat_id.txt", "r") as f:
            return f.read().strip()
    except:
        return None

def save_admin_id(chat_id):
    try:
        with open("admin_chat_id.txt", "w") as f:
            f.write(str(chat_id))
    except:
        pass

def send_msg(text):
    chat_id = get_admin_id()
    if chat_id:
        requests.get(f"https://api.telegram.org/bot{TOKEN}/sendMessage", params={'chat_id': chat_id, 'text': text})

def send_photo(photo_path, caption):
    chat_id = get_admin_id()
    if chat_id:
        with open(photo_path, 'rb') as f:
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", data={'chat_id': chat_id, 'caption': caption}, files={'photo': f})

async def playwright_task(user_upi_id):
    send_msg(f"⏳ ഡീറ്റെയിൽസ് എന്റർ ചെയ്യുന്നു... (നമ്പർ: {user_upi_id})")
    
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(args=['--no-sandbox', '--disable-dev-shm-usage'])
            browser_context = await browser.new_context(viewport={'width': 1366, 'height': 768})
            page = await browser_context.new_page()
            
            await page.goto(URL, wait_until="networkidle", timeout=60000)
            await asyncio.sleep(4)
            
            # 1. ഇമെയിൽ നൽകുന്നു (ഹിഡൻ ഇൻപുട്ടുകൾ ഒഴിവാക്കി സ്ക്രീനിൽ കാണുന്നതിൽ മാത്രം ക്ലിക്ക് ചെയ്യുന്നു)
            email_input = page.locator('input:visible').first
            await email_input.wait_for(state="visible", timeout=15000)
            await email_input.click(force=True)
            await page.keyboard.type("sanjuchacko628@gmail.com", delay=100)
            
            await asyncio.sleep(2)
            
            # 2. Get it now ക്ലിക്ക് ചെയ്യുന്നു
            get_btn = page.locator('button.checkout-proceed-cta:visible').last
            await get_btn.click(force=True)
            
            send_msg("⏳ പെയ്‌മെന്റ് ഗേറ്റ്‌വേയിലേക്ക് കണക്ട് ചെയ്യുന്നു...")
            await asyncio.sleep(6) 
            
            # 3. UPI ഓപ്ഷൻ ക്ലിക്ക് ചെയ്യുന്നു 
            upi_option = page.locator('text="UPI":visible').first
            await upi_option.wait_for(state="visible", timeout=15000)
            await upi_option.click(force=True)
            
            await asyncio.sleep(2)
            
            # 4. കൃത്യമായി മൊബൈൽ നമ്പർ നൽകുന്നു (user_upi_id)
            upi_input = page.locator('input[placeholder*="Mobile No."]:visible, input[placeholder*="UPI"]:visible').last
            if not await upi_input.is_visible():
                upi_input = page.locator('input:visible').last
                
            await upi_input.click(force=True)
            await page.keyboard.type(user_upi_id, delay=100)
            
            await asyncio.sleep(4)
            
            try:
                verify_link = page.locator('text="Verify":visible').last
                if await verify_link.is_visible(timeout=2000):
                    await verify_link.click(force=True)
                    await asyncio.sleep(3) 
            except:
                pass
            
            # 5. Proceed ബട്ടൺ കൃത്യമായി ക്ലിക്ക് ചെയ്യുന്നു 
            proceed_btn = page.locator('button:has-text("Proceed"):visible').last
            await proceed_btn.wait_for(state="visible", timeout=10000)
            await proceed_btn.click(force=True)
            
            send_msg("⏳ പെയ്‌മെന്റ് ടൈമർ വിൻഡോ ലോഡ് ആകുന്നു...")
            
            # 6. ടൈമർ വരാൻ കാത്തിരിക്കുന്നു
            try:
                await page.wait_for_selector('text="PAGE EXPIRES IN"', timeout=15000)
            except:
                if await proceed_btn.is_visible():
                    await proceed_btn.click(force=True)
                    await asyncio.sleep(4)
                
            # 7. ടൈമർ സ്ക്രീൻഷോട്ട് എടുത്ത് അയക്കുന്നു
            await page.screenshot(path="timer.png")
            send_photo("timer.png", f"✅ നിങ്ങളുടെ നമ്പറിലേക്ക് ( {user_upi_id} ) പെയ്‌മെന്റ് റിക്വസ്റ്റ് അയച്ചിട്ടുണ്ട്!\n\nദയവായി നിങ്ങളുടെ ആപ്പ് തുറന്ന് 8 മിനിറ്റിനുള്ളിൽ പെയ്‌മെന്റ് പൂർത്തിയാക്കുക.")
            
            # 8. പെയ്‌മെന്റ് സക്സസ് ആകാൻ സ്കാൻ ചെയ്യുന്നു (8 മിനിറ്റ്)
            payment_success = False
            for _ in range(240):
                await asyncio.sleep(2) 
                try:
                    page_text = await page.content()
                    if any(success_text in page_text for success_text in ["Payment Successful", "Purchase successful", "Payment made successfully", "Successful"]):
                        payment_success = True
                        break 
                except:
                    pass
            
            if payment_success:
                await asyncio.sleep(2) 
                await page.screenshot(path="success.png")
                send_photo("success.png", f"🎉 പെയ്‌മെന്റ് വിജയകരം! ({user_upi_id}) നിങ്ങളുടെ ഗെയിമിലേക്ക് റീചാർജ് തുക ആഡ് ചെയ്തു.")
            else:
                send_msg(f"⏰ 8 മിനിറ്റ് സമയം കഴിഞ്ഞു! {user_upi_id} എന്ന നമ്പറിൽ നിന്നും പെയ്‌മെന്റ് ലഭിച്ചില്ല.")
            
        except Exception as e:
            await page.screenshot(path="error.png")
            send_photo("error.png", f"❌ ഒരു തടസ്സം നേരിട്ടു: {str(e)}")
        finally:
            await browser.close()

def run_pw_thread(user_upi_id):
    asyncio.run(playwright_task(user_upi_id))

@app.route('/api/recharge/<mobile_number>')
def api_recharge(mobile_number):
    if not re.fullmatch(r'\d{10}', mobile_number):
        return jsonify({"status": "error", "message": "Invalid mobile number"}), 400
    if not get_admin_id():
        return jsonify({"status": "error", "message": "Admin chat ID not set. Send any message to bot in Telegram first."}), 400
        
    Thread(target=run_pw_thread, args=(mobile_number,)).start()
    return jsonify({"status": "success", "message": f"Recharge process started for {mobile_number}"})

@app.route('/')
def home(): return "UPI Request API Bot is Running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_admin_id(update.message.chat_id)
    await update.message.reply_text("✅ ബോട്ടിലേക്ക് കണക്ട് ചെയ്തു! ഇനി ഗെയിമിൽ നിന്നോ നേരിട്ടോ റീചാർജ് ചെയ്യാം.")

async def handle_direct_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_admin_id(update.message.chat_id)
    user_text = update.message.text.strip()
    if re.fullmatch(r'\d{10}', user_text):
        Thread(target=run_pw_thread, args=(user_text,)).start()
    else:
        await update.message.reply_text("⚠️ ദയവായി 10 അക്ക മൊബൈൽ നമ്പർ കൃത്യമായി നൽകുക.")

if __name__ == '__main__':
    Thread(target=run_flask).start()
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_direct_number))
    print("UPI Request Bot is Starting...")
    application.run_polling()
