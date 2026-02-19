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

# ഫിക്സ്: ഓരോ നമ്പറിന്റെയും പെയ്‌മെന്റ് സ്റ്റാറ്റസ് സേവ് ചെയ്യാൻ ഒരു ഡിക്ഷണറി
payment_statuses = {}

def send_msg(text):
    requests.get(f"https://api.telegram.org/bot{TOKEN}/sendMessage", params={'chat_id': ADMIN_CHAT_ID, 'text': text})

def send_photo(photo_path, caption):
    with open(photo_path, 'rb') as f:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", data={'chat_id': ADMIN_CHAT_ID, 'caption': caption}, files={'photo': f})

async def playwright_task(user_upi_id):
    send_msg(f"⏳ ഡീറ്റെയിൽസ് എന്റർ ചെയ്യുന്നു... (നമ്പർ: {user_upi_id})")
    
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(args=['--no-sandbox', '--disable-dev-shm-usage'])
            browser_context = await browser.new_context(viewport={'width': 1366, 'height': 768})
            page = await browser_context.new_page()
            
            await page.goto(URL, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(2) 
            
            all_inputs = page.locator('input')
            await all_inputs.first.wait_for(state="visible", timeout=15000)
            await all_inputs.first.click(force=True)
            await page.keyboard.type("sanjuchacko628@gmail.com", delay=20)
            
            await asyncio.sleep(1)
            
            get_btn = page.locator('button.checkout-proceed-cta')
            await get_btn.last.click(force=True)
            
            send_msg("⏳ പെയ്‌മെന്റ് ഗേറ്റ്‌വേയിലേക്ക് കണക്ട് ചെയ്യുന്നു...")
            await asyncio.sleep(3) 
            
            await page.locator('text="UPI"').last.click(force=True)
            await asyncio.sleep(1.5) 
            
            upi_input = page.locator('input[placeholder*="Mobile No."]').last
            await upi_input.click(force=True)
            await page.keyboard.type(user_upi_id, delay=30)
            
            await asyncio.sleep(2) 
            
            try:
                verify_link = page.locator('text="Verify"').last
                if await verify_link.is_visible(timeout=2000):
                    await verify_link.click(force=True)
                    await asyncio.sleep(2) 
            except:
                pass
            
            proceed_btn = page.locator('button:has-text("Proceed"):visible').last
            await proceed_btn.wait_for(state="visible", timeout=10000)
            await proceed_btn.click(force=True)
            
            send_msg("⏳ പെയ്‌മെന്റ് ടൈമർ വിൻഡോ ലോഡ് ആകുന്നു...")
            
            try:
                await page.wait_for_selector('text="PAGE EXPIRES IN"', timeout=10000)
            except:
                if await proceed_btn.is_visible():
                    await proceed_btn.click(force=True)
                    await asyncio.sleep(2)
                
            await page.screenshot(path="timer.png")
            send_photo("timer.png", f"✅ നിങ്ങളുടെ നമ്പറിലേക്ക് ( {user_upi_id} ) പെയ്‌മെന്റ് റിക്വസ്റ്റ് അയച്ചിട്ടുണ്ട്!\n\nദയവായി നിങ്ങളുടെ ആപ്പ് തുറന്ന് 8 മിനിറ്റിനുള്ളിൽ പെയ്‌മെന്റ് പൂർത്തിയാക്കുക.")
            
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
                # ഫിക്സ്: പെയ്‌മെന്റ് സക്സസ് ആയാൽ സ്റ്റാറ്റസ് അപ്ഡേറ്റ് ചെയ്യുന്നു
                payment_statuses[user_upi_id] = "Success"
                await asyncio.sleep(1) 
                await page.screenshot(path="success.png")
                send_photo("success.png", f"🎉 പെയ്‌മെന്റ് വിജയകരം! ({user_upi_id}) നിങ്ങളുടെ ഗെയിമിലേക്ക് റീചാർജ് തുക ആഡ് ചെയ്തു.")
            else:
                # ഫിക്സ്: സമയം കഴിഞ്ഞാൽ Failed ആക്കുന്നു
                payment_statuses[user_upi_id] = "Failed"
                send_msg(f"⏰ 8 മിനിറ്റ് സമയം കഴിഞ്ഞു! {user_upi_id} എന്ന നമ്പറിൽ നിന്നും പെയ്‌മെന്റ് ലഭിച്ചില്ല.")
            
        except Exception as e:
            # ഫിക്സ്: എറർ വന്നാൽ അതും സേവ് ചെയ്യുന്നു
            payment_statuses[user_upi_id] = "Error"
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
    
    # ഫിക്സ്: റീചാർജ് തുടങ്ങുമ്പോൾ തന്നെ Pending എന്ന് സെറ്റ് ചെയ്യുന്നു
    payment_statuses[mobile_number] = "Pending"
    Thread(target=run_pw_thread, args=(mobile_number,)).start()
    return jsonify({"status": "success", "message": f"Recharge process started for {mobile_number}"})

# ഫിക്സ്: ഗെയിമിന് പെയ്‌മെന്റ് സ്റ്റാറ്റസ് ചെക്ക് ചെയ്യാനുള്ള പുതിയ API ലിങ്ക്
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
    await update.message.reply_text("✅ ബോട്ട് 24/7 ലൈവ് ആണ്! ഇനി /start അടിക്കേണ്ട ആവശ്യമില്ല.")

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
    print("UPI Request Bot is Starting with 24/7 config...")
    application.run_polling()
