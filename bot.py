import os, threading, time, subprocess, textwrap
from flask import Flask
import telebot
from edge_tts import Communicate
import asyncio
from PIL import Image, ImageDraw, ImageFont

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "BOT VIVO"

def crear_video(tema, chat_id):
    try:
        bot.send_message(chat_id, "🎬 Creando tu video, dame 30 seg...")
        # 1. Texto simple
        texto = f"No te rindas en el gym. {tema}. Cada dia que vienes, eres mas fuerte que ayer. Sigue, tu puedes!"
        # 2. Voz
        audio = "voz.mp3"
        async def hacer_voz():
            comm = Communicate(texto, "es-MX-DaliaNeural")
            await comm.save(audio)
        asyncio.run(hacer_voz())

        # 3. Imagen de fondo con texto
        img = Image.new('RGB', (720, 1280), color=(15, 15, 30))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
        except:
            font = ImageFont.load_default()
        lineas = textwrap.wrap(tema.upper(), width=18)
        y = 500
        for l in lineas:
            draw.text((60, y), l, fill=(255, 215, 0), font=font)
            y += 70
        draw.text((60, 900), "NO TE RINDAS 💪", fill=(255,255,255), font=font)
        img.save("fondo.jpg")

        # 4. Video con ffmpeg
        subprocess.run(["ffmpeg","-y","-loop","1","-i","fondo.jpg","-i",audio,"-c:v","libx264","-t","15","-pix_fmt","yuv420p","-c:a","aac","-shortest","video.mp4"], check=True)

        with open("video.mp4","rb") as v:
            bot.send_video(chat_id, v, caption=f"🔥 {tema}\n\n#gym #motivacion #shorts #fyp")
        bot.send_message(chat_id, "✅ Listo! Ya puedes subirlo a TikTok.")
    except Exception as e:
        bot.send_message(chat_id, f"❌ Error: {e}\nManda foto de este error")

@bot.message_handler(commands=['start','help'])
def start(m):
    bot.reply_to(m, "🔥 BOT PRO GRATIS LISTO\n\nEscribe:\nShort 15 seg, voz hombre\nTema: no rendirse en el gym\n\nY te hago el video.")

@bot.message_handler(func=lambda m: True)
def todo(m):
    # Corre en hilo aparte para que no se trabe
    tema = m.text.replace("Short","").replace("15 seg","").replace("voz hombre","").replace("Tema:","").strip()
    if not tema:
        tema = m.text
    threading.Thread(target=crear_video, args=(tema, m.chat.id)).start()

def run_bot():
    bot.infinity_polling(timeout=60, long_polling_timeout=60)

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
