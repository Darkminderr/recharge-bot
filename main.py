import os, asyncio, logging, re, requests, threading, random, time
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

EMAIL_LIST = [
    "qvqgauwbsb23e@gmail.com", "jaiwbvwab@gmail.com", "jaisjsnsn@gmail.com",
    "jaisnansn@gmail.com", "prkdksks@gmail.com", "jaiskannsms@gmail.com",
    "jaiakananssn@gmail.com", "jakoaksnsns@gmail.com", "jaiskasm@gmail.com",
    "jakoaoakaa@gmail.com", "jeowoalkssk@gmail.com", "jeiwoalkskek@gmail.com",
    "jwiwoaoals@gmail.com"
]

playwright_loop = asyncio.new_event_loop()
global_browser = None

# പുതിയ വേരിയബിൾ: ക്യൂ ട്രാക്ക് ചെയ്യാൻ
active_requests = 0 

def start_async_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

threading.Thread(target=start_async_loop, args=(playwright_loop,), daemon=True).start()

async def init_browser():
    global global_browser
    p = await async_playwright().start()
    global_browser = await p.chromium.launch(args=[
        '--no-sandbox', 
        '--disable-dev-shm-usage',
        '--disable-gpu'
    ])
    print("Master Browser Ready on Render!")

asyncio.run_coroutine_threadsafe(init_browser(), playwright_loop)

def send_msg(text):
    try:
        requests.get(f"https://api.telegram.org/bot{TOKEN}/sendMessage", params={'chat_id': ADMIN_CHAT_ID, 'text': text})
    except Exception as e:
        print(f"Telegram Msg Error: {e}")

def send_photo(photo_path, caption):
    try:
        if os.path.exists(photo_path):
            with open(photo_path, 'rb') as f:
                requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", data={'chat_id': ADMIN_CHAT_ID, 'caption': caption}, files={'photo': f})
        else:
            send_msg(caption)
    except Exception as e:
        print(f"Telegram Photo Error: {e}")

typing_semaphore = asyncio.Semaphore(2)

async def playwright_task(user_upi_id):
    global active_requests
    active_requests += 1
    
    # ക്യൂവിലുള്ള സ്ഥാനം കണ്ടുപിടിക്കുന്നു (ആദ്യത്തെ 2 പേർക്ക് ക്യൂ ഇല്ല)
    queue_pos = active_requests - 2
    
    if queue_pos > 0:
        send_msg(f"⏳ പുതിയ റിക്വസ്റ്റ് ക്യൂവിലാണ് (നമ്പർ: {user_upi_id}). വെയിറ്റിംഗ് ലിസ്റ്റ് സ്ഥാനം: {queue_pos}")
    else:
        send_msg(f"⚡ പുതിയ റിക്വസ്റ്റ് ലഭിച്ചു (നമ്പർ: {user_upi_id}). പ്രോസസ്സ് തുടങ്ങുന്നു...")
    
    timer_img = f"timer_{user_upi_id}.png"
    success_img = f"success_{user_upi_id}.png"
    error_img = f"error_{user_upi_id}.png"
    
    while global_browser is None:
        await asyncio.sleep(0.5)
        
    context = None
    page = None
    
    try:
        async with typing_semaphore:
            # ക്യൂവിൽ കാത്തുനിന്ന യൂസറിന്റെ ഊഴം എത്തുമ്പോൾ മെസ്സേജ് അയക്കുന്നു
            if queue_pos > 0:
                send_msg(f"🚀 ഊഴം എത്തി! ക്യൂവിൽ നിന്ന {user_upi_id} നമ്പറിന്റെ പ്രോസസ്സ് ഇപ്പോൾ ആരംഭിച്ചു.")
                
            context = await global_browser.new_context(viewport={'width': 1366, 'height': 768})
            page = await context.new_page()
            
            await page.goto(URL, wait_until="domcontentloaded", timeout=60000)
            
            selected_email = random.choice(EMAIL_LIST)
            
            all_inputs = page.locator('input')
            await all_inputs.first.wait_for(state="visible", timeout=30000)
            await all_inputs.first.click(force=True)
            await page.keyboard.type(selected_email, delay=0) 
            
            get_btn = page.locator('button.checkout-proceed-cta')
            await get_btn.last.click(force=True)
            
            upi_btn = page.locator('text="UPI"').last
            await upi_btn.wait_for(state="visible", timeout=30000)
            await upi_btn.click(force=True)
            
            upi_input = page.locator('input[placeholder*="Mobile No."]').last
            await upi_input.wait_for(state="visible", timeout=15000)
            await upi_input.click(force=True)
            await page.keyboard.type(user_upi_id, delay=0) 
            
            try:
                verify_link = page.locator('text="Verify"').last
                if await verify_link.is_visible(timeout=2000):
                    await verify_link.click(force=True)
            except:
                pass
            
            proceed_btn = page.locator('button:has-text("Proceed"):visible').last
            await proceed_btn.wait_for(state="visible", timeout=15000)
            await proceed_btn.click(force=True)
            
            try:
                await page.wait_for_selector('text="PAGE EXPIRES IN"', timeout=10000)
            except:
                if await proceed_btn.is_visible():
                    await proceed_btn.click(force=True)
                    
            await page.screenshot(path=timer_img)
            send_photo(timer_img, f"✅ പെയ്‌മെന്റ് റിക്വസ്റ്റ് അയച്ചു! ( {user_upi_id} )\n7 മിനിറ്റിനുള്ളിൽ പെയ്‌മെന്റ് പൂർത്തിയാക്കുക.")
            
            payment_success = False
            for _ in range(210):
                await asyncio.sleep(2) 
                try:
                    page_text = await page.content()
                    if any(success_text in page_text for success_text in ["Payment Successful", "Purchase successful", "Payment made successfully", "Successful"]):
                        payment_success = True
                        break 
                except:
                    pass
            
            if payment_success:
                payment_statuses[user_upi_id] = "Success"
                await asyncio.sleep(1)
                await page.screenshot(path=success_img)
                send_photo(success_img, f"🎉 പെയ്‌മെന്റ് വിജയകരം! ({user_upi_id})\nനിങ്ങളുടെ ഗെയിമിലേക്ക് റീചാർജ് തുക ആഡ് ചെയ്തു.")
            else:
                payment_statuses[user_upi_id] = "Failed"
                send_msg(f"⏰ 7 മിനിറ്റ് സമയം കഴിഞ്ഞു! {user_upi_id} നമ്പറിൽ നിന്നും പെയ്‌മെന്റ് ലഭിച്ചില്ല. റീചാർജ് ക്യാൻസൽ ചെയ്തു.")
        
    except Exception as e:
        payment_statuses[user_upi_id] = "Error"
        if page:
            try:
                await page.screenshot(path=error_img)
            except:
                pass
        send_photo(error_img, f"❌ ഒരു തടസ്സം നേരിട്ടു: {str(e)}\nനമ്പർ: {user_upi_id}")
    finally:
        # പ്രോസസ്സ് കഴിഞ്ഞാൽ ക്യൂവിൽ നിന്ന് ഒരാളെ കുറയ്ക്കുന്നു
        active_requests -= 1
        if context:
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
    # എപിഐ വഴി ക്യൂവിലുള്ള സ്ഥാനം ഗെയിമിലേക്കും കൊടുക്കാൻ താല്പര്യമുണ്ടെങ്കിൽ ഈ ഭാഗത്ത് മാറ്റം വരുത്താം.
    return jsonify({"mobile": mobile_number, "status": status})

@app.route('/')
def home(): return "UPI Request API Bot is Running 24/7 on Render (With Live Queue Tracking)!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def run_polling_with_retry():
    while True:
        try:
            asyncio.set_event_loop(asyncio.new_event_loop())
            application = ApplicationBuilder().token(TOKEN).build()
            application.add_handler(CommandHandler("start", start))
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_direct_number))
            print("Starting Telegram Polling...")
            application.run_polling(drop_pending_updates=True)
        except Exception as e:
            print(f"Telegram Polling crashed: {e}. Retrying in 5 seconds...")
            time.sleep(5)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ ബോട്ട് 24/7 ലൈവ് ആണ്! Live Queue Tracking ആക്റ്റീവ്.")

async def handle_direct_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text.strip()
    if re.fullmatch(r'\d{10}', user_text):
        payment_statuses[user_text] = "Pending"
        asyncio.run_coroutine_threadsafe(playwright_task(user_text), playwright_loop)
    else:
        await update.message.reply_text("⚠️ ദയവായി 10 അക്ക മൊബൈൽ നമ്പർ കൃത്യമായി നൽകുക.")

if __name__ == '__main__':
    threading.Thread(target=run_flask).start()
    print("UPI Request Bot API is starting...")
    run_polling_with_retry()
