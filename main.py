async def playwright_task(user_upi_id):
    send_msg(f"⚡ ഗെയിമിൽ നിന്നും പുതിയ റീചാർജ് റിക്വസ്റ്റ് വന്നിട്ടുണ്ട്! നമ്പർ: {user_upi_id}\nഅതിവേഗം പെയ്‌മെന്റ് തയ്യാറാക്കുന്നു...")
    
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(args=['--no-sandbox', '--disable-dev-shm-usage'])
            browser_context = await browser.new_context(viewport={'width': 1366, 'height': 768})
            page = await browser_context.new_page()
            
            await page.goto(URL, wait_until="domcontentloaded", timeout=60000)
            
            # 1. ഇമെയിൽ നൽകുന്നു
            all_inputs = page.locator('input')
            await all_inputs.first.wait_for(state="visible", timeout=10000)
            await all_inputs.first.fill("sanjuchacko628@gmail.com")
            
            # ഫിക്സ്: വെബ്സൈറ്റിന് ഇമെയിൽ പ്രോസസ്സ് ചെയ്യാൻ 1 സെക്കൻഡ് സമയം നൽകുന്നു
            await asyncio.sleep(1)
            
            # 2. Get it now ക്ലിക്ക് ചെയ്യുന്നു
            get_btn = page.locator('button.checkout-proceed-cta').last
            await get_btn.click(force=True)
            
            # ഫിക്സ്: പോപ്പ്-അപ്പ് വിൻഡോ കൃത്യമായി വരാൻ 3 സെക്കൻഡ് കാത്തിരിക്കുന്നു
            await asyncio.sleep(3)
            
            # 3. UPI ഓപ്ഷൻ ക്ലിക്ക് ചെയ്യുന്നു (സമയം 15000 ആയി കൂട്ടി)
            upi_option = page.locator('text="UPI"').last
            await upi_option.wait_for(state="visible", timeout=15000)
            await upi_option.click(force=True)
            
            # 4. മൊബൈൽ നമ്പർ നൽകുന്നു
            upi_input = page.locator('input[placeholder*="Mobile No."]').last
            await upi_input.wait_for(state="visible", timeout=5000)
            await upi_input.click(force=True)
            await page.keyboard.type(user_upi_id, delay=50) 
            
            await asyncio.sleep(2)
            try:
                verify_link = page.locator('text="Verify"').last
                if await verify_link.is_visible(timeout=1000):
                    await verify_link.click(force=True)
                    await asyncio.sleep(2)
            except: pass
            
            # 5. Proceed ബട്ടൺ ക്ലിക്ക് ചെയ്യുന്നു
            proceed_btn = page.locator('button:has-text("Proceed"):visible').last
            await proceed_btn.wait_for(state="visible", timeout=5000)
            await proceed_btn.click(force=True)
            
            try:
                await page.wait_for_selector('text="PAGE EXPIRES IN"', timeout=10000)
            except:
                if await proceed_btn.is_visible():
                    await proceed_btn.click(force=True)
                    await page.wait_for_selector('text="PAGE EXPIRES IN"', timeout=10000)
                
            await page.screenshot(path="timer.png")
            send_photo("timer.png", f"✅ ഗെയിമിലെ യൂസറുടെ നമ്പറിലേക്ക് ( {user_upi_id} ) പെയ്‌മെന്റ് റിക്വസ്റ്റ് അയച്ചു!\n8 മിനിറ്റിനുള്ളിൽ പെയ്‌മെന്റ് പൂർത്തിയാക്കാൻ കാത്തിരിക്കുന്നു.")
            
            payment_success = False
            for _ in range(240):
                await asyncio.sleep(2) 
                try:
                    page_text = await page.content()
                    if any(st in page_text for st in ["Payment Successful", "Purchase successful", "Payment made successfully", "Successful"]):
                        payment_success = True
                        break 
                except: pass
            
            if payment_success:
                await asyncio.sleep(1)
                await page.screenshot(path="success.png")
                send_photo("success.png", f"🎉 പെയ്‌മെന്റ് വിജയകരം! ({user_upi_id}) ഗെയിമിലേക്ക് റീചാർജ് ആഡ് ചെയ്യാവുന്നതാണ്.")
            else:
                send_msg(f"⏰ സമയം കഴിഞ്ഞു! {user_upi_id} എന്ന നമ്പറിൽ നിന്നും പെയ്‌മെന്റ് ലഭിച്ചില്ല.")
            
        except Exception as e:
            await page.screenshot(path="error.png")
            send_photo("error.png", f"❌ ഒരു തടസ്സം നേരിട്ടു: {str(e)}")
        finally:
            await browser.close()
