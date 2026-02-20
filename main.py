import os, asyncio, logging, re, requests, threading, random, time
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from playwright.async_api import async_playwright
from flask import Flask, jsonify

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
app = Flask('')

TOKEN = '7510297537:AAEeCr_pl4CndrNCpBpr7Ac8mL3jlFKpyRk'
AMOUNT = "200"
URL_LIST = [
    "https://superprofile.bio/vp/6994aa10b7a14d0013343131",
    "https://superprofile.bio/vp/6994a9f46e580f00133ea7b4"
]
ADMIN_CHAT_ID = "1048415011"
payment_statuses = {}
EMAIL_LIST = ["qvqgauwbsb23e@gmail.com", "jaiwbvwab@gmail.com", "jaisjsnsn@gmail.com", "jaisnansn@gmail.com", "prkdksks@gmail.com", "jaiskannsms@gmail.com", "jaiakananssn@gmail.com", "jakoaksnsns@gmail.com", "jaiskasm@gmail.com", "jakoaoakaa@gmail.com", "jeowoalkssk@gmail.com", "jeiwoalkskek@gmail.com", "jwiwoaoals@gmail.com"]

playwright_loop = asyncio.new_event_loop()
global_browser = None
active_requests = 0

def start_async_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

threading.Thread(target=start_async_loop, args=(playwright_loop,), daemon=True).start()

async def init_browser():
    global global_browser
    p = await async_playwright().start()
    global_browser = await p.chromium.launch(args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu'])
    print(f"Browser Ready for Rs.{AMOUNT} Bot!")

asyncio.run_coroutine_threadsafe(init_browser(), playwright_loop)

def send_msg(text):
    try: requests.get(f"https://api.telegram.org/bot{TOKEN}/sendMessage", params={'chat_id': ADMIN_CHAT_ID, 'text': text})
    except: pass

def send_photo(photo_path, caption):
    try:
        if os.path.exists(photo_path):
            with open(photo_path, 'rb') as f: requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", data={'chat_id': ADMIN_CHAT_ID, 'caption': caption}, files={'photo': f})
        else: send_msg(caption)
    except: pass

typing_semaphore = asyncio.Semaphore(2)

async def playwright_task(user_upi_id):
    global active_requests
    active_requests += 1
    queue_pos = active_requests - 2
    
    if queue_pos > 0: send_msg(f"⏳ ക്യൂവിലാണ് ({user_upi_id} | ₹{AMOUNT}). സ്ഥാനം: {queue_pos}")
    else: send_msg(f"⚡ പ്രോസസ്സ് തുടങ്ങുന്നു ({user_upi_id} | ₹{AMOUNT})...")
    
    timer_img, success_img, error_img = f"t_{user_upi_id}.png", f"s_{user_upi_id}.png", f"e_{user_upi_id}.png"
    while global_browser is None: await asyncio.sleep(0.5)
    context, page = None, None
    
    try:
        async with typing_semaphore:
            if queue_pos > 0: send_msg(f"🚀 ഊഴം എത്തി! {user_upi_id} (₹{AMOUNT}) ആരംഭിച്ചു.")
            context = await global_browser.new_context(viewport={'width': 1366, 'height': 768})
            page = await context.new_page()
            
            await page.goto(random.choice(URL_LIST), wait_until="domcontentloaded", timeout=60000)
            all_inputs = page.locator('input')
            await all_inputs.first.wait_for(state="visible", timeout=30000)
            await all_inputs.first.click(force=True)
            await page.keyboard.type(random.choice(EMAIL_LIST), delay=0) 
            await page.locator('button.checkout-proceed-cta').last.click(force=True)
            
            upi_btn = page.locator('text="UPI"').last
            await upi_btn.wait_for(state="visible", timeout=30000)
            await upi_btn.click(force=True)
            
            upi_input = page.locator('input[placeholder*="Mobile No."]').last
            await upi_input.wait_for(state="visible", timeout=15000)
            await upi_input.click(force=True)
            await page.keyboard.type(user_upi_id, delay=0) 
            
            try:
                vl = page.locator('text="Verify"').last
                if await vl.is_visible(timeout=2000): await vl.click(force=True)
            except: pass
            
            proceed_btn = page.locator('button:has-text("Proceed"):visible').last
            await proceed_btn.wait_for(state="visible", timeout=15000)
            await proceed_btn.click(force=True)
            
            try: await page.wait_for_selector('text="PAGE EXPIRES IN"', timeout=10000)
            except:
                if await proceed_btn.is_visible(): await proceed_btn.click(force=True)
                    
            await page.screenshot(path=timer_img)
            send_photo(timer_img, f"✅ റിക്വസ്റ്റ് അയച്ചു! ({user_upi_id} | ₹{AMOUNT})\n3 മിനിറ്റിനുള്ളിൽ പൂർത്തിയാക്കുക.")
            
            payment_success = False
            for _ in range(90):
                await asyncio.sleep(2) 
                try:
                    if any(s in await page.content() for s in ["Payment Successful", "Purchase successful", "Payment made successfully", "Successful"]):
                        payment_success = True; break 
                except: pass
            
            if payment_success:
                payment_statuses[user_upi_id] = "Success"
                await asyncio.sleep(1)
                await page.screenshot(path=success_img)
                send_photo(success_img, f"🎉 വിജയകരം! ({user_upi_id})\n₹{AMOUNT} ആഡ് ചെയ്തു.")
            else:
                payment_statuses[user_upi_id] = "Failed"
                send_msg(f"⏰ 3 മിനിറ്റ് കഴിഞ്ഞു! {user_upi_id} (₹{AMOUNT}) ക്യാൻസൽ ചെയ്തു.")
        
    except Exception as e:
        payment_statuses[user_upi_id] = "Error"
        if page:
            try: await page.screenshot(path=error_img)
            except: pass
        send_photo(error_img, f"❌ എറർ: {str(e)}\nനമ്പർ: {user_upi_id}")
    finally:
        active_requests -= 1
        if context: await context.close()
        for img in [timer_img, success_img, error_img]:
            try: os.remove(img)
            except: pass

@app.route('/api/recharge/<mobile_number>')
def api_recharge(mobile_number):
    if not re.fullmatch(r'\d{10}', mobile_number): return jsonify({"status": "error"}), 400
    payment_statuses[mobile_number] = "Pending"
    asyncio.run_coroutine_threadsafe(playwright_task(mobile_number), playwright_loop)
    return jsonify({"status": "success"})

@app.route('/api/status/<mobile_number>')
def check_status(mobile_number): return jsonify({"mobile": mobile_number, "status": payment_statuses.get(mobile_number, "Not Found"), "amount": AMOUNT})

@app.route('/')
def home(): return f"Bot ₹{AMOUNT} is Running!"

def run_flask(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

def run_polling_with_retry():
    while True:
        try:
            asyncio.set_event_loop(asyncio.new_event_loop())
            application = ApplicationBuilder().token(TOKEN).build()
            application.add_handler(CommandHandler("start", lambda u,c: u.message.reply_text(f"✅ ₹{AMOUNT} ബോട്ട് ലൈവ് ആണ്!")))
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u,c: asyncio.run_coroutine_threadsafe(playwright_task(u.message.text.strip()), playwright_loop) if re.fullmatch(r'\d{10}', u.message.text.strip()) else u.message.reply_text("⚠️ 10 അക്ക നമ്പർ നൽകുക.")))
            application.run_polling(drop_pending_updates=True)
        except: time.sleep(5)

if __name__ == '__main__':
    threading.Thread(target=run_flask).start()
    run_polling_with_retry()
