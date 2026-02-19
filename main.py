import os, asyncio, logging, re, requests, threading
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from playwright.async_api import async_playwright
from flask import Flask, jsonify

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

app = Flask('')
TOKEN = '7510297537:AAEeCr_pl4CndrNCpBpr7Ac8mL3jlFKpyRk'
URL = "https://superprofile.bio/vp/6994a964b7a14d00133409f7"
ADMIN_CHAT_ID = "1048415011" 

payment_statuses = {}

playwright_loop = asyncio.new_event_loop()
global_browser = None

def start_async_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

threading.Thread(target=start_async_loop, args=(playwright_loop,), daemon=True).start()

async def init_browser():
    global global_browser
    p = await async_playwright().start()
    # ഫിക്സ് 1: ഇമേജുകൾ ലോഡ് ആകാൻ വേണ്ടി പഴയ സെറ്റിങ്സ് തിരികെ വെച്ചു
    global_browser = await p.chromium.launch(args=[
        '--no-sandbox', 
        '--disable-dev-shm-usage',
        '--disable-gpu'
    ])
    print("Master Browser Ready with Images Enabled!")

asyncio.run_coroutine_threadsafe(init_browser(), playwright_loop)

def send_msg(text):
    requests.get(f"https://api.telegram.org/bot{TOKEN}/sendMessage", params={'chat_id': ADMIN_CHAT_ID, 'text': text})

def send_photo(photo_path, caption):
    with open(photo_path, 'rb') as f:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", data={'chat_id': ADMIN_CHAT_ID, 'caption': caption}, files={'photo': f})

typing_semaphore = asyncio.Semaphore(2)

async def playwright_task(user_upi_id):
    send_msg(f"⚡ റീചാർജ് പ്രോസസ്സ് തുടങ്ങുന്നു... (നമ്പർ: {user_upi_id})")
    
    timer_img = f"timer_{user_upi_id}.png"
    success_img = f"success_{user_upi_id}.png"
    error_img = f"error_{user_upi_id}.png"
    
    while global_browser is None:
        await asyncio.sleep(0.5)
        
    context = await global_browser.new_context(viewport={'width': 1366, 'height': 768})
    page = await context.new_page()
    
    try:
        async with typing_semaphore:
            await page.goto(URL, wait_until="domcontentloaded", timeout=60000)
            
            all_inputs = page.locator('input')
            await all_inputs.first.wait_for(state="visible", timeout=15000)
            await all_inputs.first.click(force=True)
            await page.keyboard.type("sanjuchacko628@gmail.com", delay=0) 
            
            get_btn = page.locator('button.checkout-proceed-cta')
            await get_btn.last.click(force=True)
            
            upi_btn = page.locator('text="UPI"').last
            await upi_btn.wait_for(state="visible", timeout=10000)
            await upi_btn.click(force=True)
            
            upi_input = page.locator('input[placeholder*="Mobile No."]').last
            await upi_input.wait_for(state="visible", timeout=5000)
            await upi_input.click(force=True)
            await page.keyboard.type(user_upi_id, delay=0) 
            
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
        # ഫിക്സ് 2: മെസ്സേജിൽ 7 മിനിറ്റ് ആക്കി മാറ്റി
        send_photo(timer_img, f"✅ പെയ്‌മെന്റ് റിക്വസ്റ്റ് അയച്ചു! ( {user_upi_id} )\n7 മിനിറ്റിനുള്ളിൽ പെയ്‌മെന്റ് പൂർത്തിയാക്കുക.")
        
        payment_success = False
        # ഫിക്സ് 3: 420 സെക്കൻഡുകൾ (7 മിനിറ്റ്) സ്കാൻ ചെയ്യുന്നു
        for _ in range(420):
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
            await asyncio.sleep(0.5)
            await page.screenshot(path=success_img)
            send_photo(success_img, f"🎉 പെയ്‌മെന്റ് വിജയകരം! ({user_upi_id})\nനിങ്ങളുടെ ഗെയിമിലേക്ക് റീചാർജ് തുക ആഡ് ചെയ്തു.")
        else:
            payment_statuses[user_upi_id] = "Failed"
            send_msg(f"⏰ 7 മിനിറ്റ് സമയം കഴിഞ്ഞു! {user_upi_id} നമ്പറിൽ നിന്നും പെയ്‌മെന്റ് ലഭിച്ചില്ല. റീചാർജ് ക്യാൻസൽ ചെയ്തു.")
        
    except Exception as e:
        payment_statuses[user_upi_id] = "Error"
        await page.screenshot(path=error_img)
        send_photo(error_img, f"❌ ഒരു തടസ്സം നേരിട്ടു: {str(e)}\nനമ്പർ: {user_upi_id}")
    finally:
        await context.close()
        for img in [timer_img, success_img, error_img]:
            try:
                if os.path.exists(img): os.remove(img)
            except: pass

@app.route('/api/recharge/<mobile_number>')
def api_recharge(mobile_number):
    if not re.fullmatch(r'\d{10}', mobile_number):
        return jsonify({"status": "error", "message": "Invalid mobile number"}), 400
    
    payment_statuses[mobile_number] = "Pending"
    asyncio.run_coroutine_threadsafe(playwright_task(mobile_number), playwright_loop)
    return jsonify({"status": "success", "message": f"Recharge process started for {mobile_number}"})

@app.route('/api/status/<mobile_number>')
def check_status(mobile_number):
    status = payment_statuses.get(mobile_number, "Not Found")
    return jsonify({"mobile": mobile_number, "status": status})

@app.route('/')
def home(): return "UPI Request API Bot is Running 24/7 (High Concurrency Mode)!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ ബോട്ട് 24/7 ലൈവ് ആണ്! മാസ്റ്റർ ബ്രൗസർ ആക്റ്റീവ്.")

async def handle_direct_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text.strip()
    if re.fullmatch(r'\d{10}', user_text):
        payment_statuses[user_text] = "Pending"
        asyncio.run_coroutine_threadsafe(playwright_task(user_text), playwright_loop)
    else:
        await update.message.reply_text("⚠️ ദയവായി 10 അക്ക മൊബൈൽ നമ്പർ കൃത്യമായി നൽകുക.")

if __name__ == '__main__':
    threading.Thread(target=run_flask).start()
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_direct_number))
    print("UPI Request Bot is Starting with Master Browser Config...")
    application.run_polling()
