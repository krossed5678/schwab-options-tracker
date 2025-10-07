# 🤖 How to Add OptiFlow Bot to Your Discord Server

## 🔗 **Generate Bot Invite Link with Administrator Permissions**

### **Method 1: Using Discord Developer Portal (Recommended)**

1. **Go to Discord Developer Portal**
   - Visit: https://discord.com/developers/applications/
   - Select your OptiFlow bot application

2. **Navigate to OAuth2**
   - Click **"OAuth2"** in the left sidebar
   - Click **"URL Generator"**

3. **Select Scopes**
   - Check ✅ **"bot"**
   - Check ✅ **"applications.commands"** (for slash commands support)

4. **Select Bot Permissions**
   - Check ✅ **"Administrator"** (This gives permission level 8)
   
   **OR if you prefer specific permissions:**
   - ✅ Send Messages
   - ✅ Send Messages in Threads  
   - ✅ Embed Links
   - ✅ Attach Files
   - ✅ Read Message History
   - ✅ Use External Emojis
   - ✅ Add Reactions
   - ✅ Manage Messages (for command deletion)
   - ✅ Use Slash Commands

5. **Copy the Generated URL**
   - The URL will look like: `https://discord.com/api/oauth2/authorize?client_id=YOUR_BOT_ID&permissions=8&scope=bot%20applications.commands`
   - Copy this URL

6. **Add Bot to Server**
   - Paste the URL in your browser
   - Select your Discord server from the dropdown
   - Click **"Authorize"**
   - Complete any captcha if prompted

### **Method 2: Manual URL Construction**

If you know your bot's Client ID, you can construct the URL manually:

```
https://discord.com/api/oauth2/authorize?client_id=YOUR_BOT_CLIENT_ID&permissions=8&scope=bot%20applications.commands
```

**Replace `YOUR_BOT_CLIENT_ID`** with your actual bot's Client ID (found in General Information tab).

## 🔢 **Permission Values Explained**

- **Permission Level 8** = Administrator (Full access)
- **Permission Level 0** = No special permissions  
- **Custom Permissions** = Calculated based on specific permissions selected

## ✅ **Verification Steps**

After adding the bot:

1. **Check Bot Status**
   - Bot should appear in your server's member list
   - Status should show as "Offline" initially (until you start it)

2. **Verify Permissions**
   - Right-click the bot in member list
   - Check "Roles" - should show appropriate permissions

3. **Test Bot Connection**
   ```bash
   # Enable Message Content Intent first (as discussed earlier)
   # Then start the bot:
   python discord_bot.py
   ```

4. **Test Commands**
   - Bot should show as "Online"
   - Try: `!opti help`
   - Should get ephemeral (private) response

## 🚨 **Important Notes**

### **Administrator vs Custom Permissions**
- **Administrator (Level 8)**: Easiest setup, bot can do everything
- **Custom Permissions**: More secure, only specific permissions granted

### **Required for OptiFlow Bot:**
At minimum, your bot needs:
- ✅ **Send Messages** - To respond to commands
- ✅ **Embed Links** - For rich formatted responses  
- ✅ **Manage Messages** - For command deletion feature
- ✅ **Use External Emojis** - For enhanced UI elements

### **Security Consideration**
Administrator permission is powerful - consider using custom permissions if you're security-conscious.

## 🔧 **If Bot Still Won't Respond**

Even after adding with correct permissions:

1. **Enable Message Content Intent** (as covered in previous guide)
2. **Check bot is in the right channel** (where you're typing commands)
3. **Verify command format**: `!opti help` (space after opti)
4. **Check bot status** in server - should be "Online"

## 📱 **Mobile Discord Setup**

The OAuth2 URL works the same on mobile:
1. Paste the invite URL in mobile browser
2. It will open Discord app
3. Select server and authorize
4. Bot will be added with chosen permissions

Once your bot is added with Administrator permissions and you've enabled Message Content Intent, your OptiFlow bot will have full functionality! 🚀