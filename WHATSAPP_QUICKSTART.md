# 🚀 Quick Start - WhatsApp Direct Integration

Send WhatsApp messages directly from YOUR phone - no Twilio, no API costs!

## ✅ Prerequisites

1. **Node.js** installed (download from https://nodejs.org/)
2. **Your phone** with WhatsApp installed
3. **Internet connection** on both computer and phone

---

## 📦 Setup (One-time)

### Windows:
```bash
setup-whatsapp.bat
```

### Linux/Mac:
```bash
chmod +x setup-whatsapp.sh start-whatsapp.sh
./setup-whatsapp.sh
```

---

## 🎯 Usage

### Step 1: Start DressGuard Backend

The WhatsApp service **automatically starts** with the backend!

**Windows:**
```bash
start-all.bat
```

**OR manually:**
```bash
uvicorn main:app --reload
```

**Linux/Mac:**
```bash
./start-all.sh
```

### Step 2: Scan QR Code

A **separate console window** will appear with the QR code.

1. Open **WhatsApp** on your phone
2. Go to **Settings** > **Linked Devices**
3. Tap **"Link a Device"**
4. Scan the QR code shown in the WhatsApp service window

✅ Once connected, you'll see: **"WhatsApp Client is READY!"**

### Step 3: Start Frontend

In a **new terminal**:

```bash
cd frontend
npm run dev
```

### Step 4: Send Alerts!

Click the **"Send Alerts"** button in DressGuard UI - messages will be sent from YOUR WhatsApp! 📱

---

## 🔧 Configuration

Edit `config.py`:

```python
# Your recipients (phone numbers with country code, no +)
WHATSAPP_RECIPIENTS = [
    "919108816244",  # India: 91 + 9108816244
    "15551234567",   # US: 1 + 5551234567
]
```

---

## 💡 How It Works

1. **Backend automatically starts** the Node.js WhatsApp service on startup
2. **Node.js service** connects to WhatsApp Web (like desktop app)
3. **Your phone** must have internet and WhatsApp active
4. **Session persists** - no need to scan QR again (unless logged out)
5. **Messages sent from your phone** - shows as "You" in WhatsApp
6. **Service stops** automatically when backend shuts down

---

## ⚠️ Important Notes

- ✅ **FREE** - No API costs!
- ✅ **Your number** - Messages sent from your WhatsApp
- ✅ **Reliable** - Uses official WhatsApp Web protocol
- ⚠️ **Computer must be running** - Service must be active
- ⚠️ **Phone must have internet** - WhatsApp must be online
- ⚠️ **Rate limits** - Don't spam (WhatsApp may ban)

---

## 🐛 Troubleshooting

### "Service not available"
- Make sure Node.js service is running: `start-whatsapp.bat`
- Check terminal for errors

### "WhatsApp client not ready"
- Scan QR code with your phone
- Wait until you see "✅ WhatsApp Client is READY!"

### "Error sending message"
- Check phone number format (no + sign, include country code)
- Verify recipient has WhatsApp
- Make sure your phone has internet

### QR Code not showing
- Install dependencies: `cd whatsapp-service && npm install`
- Check Node.js is installed: `node --version`

---

## 📊 Test It

Send a test message:

```bash
curl -X POST http://localhost:3001/send-message \
  -H "Content-Type: application/json" \
  -d '{"to": "919108816244", "message": "Test from DressGuard!"}'
```

---

## 🔄 Restart/Reconnect

If WhatsApp disconnects:

1. Stop service (Ctrl+C)
2. Start again: `start-whatsapp.bat`
3. Session should auto-reconnect (no QR needed)

To force new QR (if issues):
```bash
cd whatsapp-service
rm -rf .wwebjs_auth/
node server.js
```

---

## ✨ Advantages over Twilio

| Feature | Direct WhatsApp | Twilio |
|---------|----------------|--------|
| **Cost** | FREE ✅ | $0.005-0.02 per message |
| **Setup Time** | 2 minutes | 30+ minutes |
| **Phone Number** | Your personal number | Twilio sandbox/verified |
| **Verification** | None needed | Business verification required |
| **Message Source** | From YOU | From Twilio number |
| **Reliability** | Very high | Very high |

---

**Need help?** Check logs in the WhatsApp service terminal for detailed error messages.
