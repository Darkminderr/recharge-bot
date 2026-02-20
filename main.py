import os, asyncio, logging, re, requests, threading, random, time
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from playwright.async_api import async_playwright
from flask import Flask, jsonify

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
app = Flask('')

TOKEN = '7510297537:AAEeCr_pl4CndrNCpBpr7Ac8mL3jlFKpyRk'

# URL_LIST മാറ്റി 200 നും 2000 നും ഉള്ള ലിങ്കുകൾ നൽകി
URLS = {
    "200": [
        "https://superprofile.bio/vp/6994aa10b7a14d0013343131",
        "https://superprofile.bio/vp/6994a9f46e580f00133ea7b4"
    ],
    "2000": [
        "https://superprofile.bio/vp/6994a9a6b7a14d0013341920",
        "https://superprofile.bio/vp/6994a9d0b7a14d00133422cd"
    ]
}

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
    print("Browser Ready for Rs.200 and Rs.2000 Bot!")

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

async def playwright_task(user_upi_id, amount):
    global active_requests
    active_requests += 1
    queue_pos = active_requests - 2
    
    if queue_pos > 0: send_msg(f"⏳ ക്യൂവിലാണ് ({user_upi_id} | ₹{amount}). സ്ഥാനം: {queue_pos}")
    else: send_msg(f"⚡ പ്രോസസ്സ് തുടങ്ങുന്നു ({user_upi_id} | ₹{amount})...")
    
    timer_img, success_img, error_img = f"t_{user_upi_id}.png", f"s_{user_upi_id}.png", f"e_{user_upi_id}.png"
    while global_browser is None: await asyncio.sleep(0.5)
    context, page = None, None
    
    try:
        async with typing_semaphore:
            if queue_pos > 0: send_msg(f"🚀 ഊഴം എത്തി! {user_upi_id} (₹{amount}) ആരംഭിച്ചു.")
            context = await global_browser.new_context(viewport={'width': 1366, 'height': 768})
            page = await context.new_page()
            
            # എമൗണ്ട് അനുസരിച്ചുള്ള ലിങ്ക് എടുക്കാൻ മാറ്റി
            await page.goto(random.choice(URLS[amount]), wait_until="domcontentloaded", timeout=60000)
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
            send_photo(timer_img, f"✅ റിക്വസ്റ്റ് അയച്ചു! ({user_upi_id} | ₹{amount})\n3 മിനിറ്റിനുള്ളിൽ പൂർത്തിയാക്കുക.")
            
            payment_success = False
            for _ in range(90):
                await asyncio.sleep(2) 
                try:
                    if any(s in await page.content() for s in ["Payment Successful", "Purchase successful", "Payment made successfully", "Successful"]):
                        payment_success = True; break 
                except: pass
            
            if payment_success:
                payment_statuses[user_upi_id] = {"status": "Success", "amount": amount}
                await asyncio.sleep(1)
                await page.screenshot(path=success_img)
                send_photo(success_img, f"🎉 വിജയകരം! ({user_upi_id})\n₹{amount} ആഡ് ചെയ്തു.")
            else:
                payment_statuses[user_upi_id] = {"status": "Failed", "amount": amount}
                send_msg(f"⏰ 3 മിനിറ്റ് കഴിഞ്ഞു! {user_upi_id} (₹{amount}) ക്യാൻസൽ ചെയ്തു.")
        
    except Exception as e:
        payment_statuses[user_upi_id] = {"status": "Error", "amount": amount}
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

# API ലിങ്കിൽ എമൗണ്ട് കൂടി ചേർത്തു
@app.route('/api/recharge/<amount>/<mobile_number>')
def api_recharge(amount, mobile_number):
    if amount not in URLS: return jsonify({"status": "error", "message": "Invalid amount"}), 400
    if not re.fullmatch(r'\d{10}', mobile_number): return jsonify({"status": "error"}), 400
    
    payment_statuses[mobile_number] = {"status": "Pending", "amount": amount}
    asyncio.run_coroutine_threadsafe(playwright_task(mobile_number, amount), playwright_loop)
    return jsonify({"status": "success", "amount": amount})

@app.route('/api/status/<mobile_number>')
def check_status(mobile_number): 
    data = payment_statuses.get(mobile_number, {"status": "Not Found", "amount": "0"})
    if isinstance(data, str): 
        return jsonify({"mobile": mobile_number, "status": data, "amount": "Unknown"})
    return jsonify({"mobile": mobile_number, "status": data["status"], "amount": data["amount"]})

@app.route('/')
def home(): return "Bot (Rs.200 & Rs.2000) is Running!"

def run_flask(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

def run_polling_with_retry():
    while True:
        try:
            asyncio.set_event_loop(asyncio.new_event_loop())
            application = ApplicationBuilder().token(TOKEN).build()
            application.add_handler(CommandHandler("start", lambda u,c: u.message.reply_text("✅ 200 & 2000 ബോട്ട് ലൈവ് ആണ്!")))
            
            # ടെലിഗ്രാമിൽ എമൗണ്ട് വെച്ച് നമ്പർ കൊടുക്കാൻ മാറ്റി
            async def handle_text(u, c):
                text = u.message.text.strip().split()
                if len(text) == 2 and text[0] in URLS and re.fullmatch(r'\d{10}', text[1]):
                    amount, mobile = text[0], text[1]
                    payment_statuses[mobile] = {"status": "Pending", "amount": amount}
                    asyncio.run_coroutine_threadsafe(playwright_task(mobile, amount), playwright_loop)
                else:
                    await u.message.reply_text("⚠️ ദയവായി എമൗണ്ടും നമ്പറും ചേർത്ത് നൽകുക. ഉദാഹരണത്തിന്:\n200 9876543210\nഅല്ലെങ്കിൽ\n2000 9876543210")
                    
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
            application.run_polling(drop_pending_updates=True)
        except: time.sleep(5)

if __name__ == '__main__':
    threading.Thread(target=run_flask).start()
    run_polling_with_retry()
