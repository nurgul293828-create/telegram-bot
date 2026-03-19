from flask import Flask
import threading
import telebot
import json
import os
import requests
from telebot.types import ChatJoinRequest, InlineKeyboardMarkup, InlineKeyboardButton

# Flask web server
app = Flask('')

@app.route('/')
def home():
    return "Bot çalışıyor... 🤖"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = threading.Thread(target=run)
    t.start()

# Telegram bot
TOKEN = "8675623246:AAG17fieaauWE469eMDKh1VSUtkHC95tfqY"
API_URL = "http://fi8.bot-hosting.net:20163/elos-gemina"

VERI_DOSYASI = "aktif_kanallar.json"
SORUMLU_DOSYASI = "kanal_sorumluları.json"
LOG_DOSYASI = "log_kanallari.json"

bot = telebot.TeleBot(TOKEN)

def isim_kontrol(isim):
    if not isim or len(isim) < 2:
        return False, "geçersiz isim"
    try:
        response = requests.get(API_URL, params={"text": f"Bu isim Türkiye'de kız ismi mi? Sadece EVET veya HAYIR yaz: {isim}"}, timeout=10)
        if response.status_code == 200:
            cevap = response.json().get("response", "").strip().upper()
            if "EVET" in cevap:
                return True, cevap
            elif "HAYIR" in cevap:
                return False, cevap
        return None, f"hata {response.status_code}"
    except Exception as e:
        return None, f"bağlantı hatası: {str(e)}"

def butonlu_gonder(chat_id, text, **kwargs):
    klavye = InlineKeyboardMarkup()
    klavye.add(InlineKeyboardButton(text="👨‍💻 @TekParca", url="https://t.me/TekParca"))
    kwargs["reply_markup"] = klavye
    bot.send_message(chat_id, text, **kwargs)

def butonlu_cevapla(message, text, **kwargs):
    klavye = InlineKeyboardMarkup()
    klavye.add(InlineKeyboardButton(text="👨‍💻 @TekParca", url="https://t.me/TekParca"))
    kwargs["reply_markup"] = klavye
    bot.reply_to(message, text, **kwargs)

def yukle_json(dosya):
    if os.path.exists(dosya):
        with open(dosya, "r") as f:
            return json.load(f)
    return {} if dosya in [SORUMLU_DOSYASI, LOG_DOSYASI] else set()

def kaydet_json(dosya, veri):
    with open(dosya, "w") as f:
        if dosya == VERI_DOSYASI:
            json.dump(list(veri), f)
        else:
            json.dump(veri, f)

def log_gonder(kanal_id, mesaj):
    log_kanallari = yukle_json(LOG_DOSYASI)
    log_id = log_kanallari.get(str(kanal_id))
    if log_id:
        try:
            butonlu_gonder(log_id, mesaj)
        except:
            pass

def admin_mi(message, kanal_id):
    try:
        chat_member = bot.get_chat_member(kanal_id, message.from_user.id)
        return chat_member.status in ['administrator', 'creator']
    except:
        return False

aktif_kanallar = set(yukle_json(VERI_DOSYASI)) if os.path.exists(VERI_DOSYASI) else set()
sorumlular = yukle_json(SORUMLU_DOSYASI) if os.path.exists(SORUMLU_DOSYASI) else {}
log_kanallari = yukle_json(LOG_DOSYASI) if os.path.exists(LOG_DOSYASI) else {}

@bot.message_handler(commands=['help'])
def help_komut(message):
    butonlu_cevapla(message, 
        "🤖 İSTEK ONAY BOT\n\n"
        "📌 **KOMUTLAR:**\n"
        "/onay <kanal_id> - aktifleştir\n"
        "/kapat <kanal_id> - devre dışı\n"
        "/logayarla <kanal_id> - log kanalını ayarla\n"
        "/test <isim> - isim test et\n"
        "/api - api durumu\n\n"
        "⚠️ Sadece kanal adminleri kendi kanalları için komut kullanabilir!")

@bot.message_handler(commands=['test'])
def test_komut(message):
    try:
        isim = message.text.split()[1]
        butonlu_cevapla(message, f"🔍 {isim} analiz ediliyor...")
        sonuc, detay = isim_kontrol(isim)
        if sonuc is True:
            butonlu_cevapla(message, f"❌ {isim} → KIZ İSMİ (onaylanmaz)")
        elif sonuc is False:
            butonlu_cevapla(message, f"✅ {isim} → KIZ İSMİ DEĞİL (onaylanır)")
        else:
            butonlu_cevapla(message, f"⚠️ {isim} → {detay}")
    except:
        butonlu_cevapla(message, "❗ /test <isim>")

@bot.message_handler(commands=['api'])
def api_komut(message):
    butonlu_cevapla(message, "🔄 kontrol ediliyor...")
    sonuc, detay = isim_kontrol("test")
    if sonuc is not None:
        butonlu_cevapla(message, f"✅ API çalışıyor")
    else:
        butonlu_cevapla(message, f"❌ API hatası: {detay}")

@bot.message_handler(commands=['logayarla'])
def log_ayarla(message):
    try:
        kanal_id = int(message.text.split()[1])
        
        if not admin_mi(message, kanal_id):
            butonlu_cevapla(message, "⛔ Bu kanalda admin değilsin!")
            return
        
        log_kanallari[str(kanal_id)] = message.chat.id
        kaydet_json(LOG_DOSYASI, log_kanallari)
        
        butonlu_cevapla(message, f"✅ Bu sohbet **{kanal_id}** için log kanalı olarak ayarlandı")
        log_gonder(kanal_id, f"📥 Log kanalı başarıyla ayarlandı")
        
    except:
        butonlu_cevapla(message, "❗ /logayarla <kanal_id>")

@bot.message_handler(commands=['onay'])
def onay_komut(message):
    try:
        kanal_id = int(message.text.split()[1])
        
        if not admin_mi(message, kanal_id):
            butonlu_cevapla(message, "⛔ Bu kanalda admin değilsin!")
            return
        
        aktif_kanallar.add(kanal_id)
        kaydet_json(VERI_DOSYASI, aktif_kanallar)
        
        sorumlular[str(kanal_id)] = message.from_user.id
        kaydet_json(SORUMLU_DOSYASI, sorumlular)
        
        butonlu_cevapla(message, f"✅ **{kanal_id}** aktif edildi\n🧠 Yapay zeka filtresi açık")
        log_gonder(kanal_id, f"✅ {message.from_user.first_name} kanalı aktif etti")
        
    except:
        butonlu_cevapla(message, "❗ /onay <kanal_id>")

@bot.message_handler(commands=['kapat'])
def kapat_komut(message):
    try:
        kanal_id = int(message.text.split()[1])
        
        if not admin_mi(message, kanal_id):
            butonlu_cevapla(message, "⛔ Bu kanalda admin değilsin!")
            return
        
        if kanal_id in aktif_kanallar:
            aktif_kanallar.remove(kanal_id)
            kaydet_json(VERI_DOSYASI, aktif_kanallar)
            
            sorumlular.pop(str(kanal_id), None)
            kaydet_json(SORUMLU_DOSYASI, sorumlular)
            
            butonlu_cevapla(message, f"⛔ **{kanal_id}** devre dışı")
            log_gonder(kanal_id, f"⛔ {message.from_user.first_name} kanalı kapattı")
        else:
            butonlu_cevapla(message, "ℹ️ Bu kanal zaten aktif değil")
            
    except:
        butonlu_cevapla(message, "❗ /kapat <kanal_id>")

@bot.chat_join_request_handler()
def istek_onayla(request):
    if request.chat.id not in aktif_kanallar:
        return
    
    tam_adi = f"{request.from_user.first_name or ''} {request.from_user.last_name or ''}".strip()
    kullanici_adi = request.from_user.username or "yok"
    
    kullanici = f"👤 **{tam_adi}**\n🆔 @{kullanici_adi}\n🔢 `{request.from_user.id}`"
    
    sonuc, detay = isim_kontrol(tam_adi)
    
    if sonuc is True:
        log_gonder(request.chat.id, f"🚫 **ONAYLANMADI**\n\n{kullanici}\n📢 {request.chat.title}\n🤖 {detay}")
        
        if str(request.chat.id) in sorumlular:
            butonlu_gonder(sorumlular[str(request.chat.id)], 
                f"🚫 **ONAYLANMADI**\n\n{kullanici}\n📢 {request.chat.title}")
                
    elif sonuc is False:
        try:
            bot.approve_chat_join_request(request.chat.id, request.from_user.id)
            log_gonder(request.chat.id, f"✅ **ONAYLANDI**\n\n{kullanici}\n📢 {request.chat.title}")
            
            if str(request.chat.id) in sorumlular:
                butonlu_gonder(sorumlular[str(request.chat.id)], 
                    f"✅ **ONAYLANDI**\n\n{kullanici}\n📢 {request.chat.title}")
        except Exception as e:
            log_gonder(request.chat.id, f"❌ HATA: {str(e)}")
            
    else:
        log_gonder(request.chat.id, f"⚠️ **API HATASI**\n\n{kullanici}\n📢 {request.chat.title}\n❌ {detay}")
        
        if str(request.chat.id) in sorumlular:
            butonlu_gonder(sorumlular[str(request.chat.id)], 
                f"⚠️ **API HATASI**\n\n{kullanici}\n📢 {request.chat.title}\n❌ {detay}")

# Web server'ı başlat
keep_alive()

print("🚀 bot çalışıyor...")
print("📌 Webview: https://telegram-bot.devintell44.repl.co")
bot.infinity_polling()
