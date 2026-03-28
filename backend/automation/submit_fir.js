const puppeteer = require('puppeteer');
const fs = require('fs');

const data = JSON.parse(fs.readFileSync('formData.json', 'utf-8'));

// ─── Helpers ──────────────────────────────────────────────────────────────────

async function fillInput(page, selector, value) {
  try {
    await page.waitForSelector(selector, { timeout: 5000 });
    await page.focus(selector);
    // Clear existing text just in case (e.g., if there's a default value)
    await page.click(selector, { clickCount: 3 });
    await page.keyboard.press('Backspace');
    // Type with a minimal delay to ensure "letter by letter" visual
    await page.type(selector, String(value), { delay: 10 });
    console.log(`✅ Filled input (typed): ${selector}`);
  } catch {
    console.log(`⚠️  Skipped input: ${selector}`);
  }
}

async function fillTextarea(page, selector, value) {
  try {
    await page.waitForSelector(selector, { timeout: 5000 });
    await page.focus(selector);
    // Clear existing text
    await page.click(selector, { clickCount: 3 });
    await page.keyboard.press('Backspace');
    // Type with delay
    await page.type(selector, String(value), { delay: 10 });
    console.log(`✅ Filled textarea (typed): ${selector}`);
  } catch {
    console.log(`⚠️  Skipped textarea: ${selector}`);
  }
}

async function fillSelect(page, selector, value) {
  try {
    await page.waitForSelector(selector, { timeout: 5000 });
    await page.evaluate((sel, val) => {
      const el = document.querySelector(sel);
      if (!el) return;
      const nativeSetter = Object.getOwnPropertyDescriptor(
        window.HTMLSelectElement.prototype, 'value'
      ).set;
      nativeSetter.call(el, val);
      el.dispatchEvent(new Event('input', { bubbles: true }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
    }, selector, String(value));
    console.log(`✅ Set select: ${selector} → ${value}`);
  } catch {
    console.log(`⚠️  Skipped select: ${selector}`);
  }
}

async function clickRadio(page, selector) {
  try {
    await page.waitForSelector(selector, { timeout: 5000 });
    await page.click(selector);
    console.log(`✅ Clicked radio: ${selector}`);
  } catch {
    console.log(`⚠️  Skipped radio: ${selector}`);
  }
}

async function clickTab(page, selector) {
  await page.waitForSelector(selector, { timeout: 8000 });
  await page.click(selector);
  await new Promise(r => setTimeout(r, 500));
}

// ─── Overlay ──────────────────────────────────────────────────────────────────

async function ensureOverlay(page) {
  await page.evaluate(() => {
    if (document.getElementById('ai-helper-overlay')) return;
    const overlay = document.createElement('div');
    overlay.id = 'ai-helper-overlay';
    overlay.innerHTML = `
      <div id="ai-box" style="
        position:fixed; top:20px; right:20px;
        background:rgba(0,0,0,0.9); color:white;
        padding:15px; border-radius:12px; z-index:999999;
        width:290px; font-family:Arial; font-size:13px;
        box-shadow:0 0 15px rgba(0,0,0,0.5); cursor:move;
      ">
        <div id="ai-title" style="font-weight:bold;color:#00ffd5;margin-bottom:8px;">🤖 AI Assistant</div>
        <div id="ai-message">Initializing...</div>
      </div>`;
    document.body.appendChild(overlay);

    const box = document.getElementById('ai-box');
    let isDragging = false, offsetX = 0, offsetY = 0;
    box.addEventListener('mousedown', e => {
      isDragging = true;
      offsetX = e.clientX - box.getBoundingClientRect().left;
      offsetY = e.clientY - box.getBoundingClientRect().top;
      box.style.transition = 'none';
    });
    document.addEventListener('mousemove', e => {
      if (isDragging) {
        box.style.left = (e.clientX - offsetX) + 'px';
        box.style.top  = (e.clientY - offsetY) + 'px';
        box.style.right = 'auto';
      }
    });
    document.addEventListener('mouseup', () => { isDragging = false; });
  });
}

async function updateOverlay(page, msg, color = 'white') {
  await ensureOverlay(page);
  await page.evaluate((m, c) => {
    const el = document.getElementById('ai-message');
    if (el) { el.innerText = m; el.style.color = c; }
  }, msg, color);
}

// ─── Form Sections ────────────────────────────────────────────────────────────

async function fillPersonalInformation(page, pi) {
  console.log('\n📋 Filling: Personal Information');
  await clickTab(page, '#subtab-personalInformation');
  await updateOverlay(page, '📋 Filling Personal Information...', '#00ffd5');

  if (pi.uid)                await fillInput(page, '#pi-uid', pi.uid);
  if (pi.firstName)          await fillInput(page, '#pi-first-name', pi.firstName);
  if (pi.middleName)         await fillInput(page, '#pi-middle-name', pi.middleName);
  if (pi.lastName)           await fillInput(page, '#pi-last-name', pi.lastName);
  if (pi.natureOfComplaint)  await fillInput(page, '#pi-nature-of-complaint', pi.natureOfComplaint);
  if (pi.emailId)            await fillInput(page, '#pi-email', pi.emailId);
  if (pi.mobileCountryCode)  await fillInput(page, '#pi-mobile-cc', pi.mobileCountryCode);
  if (pi.mobileNo)           await fillInput(page, '#pi-mobile-no', pi.mobileNo);
  if (pi.landlineStd)        await fillInput(page, '#pi-landline-std', pi.landlineStd);
  if (pi.landlineCode)       await fillInput(page, '#pi-landline-code', pi.landlineCode);
  if (pi.landlineNo)         await fillInput(page, '#pi-landline-no', pi.landlineNo);
  if (pi.dateOfBirth)        await fillInput(page, '#pi-dob', pi.dateOfBirth);
}

async function fillAddress(page, addr) {
  console.log('\n📋 Filling: Address');
  await clickTab(page, '#subtab-address');
  await updateOverlay(page, '📋 Filling Address Details...', '#00ffd5');

  if (addr.houseNo)        await fillInput(page, '#addr-house', addr.houseNo);
  if (addr.streetName)     await fillInput(page, '#addr-street', addr.streetName);
  if (addr.colony)         await fillInput(page, '#addr-colony', addr.colony);
  if (addr.village)        await fillInput(page, '#addr-village', addr.village);
  if (addr.tehsil)         await fillInput(page, '#addr-tehsil', addr.tehsil);
  if (addr.country)        await fillInput(page, '#addr-country', addr.country);
  if (addr.state)          await fillInput(page, '#addr-state', addr.state);
  if (addr.district)       await fillInput(page, '#addr-district', addr.district);
  if (addr.policeStation)  await fillSelect(page, '#addr-police-station', addr.policeStation);
  if (addr.pincode)        await fillInput(page, '#addr-pincode', addr.pincode);
}

async function fillIdentification(page, ident) {
  console.log('\n📋 Filling: Identification');
  await clickTab(page, '#subtab-identification');
  await updateOverlay(page, '📋 Filling Identification...', '#00ffd5');

  if (ident.countryOfNationality) {
    await fillSelect(page, '#id-country-nationality', ident.countryOfNationality);
  }

  if (ident.records && ident.records.length > 0) {
    for (const record of ident.records) {
      await fillSelect(page, '#id-type', record.type);
      await fillInput(page, '#id-number', record.number);
      await page.click('#id-btn-add');
      await new Promise(r => setTimeout(r, 400));
      console.log(`✅ Added identification: ${record.type} → ${record.number}`);
    }
  }
}

async function fillAccusedDetail(page, accused) {
  console.log('\n📋 Filling: Accused Detail');
  await clickTab(page, '#tab-accusedDetail');
  await updateOverlay(page, '📋 Filling Accused Details...', '#00ffd5');

  for (const person of accused) {
    await page.click('#accused-btn-add-new');
    await new Promise(r => setTimeout(r, 400));
    if (person.name)    await fillInput(page, '#accused-name', person.name);
    if (person.address) await fillInput(page, '#accused-address', person.address);
    await page.click('#accused-btn-save');
    await new Promise(r => setTimeout(r, 400));
    console.log(`✅ Added accused: ${person.name}`);
  }
}

async function fillIncidentDetail(page, incident) {
  console.log('\n📋 Filling: Incident Detail');
  await clickTab(page, '#tab-incidentDetail');
  await updateOverlay(page, '📋 Filling Incident Details...', '#00ffd5');

  if (incident.placeOfIncident) await fillTextarea(page, '#incident-place', incident.placeOfIncident);
  if (incident.typeOfIncident)  await fillTextarea(page, '#incident-type', incident.typeOfIncident);

  if (incident.isDateTimeKnown === 'no') {
    await clickRadio(page, '#incident-datetime-known-no');
  } else {
    await clickRadio(page, '#incident-datetime-known-yes');
  }

  if (incident.incidentDate) await fillInput(page, '#incident-date', incident.incidentDate);
  if (incident.incidentTime) await fillInput(page, '#incident-time', incident.incidentTime);
}

async function fillComplaintSubmission(page, sub) {
  console.log('\n📋 Filling: Complaint Submission Details');
  await clickTab(page, '#tab-complaintSubmissionDetails');
  await updateOverlay(page, '📋 Filling Submission Details...', '#00ffd5');

  if (sub.knowPoliceStation === 'no') {
    await clickRadio(page, '#sub-know-ps-no');
  } else {
    await clickRadio(page, '#sub-know-ps-yes');
  }

  if (sub.district)       await fillSelect(page, '#sub-district', sub.district);
  if (sub.policeStation)  await fillSelect(page, '#sub-police-station', sub.policeStation);
}

async function fillComplaintDetail(page, cd) {
  console.log('\n📋 Filling: Complaint Detail');
  await clickTab(page, '#tab-complaintDetail');
  await updateOverlay(page, '📋 Filling Complaint Detail...', '#00ffd5');

  if (cd.dateOfComplaint) await fillInput(page, '#cd-date', cd.dateOfComplaint);
  if (cd.description)     await fillTextarea(page, '#cd-description', cd.description);
  if (cd.remarks)         await fillTextarea(page, '#cd-remarks', cd.remarks);
}

// ─── Main ─────────────────────────────────────────────────────────────────────

(async () => {
  const browser = await puppeteer.launch({ headless: false, defaultViewport: null });
  const page    = await browser.newPage();

  await page.goto('http://localhost:3001/', { waitUntil: 'networkidle2' });
  await ensureOverlay(page);

  // ── Step 1: Fill login credentials ──────────────────────────────────────────
  console.log('\n🔐 Filling login credentials...');
  await fillInput(page, '#login-username', data.credentials.username);
  await fillInput(page, '#login-password', data.credentials.password);

  await updateOverlay(page, `🔐 Login Step\n\n👉 Please:\n1. Enter the CAPTCHA shown\n2. Click the Login button\n\n⚠️ Characters are case-sensitive`, '#00ffd5');

  // ── Step 2: Auto-handle OTP ──────────────────────────────────────────────────
  let otpHandled = false;
  const otpWatcher = setInterval(async () => {
    try {
      const otpVisible = await page.evaluate(() =>
        !!document.querySelector('input[type="password"][maxlength="6"]')
      );
      if (otpVisible && !otpHandled) {
        otpHandled = true;
        clearInterval(otpWatcher);

        console.log('📲 OTP modal detected → entering OTP...');
        await updateOverlay(page, '📲 OTP detected!\n\n🤖 Auto-entering OTP...', 'orange');
        await new Promise(r => setTimeout(r, 600));

        const otpInput = await page.$('input[type="password"][maxlength="6"]');
        if (otpInput) {
          await otpInput.click({ clickCount: 3 });
          await otpInput.type('12345');
        }

        // Click Submit button inside OTP modal
        await page.evaluate(() => {
          const btns = Array.from(document.querySelectorAll('button'));
          const submitBtn = btns.find(b => b.innerText.trim() === 'Submit');
          if (submitBtn) submitBtn.click();
        });

        console.log('✅ OTP submitted');
      }
    } catch { /* ignore */ }
  }, 800);

  // ── Step 3: Wait for /home, then navigate to /form ───────────────────────────
  await new Promise((resolve) => {
    page.on('framenavigated', async (frame) => {
      if (frame.url().includes('/home')) {
        clearInterval(otpWatcher);
        console.log('\n🏠 Reached Home page → navigating to form...');
        await updateOverlay(page, '🏠 Login Successful!\n\n🤖 Navigating to complaint form...', 'lightgreen');
        await new Promise(r => setTimeout(r, 1000));
        resolve();
      }
    });
  });

  // Navigate to /form directly
  await page.goto('http://localhost:3001/form', { waitUntil: 'networkidle2' });
  await ensureOverlay(page);
  await updateOverlay(page, '📝 Form loaded!\n\n🤖 Starting to fill form...', '#00ffd5');
  await new Promise(r => setTimeout(r, 800));

  // ── Step 4: Fill all form tabs ───────────────────────────────────────────────

  // ── Tab 1: Complainant Detail ────────────────────────────────────────────────
  console.log('\n🟦 TAB: Complainant Detail');
  await clickTab(page, '#tab-complainantDetail');

  const cd = data.complainantDetail;
  if (cd.personalInformation) await fillPersonalInformation(page, cd.personalInformation);
  if (cd.address)             await fillAddress(page, cd.address);
  if (cd.identification)      await fillIdentification(page, cd.identification);

  // ── Tab 2: Accused Detail ────────────────────────────────────────────────────
  if (data.accusedDetail && data.accusedDetail.length > 0) {
    await fillAccusedDetail(page, data.accusedDetail);
  }

  // ── Tab 3: Incident Detail ───────────────────────────────────────────────────
  if (data.incidentDetail) {
    await fillIncidentDetail(page, data.incidentDetail);
  }

  // ── Tab 4: Complaint Submission Details ──────────────────────────────────────
  if (data.complaintSubmissionDetails) {
    await fillComplaintSubmission(page, data.complaintSubmissionDetails);
  }

  // ── Tab 5: Complaint Detail ──────────────────────────────────────────────────
  if (data.complaintDetail) {
    await fillComplaintDetail(page, data.complaintDetail);
  }

  // ── Done ─────────────────────────────────────────────────────────────────────
  console.log('\n🎉 Form filling complete!');
  await updateOverlay(page, `🎉 All Done!\n\n✅ Form has been filled.\n\n👉 Please review and submit.`, 'lightgreen');

})();
