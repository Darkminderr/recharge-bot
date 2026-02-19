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
ADMIN_CHAT_ID = "1048415011" 

payment_statuses = {}

def send_msg(text):
    requests.get(f"https://api.telegram.org/bot{TOKEN}/sendMessage", params={'chat_id': ADMIN_CHAT_ID, 'text': text})

def send_photo(photo_path, caption):
    with open(photo_path, 'rb') as f:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", data={'chat_id': ADMIN_CHAT_ID, 'caption': caption}, files={'photo': f})

async def playwright_task(user_upi_id):
    send_msg(f"⚡ അതിവേഗ പ്രോസസ്സിംഗ് തുടങ്ങുന്നു... (നമ്പർ: {user_upi_id})")
    
    timer_img = f"timer_{user_upi_id}.png"
    success_img = f"success_{user_upi_id}.png"
    error_img = f"error_{user_upi_id}.png"
    
    async with async_playwright() as p:
        try:
            # ഫിക്സ് 1: ചിത്രങ്ങൾ ഒഴിവാക്കി ബ്രൗസർ സൂപ്പർ ഫാസ്റ്റ് ആക്കുന്നു
            browser = await p.chromium.launch(args=[
                '--no-sandbox', 
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--blink-settings=imagesEnabled=false' 
            ])
            browser_context = await browser.new_context(viewport={'width': 1366, 'height': 768})
            page = await browser_context.new_page()
            
            await page.goto(URL, wait_until="domcontentloaded", timeout=60000)
            
            # ഫിക്സ് 2: വെറുതെയുള്ള കാത്തിരിപ്പുകൾ ഒഴിവാക്കി, സ്പീഡിൽ ടൈപ്പ് ചെയ്യുന്നു
            all_inputs = page.locator('input')
            await all_inputs.first.wait_for(state="visible", timeout=10000)
            await all_inputs.first.click(force=True)
            await page.keyboard.type("sanjuchacko628@gmail.com", delay=0) # 0 ഡിലേ!
            
            get_btn = page.locator('button.checkout-proceed-cta')
            await get_btn.last.click(force=True)
            
            # UPI ബട്ടൺ വന്നാൽ ഉടനെ ക്ലിക്ക് ചെയ്യുക (സ്മാർട്ട് വെയിറ്റിംഗ്)
            upi_btn = page.locator('text="UPI"').last
            await upi_btn.wait_for(state="visible", timeout=8000)
            await upi_btn.click(force=True)
            
            upi_input = page.locator('input[placeholder*="Mobile No."]').last
            await upi_input.wait_for(state="visible", timeout=5000)
            await upi_input.click(force=True)
            await page.keyboard.type(user_upi_id, delay=0) # 0 ഡിലേ!
            
            try:
                verify_link = page.locator('text="Verify"').last
                if await verify_link.is_visible(timeout=1000):
                    await verify_link.click(force=True)
            except:
                pass
            
            proceed_btn = page.locator('button:has-text("Proceed"):visible').last
            await proceed_btn.wait_for(state="visible", timeout=5000)
            await proceed_btn.click(force=True)
            
            try:
                await page.wait_for_selector('text="PAGE EXPIRES IN"', timeout=10000)
            except:
                if await proceed_btn.is_visible():
                    await proceed_btn.click(force=True)
                
            await page.screenshot(path=timer_img)
            send_photo(timer_img, f"✅ പെയ്‌മെന്റ് റിക്വസ്റ്റ് അയച്ചു! ( {user_upi_id} )\n8 മിനിറ്റിനുള്ളിൽ പെയ്‌മെന്റ് പൂർത്തിയാക്കുക.")
            
            # ഫിക്സ് 3: പെയ്‌മെന്റ് സക്സസ് സ്കാനിങ് അതിവേഗത്തിലാക്കി (ഓരോ 1 സെക്കൻഡിലും)
            payment_success = False
            for _ in range(480):
                await asyncio.sleep(1) 
                try:
                    page_text = await page.content()
                    if any(success_text in page_text for success_text in ["Payment Successful", "Purchase successful", "Payment made successfully", "Successful"]):
                        payment_success = True
                        break 
                except:
                    pass
            
            if payment_success:
                payment_statuses[user_upi_id] = "Success"
                await page.screenshot(path=success_img)
                send_photo(success_img, f"🎉 പെയ്‌മെന്റ് വിജയകരം! ({user_upi_id})")
            else:
                payment_statuses[user_upi_id] = "Failed"
                send_msg(f"⏰ സമയം കഴിഞ്ഞു! {user_upi_id} നമ്പറിൽ നിന്നും പെയ്‌മെന്റ് ലഭിച്ചില്ല.")
            
        except Exception as e:
            payment_statuses[user_upi_id] = "Error"
            await page.screenshot(path=error_img)
            send_photo(error_img, f"❌ ഒരു തടസ്സം നേരിട്ടു: {str(e)}\nനമ്പർ: {user_upi_id}")
        finally:
            await browser.close()
            for img in [timer_img, success_img, error_img]:
                try:
                    if os.path.exists(img):
                        os.remove(img)
                except:
                    pass

def run_pw_thread(user_upi_id):
    asyncio.run(playwright_task(user_upi_id))

@app.route('/api/recharge/<mobile_number>')
def api_recharge(mobile_number):
    if not re.fullmatch(r'\d{10}', mobile_number):
        return jsonify({"status": "error", "message": "Invalid mobile number"}), 400
    
    payment_statuses[mobile_number] = "Pending"
    Thread(target=run_pw_thread, args=(mobile_number,)).start()
    return jsonify({"status": "success", "message": f"Recharge process started for {mobile_number}"})

@app.route('/api/status/<mobile_number>')
def check_status(mobile_number):
    status = payment_statuses.get(mobile_number, "Not Found")
    return jsonify({"mobile": mobile_number, "status": status})

@app.route('/')
def home(): return "UPI Request API Bot is Running 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ ബോട്ട് 24/7 ലൈവ് ആണ്! അതിവേഗ മോഡ് ആക്റ്റീവ്.")

async def handle_direct_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text.strip()
    if re.fullmatch(r'\d{10}', user_text):
        payment_statuses[user_text] = "Pending"
        Thread(target=run_pw_thread, args=(user_text,)).start()
    else:
        await update.message.reply_text("⚠️ ദയവായി 10 അക്ക മൊബൈൽ നമ്പർ കൃത്യമായി നൽകുക.")

if __name__ == '__main__':
    Thread(target=run_flask).start()
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_direct_number))
    print("UPI Request Bot is Starting in SUPER FAST Mode...")
    application.run_polling()
