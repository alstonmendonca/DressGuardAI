const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const express = require('express');

const app = express();
app.use(express.json());

console.log('🚀 Starting WhatsApp Web Client...\n');

const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: {
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    }
});

let isReady = false;

client.on('qr', (qr) => {
    console.log('\n╔══════════════════════════════════════════════════════════╗');
    console.log('║  🔵 SCAN THIS QR CODE WITH YOUR PHONE                   ║');
    console.log('╚══════════════════════════════════════════════════════════╝\n');
    qrcode.generate(qr, { small: true });
    console.log('\n📱 Open WhatsApp on your phone');
    console.log('👆 Go to Settings > Linked Devices > Link a Device');
    console.log('📷 Scan the QR code above\n');
});

client.on('authenticated', () => {
    console.log('✅ Authenticated successfully!');
});

client.on('ready', () => {
    isReady = true;
    console.log('\n╔══════════════════════════════════════════════════════════╗');
    console.log('║  ✅ WhatsApp Client is READY!                           ║');
    console.log('║  📱 Messages will be sent from your phone                ║');
    console.log('╚══════════════════════════════════════════════════════════╝\n');
    console.log(`📞 Your WhatsApp: ${client.info.wid.user}`);
    console.log(`👤 Name: ${client.info.pushname}\n`);
});

client.on('disconnected', (reason) => {
    console.log('❌ Client was disconnected:', reason);
    isReady = false;
});

client.initialize();

// API endpoint to send message
app.post('/send-message', async (req, res) => {
    try {
        if (!isReady) {
            return res.status(503).json({ 
                success: false, 
                error: 'WhatsApp client not ready. Please scan QR code.' 
            });
        }

        const { to, message } = req.body;
        
        if (!to || !message) {
            return res.status(400).json({ 
                success: false,
                error: 'Missing "to" or "message" in request body' 
            });
        }
        
        // Format phone number (remove + and spaces, add @c.us)
        const phoneNumber = to.replace(/[^0-9]/g, '');
        const chatId = phoneNumber + '@c.us';
        
        console.log(`📤 Sending message to ${to}...`);
        
        await client.sendMessage(chatId, message);
        
        console.log(`✅ Message sent successfully to ${to}`);
        
        res.json({ 
            success: true, 
            to: to,
            chatId: chatId,
            message: 'Message sent successfully'
        });
        
    } catch (error) {
        console.error('❌ Error sending message:', error);
        res.status(500).json({ 
            success: false, 
            error: error.message 
        });
    }
});

// API endpoint to send document with caption
app.post('/send-document', async (req, res) => {
    try {
        if (!isReady) {
            return res.status(503).json({ 
                success: false, 
                error: 'WhatsApp client not ready. Please scan QR code.' 
            });
        }

        const { to, caption, filename, filedata } = req.body;
        
        if (!to || !filedata || !filename) {
            return res.status(400).json({ 
                success: false,
                error: 'Missing required fields: to, filename, filedata' 
            });
        }
        
        // Format phone number
        const phoneNumber = to.replace(/[^0-9]/g, '');
        const chatId = phoneNumber + '@c.us';
        
        console.log(`📎 Sending document "${filename}" to ${to}...`);
        
        // Decode base64 file data
        const buffer = Buffer.from(filedata, 'base64');
        
        // Create MessageMedia object
        const { MessageMedia } = require('whatsapp-web.js');
        const media = new MessageMedia('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 
                                      filedata, 
                                      filename);
        
        // Send document with caption
        await client.sendMessage(chatId, media, { caption: caption || '' });
        
        console.log(`✅ Document sent successfully to ${to}`);
        
        res.json({ 
            success: true, 
            to: to,
            chatId: chatId,
            filename: filename,
            message: 'Document sent successfully'
        });
        
    } catch (error) {
        console.error('❌ Error sending document:', error);
        res.status(500).json({ 
            success: false, 
            error: error.message 
        });
    }
});

// Status endpoint
app.get('/status', (req, res) => {
    res.json({ 
        status: isReady ? 'ready' : 'not_ready',
        connected: isReady,
        info: isReady ? {
            phone: client.info.wid.user,
            name: client.info.pushname
        } : null
    });
});

// Health check
app.get('/health', (req, res) => {
    res.json({ status: 'ok', service: 'whatsapp-web' });
});

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
    console.log(`\n🌐 WhatsApp service running on http://localhost:${PORT}`);
    console.log(`📍 Endpoints:`);
    console.log(`   POST http://localhost:${PORT}/send-message`);
    console.log(`   GET  http://localhost:${PORT}/status`);
    console.log(`\n⏳ Waiting for WhatsApp connection...\n`);
});
