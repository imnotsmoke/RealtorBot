# WhatsApp Realtor Qualifier Bot 🏠

Free stack: Meta WhatsApp Cloud API + OpenAI GPT-3.5-turbo + Render.com

---

## STEP 1 — Get your free WhatsApp API access (Meta)

1. Go to https://developers.facebook.com and log in
2. Click **My Apps** → **Create App** → choose **Business**
3. Add the **WhatsApp** product to your app
4. Go to **WhatsApp → API Setup**
5. Copy your:
   - **Phone Number ID** (you'll need this)
   - **Temporary Access Token** (valid 24hrs — get a permanent one later)
6. Under **Webhook**, set:
   - URL: `https://your-render-url.onrender.com/webhook`
   - Verify Token: `realtor_bot_secret`
   - Subscribe to: `messages`

---

## STEP 2 — Deploy to Render.com (free)

1. Push this folder to a GitHub repo
2. Go to https://render.com → New → Web Service
3. Connect your GitHub repo
4. Set these environment variables in Render dashboard:
   - `WHATSAPP_TOKEN` = your Meta access token
   - `OPENAI_API_KEY` = your OpenAI key (sk-...)
   - `VERIFY_TOKEN` = realtor_bot_secret
5. Deploy — Render gives you a free URL like `https://your-app.onrender.com`

---

## STEP 3 — Test it

Send "hi" to your WhatsApp test number and the bot will start the flow.

---

## Add your real listings

Edit the `LISTINGS` dictionary in `bot.py`:

```python
LISTINGS = {
    "home_rent": [
        {"id": "HR1", "name": "Your Property Name", "monthly": 12000, "detail": "3 bed · 2 bath"},
    ],
    ...
}
```

---

## How the 3x rule works

- **Renters**: monthly rent must be ≤ 1/3 of net salary
  - Example: R9,500/mo rent → needs R28,500/mo salary to qualify
- **Buyers**: estimated monthly bond must be ≤ 1/3 of net salary
  - Bond is estimated at 1.05% of purchase price per month (~10.5% over 20 years)
  - Example: R1.65M house → ~R17,325/mo bond → needs R51,975/mo salary

---

## Cost breakdown

| Service         | Cost          |
|-----------------|---------------|
| Meta Cloud API  | FREE (1000 convos/month) |
| Render hosting  | FREE          |
| OpenAI GPT-3.5  | ~$0.002 per conversation |
| **Total**       | **~$0.20 for 100 leads** |

Your $4.40 OpenAI credits = ~2,200 qualifying conversations.

---

## Selling to realtors

Suggested pricing:
- Setup fee: R2,000–R3,500 once-off
- Monthly: R800–R1,500/month
- Add their listings to the bot and hand it over
