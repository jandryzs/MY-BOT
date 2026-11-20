import os, re, textwrap, subprocess, asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import edge_tts
from PIL import Image, ImageDraw, ImageFont

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Voces gratis
VOCES = {
    "hombre": "es-MX-JorgeNeural",
    "mujer": "es-MX-DaliaNeural",
    "hombre_espana": "es-ES-AlvaroNeural",
    "mujer_espana": "es-ES-ElviraNeural",
}

def parsear_mensaje(texto):
    texto_low = texto.lower()
    # Duración
    dur = 30
    m = re.search(r'(\d+)\s*seg', texto_low)
    if m: dur = int(m.group(1))
    # Voz
    voz = "hombre"
    if "mujer" in texto_low or "femenina" in texto_low or "chica" in texto_low:
        voz = "mujer"
    # Estilo
    estilo = "motivacional"
    for e in ["chistoso", "gracioso", "terror", "miedo", "informativo", "motivacional", "triste", "amor"]:
        if e in texto_low:
            estilo = e
            break
    # Tema = todo después de "tema:" o si no, todo el mensaje
    tema = texto
    if "tema:" in texto_low:
        tema = texto.split("tema:",1)[1].strip()
    elif "sobre:" in texto_low:
        tema = texto.split("sobre:",1)[1].strip()
    return dur, voz, estilo, tema

def crear_guion(tema, estilo, dur):
    if estilo in ["chistoso","gracioso"]:
        return f"Oye, escucha esto porque está brutal. {tema}. Y lo peor es que es verdad. Si te reíste, sígueme que mañana te cuento algo peor."
    if estilo in ["terror","miedo"]:
        return f"No veas esto de noche. {tema}. Dicen que quien lo escucha, no duerme tranquilo. ¿Te atreves a compartirlo?"
    if estilo == "informativo":
        return f"¿Sabías que {tema}? Esto casi nadie lo sabe. Guarda este video porque te va a servir. Sígueme para aprender algo nuevo cada día."
    # motivacional por defecto
    return f"Escucha bien. {tema}. No importa cuántas veces caigas, lo que importa es que te levantes una vez más. Si este video te motivó, compártelo con alguien que lo necesite."

def crear_srt(guion, archivo="subs.srt"):
    palabras = guion.split()
    # Agrupar de 4 en 4 palabras para subtítulos estilo TikTok
    bloques = [" ".join(palabras[i:i+4]) for i in range(0, len(palabras), 4)]
    with open(archivo, "w", encoding="utf-8") as f:
        for i, b in enumerate(bloques):
            inicio = i * 1.2
            fin = inicio + 1.2
            def fmt(t):
                h=int(t//3600); m=int((t%3600)//60); s=int(t%60); ms=int((t%1)*1000)
                return f"{h:02}:{m:02}:{s:02},{ms:03}"
            f.write(f"{i+1}\n{fmt(inicio)} --> {fmt(fin)}\n{b}\n\n")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 BOT PRO LISTO\n\nEscríbeme así:\n\n`Short 30 seg, estilo chistoso, voz mujer\nTema: no rendirse en el gym`\n\nOpciones:\nDuración: 15, 30, 45, 60 seg\nEstilo: motivacional, chistoso, terror, informativo\nVoz: hombre, mujer"
    )

async def crear_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text
    dur, voz_tipo, estilo, tema = parsear_mensaje(texto)
    guion = crear_guion(tema, estilo, dur)
    
    await update.message.reply_text(f"🎬 Creando...\n📌 Tema: {tema}\n⏱️ {dur} seg | 🎭 {estilo} | 🎤 Voz {voz_tipo}\nDame 40 seg...")

    # 1. Voz
    voz_elegida = VOCES.get(voz_tipo, VOCES["hombre"])
    comm = edge_tts.Communicate(guion, voz_elegida)
    await comm.save("voz.mp3")

    # 2. Fondo 1080x1920 con colores según estilo
    colores = {
        "motivacional": (20, 20, 40),
        "chistoso": (120, 20, 120),
        "terror": (5, 5, 5),
        "informativo": (0, 80, 120),
    }
    color = colores.get(estilo, (20,20,40))
    img = Image.new('RGB', (1080, 1920), color=color)
    d = ImageDraw.Draw(img)
    try: font = ImageFont.truetype("arial.ttf", 80)
    except: font = ImageFont.load_default()
    d.multiline_text((80, 750), textwrap.fill(tema.upper(), width=18), fill=(255,255,255), font=font, spacing=20)
    img.save("fondo.jpg")

    # 3. Subtítulos
    crear_srt(guion)

    # 4. Video con subtítulos amarillos grandes
    # Estilo TikTok: amarillo, borde negro grueso, centrado abajo
    style = "Fontsize=52,PrimaryColour=&H00FFFF&,OutlineColour=&H000000&,BorderStyle=1,Outline=3,Shadow=0,Bold=1,Alignment=2,MarginV=350"
    cmd = ["ffmpeg","-y","-loop","1","-i","fondo.jpg","-i","voz.mp3",
           "-vf", f"scale=1080:1920,subtitles=subs.srt:force_style='{style}'",
           "-shortest","-c:v","libx264","-c:a","aac","video.mp4"]
    subprocess.run(cmd)

    # 5. Si tienes música, la mezcla (opcional)
    # Sube un archivo musica.mp3 a tu GitHub y descomenta esto:
    # subprocess.run(["ffmpeg","-y","-i","video.mp4","-i","musica.mp3","-filter_complex","[1:a]volume=0.15[a1];[0:a][a1]amix=inputs=2:duration=first","-c:v","copy","video_final.mp4"])
    # await update.message.reply_video(video=open("video_final.mp4","rb"), caption=f"Listo 🔥 {tema} | {estilo} | {dur}s")

    await update.message.reply_video(video=open("video.mp4","rb"), caption=f"Listo 🔥 {tema} | {estilo} | {dur}s | voz {voz_tipo}")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, crear_video))
app.run_polling()
