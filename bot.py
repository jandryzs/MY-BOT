import os, re, textwrap, subprocess, threading
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import edge_tts
from PIL import Image, ImageDraw, ImageFont
from flask import Flask

# Mini servidor gratis para Render
app_web = Flask(__name__)
@app_web.route('/')
def home():
    return "Bot prendido ✅"

def correr_web():
    port = int(os.environ.get("PORT", 10000))
    app_web.run(host="0.0.0.0", port=port)

BOT_TOKEN = os.getenv("BOT_TOKEN")

VOCES = {
    "hombre": "es-MX-JorgeNeural",
    "mujer": "es-MX-DaliaNeural",
}

def parsear_mensaje(texto):
    texto_low = texto.lower()
    dur = 30
    m = re.search(r'(\d+)\s*seg', texto_low)
    if m: dur = int(m.group(1))
    voz = "mujer" if "mujer" in texto_low else "hombre"
    estilo = "motivacional"
    for e in ["chistoso","gracioso","terror","miedo","informativo","motivacional"]:
        if e in texto_low:
            estilo = e
            break
    tema = texto.split("tema:",1)[1].strip() if "tema:" in texto_low else texto
    return dur, voz, estilo, tema

def crear_guion(tema, estilo, dur):
    if estilo in ["chistoso","gracioso"]:
        return f"Oye, escucha esto porque está brutal. {tema}. Y lo peor es que es verdad. Si te reíste, sígueme."
    if estilo in ["terror","miedo"]:
        return f"No veas esto de noche. {tema}. Dicen que quien lo escucha, no duerme tranquilo."
    if estilo == "informativo":
        return f"¿Sabías que {tema}? Esto casi nadie lo sabe. Guarda este video. Sígueme para más."
    return f"Escucha bien. {tema}. No importa cuántas veces caigas, lo que importa es que te levantes una vez más."

def crear_srt(guion):
    palabras = guion.split()
    bloques = [" ".join(palabras[i:i+4]) for i in range(0, len(palabras), 4)]
    with open("subs.srt","w",encoding="utf-8") as f:
        for i,b in enumerate(bloques):
            inicio=i*1.2; fin=inicio+1.2
            def fmt(t): return f"{int(t//3600):02}:{int((t%3600)//60):02}:{int(t%60):02},{int((t%1)*1000):03}"
            f.write(f"{i+1}\n{fmt(inicio)} --> {fmt(fin)}\n{b}\n\n")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 BOT PRO GRATIS LISTO\n\nEscríbeme:\nShort 30 seg, estilo chistoso, voz mujer\nTema: no rendirse en el gym")

async def crear_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text
    dur, voz_tipo, estilo, tema = parsear_mensaje(texto)
    guion = crear_guion(tema, estilo, dur)
    await update.message.reply_text(f"🎬 Creando... {tema} | {estilo} | {dur}s | voz {voz_tipo}")
    comm = edge_tts.Communicate(guion, VOCES.get(voz_tipo, VOCES["hombre"]))
    await comm.save("voz.mp3")
    img = Image.new('RGB', (1080,1920), color=(20,20,40))
    d = ImageDraw.Draw(img)
    try: font = ImageFont.truetype("arial.ttf", 80)
    except: font = ImageFont.load_default()
    d.multiline_text((80,750), textwrap.fill(tema.upper(), width=18), fill=(255,255,255), font=font, spacing=20)
    img.save("fondo.jpg")
    crear_srt(guion)
    style = "Fontsize=52,PrimaryColour=&H00FFFF&,OutlineColour=&H000000&,BorderStyle=1,Outline=3,Shadow=0,Bold=1,Alignment=2,MarginV=350"
    subprocess.run(["ffmpeg","-y","-loop","1","-i","fondo.jpg","-i","voz.mp3","-vf",f"scale=1080:1920,subtitles=subs.srt:force_style='{style}'","-shortest","-c:v","libx264","-c:a","aac","video.mp4"])
    await update.message.reply_video(video=open("video.mp4","rb"), caption=f"Listo 🔥 {tema}")

if __name__ == "__main__":
    threading.Thread(target=correr_web, daemon=True).start()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, crear_video))
    app.run_polling()
