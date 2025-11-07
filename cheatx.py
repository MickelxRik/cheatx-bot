from telethon import TelegramClient, events
import os, requests, json, urllib3, getpass, subprocess, random, asyncio, re

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ================= AI CONFIG =================
AI_URL = "https://openrouter.ai/api/v1/chat/completions"
TIMEOUT = 20
MEMORY_FILE = "cheatx_memory.json"  # Persistent chat memory file
# =============================================

def load_api_key_encrypted(enc_path="key.enc"):
    """Decrypt encrypted API key (or use env variable)."""
    env_key = os.environ.get("CHEATX_API_KEY")
    if env_key:
        return env_key.strip()
    if not os.path.exists(enc_path):
        return None
    passphrase = getpass.getpass("Enter passphrase to decrypt key.enc: ")
    try:
        p = subprocess.run(
            ["openssl", "enc", "-d", "-aes-256-cbc", "-salt",
             "-pbkdf2", "-iter", "100000", "-in", enc_path, "-pass", "stdin"],
            input=(passphrase + "\n").encode(),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20
        )
        if p.returncode != 0:
            return None
        return p.stdout.decode().strip()
    except Exception:
        return None


API_KEY = load_api_key_encrypted("key.enc")
if not API_KEY:
    API_KEY = input("Enter OpenRouter API key: ").strip()

# Telegram credentials
if os.path.exists("auth_cheatx.txt"):
    with open("auth_cheatx.txt", "r") as f:
        api_id = int(f.readline().strip())
        api_hash = f.readline().strip()
else:
    print("Enter your Telegram API details (https://my.telegram.org)")
    api_id = int(input("API ID: "))
    api_hash = input("API Hash: ")
    with open("auth_cheatx.txt", "w") as f:
        f.write(f"{api_id}\n{api_hash}\n")

client = TelegramClient("CheatX", api_id, api_hash)

# ================= Memory Management =================
def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_memory(memory):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory[-200:], f, ensure_ascii=False, indent=2)

conversation_history = load_memory()

def extract_emojis(text):
    emoji_pattern = re.compile(
        "["u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF"
        u"\u2600-\u26FF\u2700-\u27BF]+",
        flags=re.UNICODE)
    return emoji_pattern.findall(text)

# ================= AI Reply Generator =================
def get_ai_reply(user_msg, mirrored_emojis=None):
    global conversation_history
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    base_prompt = (
        "You are CheatX 🤖 — a chill, natural, and smart human-like friend. "
        "Reply quickly and casually, like a real person texting."
    )
    if mirrored_emojis:
        base_prompt += f" Feel free to use these emojis naturally: {' '.join(mirrored_emojis)}"

    messages = [{"role": "system", "content": base_prompt}] + conversation_history + [
        {"role": "user", "content": user_msg}
    ]

    try:
        res = requests.post(AI_URL, headers=headers, json={"model": "gpt-3.5-turbo", "messages": messages},
                            timeout=TIMEOUT, verify=False)
        if res.status_code == 200:
            reply = res.json()["choices"][0]["message"]["content"].strip()
            conversation_history.append({"role": "user", "content": user_msg})
            conversation_history.append({"role": "assistant", "content": reply})
            save_memory(conversation_history)
            return reply
        else:
            return ""
    except Exception:
        return ""

# ================= Telegram Event =================
@client.on(events.NewMessage)
async def reply_handler(event):
    if event.is_private and not event.out:
        msg = event.raw_text.strip() if event.raw_text else ""
        lower_msg = msg.lower()
        user_emojis = extract_emojis(msg)

        # ✅ Detect if message is a sticker
        if event.message and event.message.media and event.message.media.document:
            await asyncio.sleep(random.uniform(0.2, 0.6))
            sticker_replies = [
                "Haha nice sticker 😄",
                "Ye sticker to OP lag raha 😂🔥",
                "Aree ye sticker kaha se mila 😅",
                "Cool sticker bro 😎",
                "Nice one 😁👍"
            ]
            await event.reply(random.choice(sticker_replies))
            return

        # ✅ Custom rule: if user asks about owner/developer
        owner_keywords = ["owner", "creator", "developer", "made you", "banane wale", "who created", "creator of"]
        if any(k in lower_msg for k in owner_keywords):
            await asyncio.sleep(random.uniform(0.3, 0.7))
            owner_replies = [
                "Mera owner abhi offline hai 😅, aap mujhse pooch lo kya baat karni thi?",
                "Owner @Mickelxrik abhi busy hai 😎, par main help kar sakta hoon — bolo kya kaam hai?",
                "Mickelxrik bhai abhi offline hain 💫, par main yahan hoon 😄 kya poochhna tha?",
                "Aapka message main owner @Mickelxrik tak pahucha dunga 😇, tab tak mujhe batao kya baat karni thi?",
                "Owner abhi thoda busy hain 😉, mujhe batao kya poochhna hai, main help kar dunga."
            ]
            await event.reply(random.choice(owner_replies))
            return

        # 😔 Detect sad/emotional emojis
        sad_emojis = ["😔", "😢", "😭", "😞", "💔", "🥺", "😩", "😥"]
        if any(e in msg for e in sad_emojis):
            await asyncio.sleep(random.uniform(0.3, 0.7))
            comfort_lines = [
                "Kya hua bro 😔 sab thik hai na?",
                "Hey, chill kar ❤️ sab thik ho jayega!",
                "Aree mood off lag raha 😢, baat kar mere se 💬",
                "Don’t worry bhai, main yahin hoon tere sath 💪",
                "Tension mat le ❤️ everything will be okay!"
            ]
            await event.reply(random.choice(comfort_lines))
            return

        # 😄 Handle pure emoji messages (no text)
        if len(msg) <= len("".join(user_emojis)) and user_emojis:
            await asyncio.sleep(random.uniform(0.3, 0.6))
            bot_emojis = ["😎", "😄", "🔥", "😉", "😁", "❤️", "🤖", "😅", "✨"]
            emoji_reply = random.choice([
                f"{random.choice(bot_emojis)} haha nice one!",
                f"{random.choice(bot_emojis)} cool!",
                f"{random.choice(bot_emojis)} love that energy!",
                f"That’s a good one {random.choice(bot_emojis)}",
                f"😂 lol!"
            ])
            await event.reply(emoji_reply)
            return

        # ⚡ Fast & smooth delay (0.2–0.7 sec)
        await asyncio.sleep(random.uniform(0.2, 0.7))

        # 💬 Normal AI reply for text messages
        if msg:
            ai_reply = get_ai_reply(msg)
            if ai_reply:
                await event.reply(ai_reply)

# ================= Startup Message =================
print("\n🚀 CheatX AI Auto-Reply is now ACTIVE!")
print("🤖 Running with Persistent Memory + Smart Chat Mode ⚡")
print("💬 You can close Termux safely — bot will keep replying silently.\n")

client.start()
client.run_until_disconnected()