import glob
import re
import subprocess
import webbrowser

import unicodedata
import yt_dlp
import os
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time


# ffmpeg path
def get_ffmpeg_path():
    # Proje dizinini al
    project_dir = os.path.dirname(os.path.abspath(__file__))

    # FFmpeg yolunu döndür
    return os.path.join(project_dir, ".venv", "Lib", "site-packages", "imageio_ffmpeg", "binaries", "ffmpeg-win-x86_64-v7.1.exe")


# Aynı isimde dosya inerse adını değiştirme
def unique_filename(directory, filename):
    base, ext = os.path.splitext(filename)
    counter = 1
    new_filename = filename
    while os.path.exists(os.path.join(directory, new_filename)):
        new_filename = f"{base} ({counter}){ext}"
        counter += 1
    return new_filename


# Dosyanın indirilme tarihini güncelleme
def update_file_timestamp(filepath):
    if os.path.exists(filepath):
        current_time = time.time()
        os.utime(filepath, (current_time, current_time))



# ProgressBar indirme bilgileri
def progress_hook(d):
    if d['status'] == 'downloading':
        try:
            percent = float(d['_percent_str'].strip('%'))
            downloaded = d.get('downloaded_bytes', 0) / (1024 * 1024)  # MB
            total_size = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            total_size_mb = total_size / (1024 * 1024) if total_size else 0
            speed = d.get('_speed_str', '0MiB')
            eta = d.get('_eta_str', '00:00:00')
            progress_bar['value'] = percent
            progress_label.config(
                text=f"{percent:.1f}% of {total_size_mb:.2f}MiB in {eta} at {speed}/s \n'Tamamlandı' mesajını "
                     f"görene kadar lütfen bekleyin"
            )
            root.update_idletasks()
        except Exception as e:
            print("Progress Hook Hatası:", str(e))



# Türkçe karakterleri değiştirerek dosya adlarını temizleme
def temizle_dosya_adi(dosya_adi):
    dosya_adi = dosya_adi.replace("ı", "i")  # 'ı' harflerini 'i' harfine çevir
    dosya_adi = unicodedata.normalize("NFKD", dosya_adi).encode("ascii", "ignore").decode("utf-8")
    dosya_adi = re.sub(r"[^\w\s.-]", "", dosya_adi)  # Geçersiz karakterleri kaldır
    dosya_adi = dosya_adi.replace(" ", "_")  # Boşlukları alt çizgiye çevir

    return dosya_adi



# 720p video ve ses indirme - birleştirme
def youtube_720p_video_indir(url, kayit_yeri):

    with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
        info = ydl.extract_info(url, download=False)
        video_title = info.get("title", "indirilen_video")

    # Türkçe karakterleri temizle
    temiz_video_title = temizle_dosya_adi(video_title)
    base_filename = os.path.join(kayit_yeri, temiz_video_title)

    # Video ve ses dosyalarının indirilmesi için ayarlar
    ydl_opts_video = {
        "format": "bestvideo[height<=720]/bestvideo",  # 720p video
        "outtmpl": f"{base_filename}_(Video).%(ext)s",
        "progress_hooks": [progress_hook]
    }

    ydl_opts_audio = {
        "format": "bestaudio",
        "outtmpl": f"{base_filename}_(Ses).%(ext)s",
        "progress_hooks": [progress_hook]
    }

    # Video ve ses dosyalarını indir
    with yt_dlp.YoutubeDL(ydl_opts_video) as ydl:
        ydl.download([url])
    with yt_dlp.YoutubeDL(ydl_opts_audio) as ydl:
        ydl.download([url])

    # İndirilen video ve ses dosyalarını bul
    video_path = glob.glob(f"{base_filename}_(Video).*")[0]
    audio_path = glob.glob(f"{base_filename}_(Ses).*")[0]
    output_path = os.path.join(kayit_yeri, f"{temiz_video_title}.mp4")

    # Dosya zaman damgasını güncelle
    update_file_timestamp(video_path)
    update_file_timestamp(audio_path)

    # Video ve ses dosyaları mevcut mu kontrol et
    while not os.path.exists(video_path):
        time.sleep(1)
    while not os.path.exists(audio_path):
        time.sleep(1)

    try:
        # 🔧 FFmpeg yolu al
        ffmpeg_path = get_ffmpeg_path()

        # FFmpeg komutu ile video ve ses birleştiriliyor
        ffmpeg_cmd = [
            ffmpeg_path,
            "-y",  # Üzerine yazmaya zorla
            "-i", video_path,  # Video dosyası
            "-i", audio_path,  # Ses dosyası
            "-c:v", "copy",  # Video codec
            "-c:a", "aac",   # Ses codec
            "-strict", "experimental",  # AAC ses codec kullanımı
            output_path
        ]

        # FFmpeg komutunu çalıştır
        subprocess.run(ffmpeg_cmd, check=True)

        # Geçici video ve ses dosyalarını sil
        os.remove(video_path)
        os.remove(audio_path)

        # İşlem tamamlandığında kullanıcıyı bilgilendir
        messagebox.showinfo("Tamamlandı", "Video ve ses dosyası başarıyla indirildi ve birleştirildi!")

    except Exception as e:
        # Hata mesajı göster
        messagebox.showerror("Hata", f"Birleştirme hatası: {str(e)}")



# 1080p video ve ses indirme - birleştirme
def youtube_1080p_video_indir(url, kayit_yeri):

    with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
        info = ydl.extract_info(url, download=False)
        video_title = info.get("title", "indirilen_video")

    temiz_video_title = temizle_dosya_adi(video_title)
    base_filename = os.path.join(kayit_yeri, temiz_video_title)

    ydl_opts_video = {
        "format": "bestvideo[height=1080]/bestvideo",
        "outtmpl": f"{base_filename}_(Video).%(ext)s",
        "progress_hooks": [progress_hook]
    }

    ydl_opts_audio = {
        "format": "bestaudio",
        "outtmpl": f"{base_filename}_(Ses).%(ext)s",
        "progress_hooks": [progress_hook]
    }

    with yt_dlp.YoutubeDL(ydl_opts_video) as ydl:
        ydl.download([url])
    with yt_dlp.YoutubeDL(ydl_opts_audio) as ydl:
        ydl.download([url])

    video_path = glob.glob(f"{base_filename}_(Video).*")[0]
    audio_path = glob.glob(f"{base_filename}_(Ses).*")[0]
    output_path = os.path.join(kayit_yeri, f"{temiz_video_title}.mp4")

    update_file_timestamp(video_path)
    update_file_timestamp(audio_path)

    while not os.path.exists(video_path):
        time.sleep(1)
    while not os.path.exists(audio_path):
        time.sleep(1)

    try:
        # 🔧 FFmpeg yolu al
        ffmpeg_path = get_ffmpeg_path()

        ffmpeg_cmd = [
            ffmpeg_path,
            "-y",
            "-i", video_path,
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-strict", "experimental",
            output_path
        ]

        subprocess.run(ffmpeg_cmd, check=True)

        os.remove(video_path)
        os.remove(audio_path)

        messagebox.showinfo("Tamamlandı", "Video ve ses dosyası başarıyla indirildi ve birleştirildi!")

    except Exception as e:
        messagebox.showerror("Hata", f"Birleştirme hatası: {str(e)}")



# 4K video ve ses indirme - birleştirme
def youtube_4k_video_indir(url, kayit_yeri):

    with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
        info = ydl.extract_info(url, download=False)
        video_title = info.get("title", "indirilen_video")

    # Türkçe karakterleri temizle
    temiz_video_title = temizle_dosya_adi(video_title)
    base_filename = os.path.join(kayit_yeri, temiz_video_title)

    # Video ve ses dosyalarının indirilmesi için ayarlar
    ydl_opts_video = {
        "format": "bestvideo[height=2160]/bestvideo",  # 4K video (2160p)
        "outtmpl": f"{base_filename}_(Video).%(ext)s",
        "progress_hooks": [progress_hook]
    }

    ydl_opts_audio = {
        "format": "bestaudio",
        "outtmpl": f"{base_filename}_(Ses).%(ext)s",
        "progress_hooks": [progress_hook]
    }

    # Video ve ses dosyalarını indir
    with yt_dlp.YoutubeDL(ydl_opts_video) as ydl:
        ydl.download([url])
    with yt_dlp.YoutubeDL(ydl_opts_audio) as ydl:
        ydl.download([url])

    # İndirilen video ve ses dosyalarını bul
    video_path = glob.glob(f"{base_filename}_(Video).*")[0]
    audio_path = glob.glob(f"{base_filename}_(Ses).*")[0]
    output_path = os.path.join(kayit_yeri, f"{temiz_video_title}.mp4")

    # Dosya zaman damgasını güncelle
    update_file_timestamp(video_path)
    update_file_timestamp(audio_path)

    # Video ve ses dosyaları mevcut mu kontrol et
    while not os.path.exists(video_path):
        time.sleep(1)
    while not os.path.exists(audio_path):
        time.sleep(1)

    try:
        # 🔧 FFmpeg yolu al
        ffmpeg_path = get_ffmpeg_path()

        # FFmpeg komutu ile video ve ses birleştiriliyor
        ffmpeg_cmd = [
            ffmpeg_path,
            "-y",  # Üzerine yazmaya zorla
            "-i", video_path,  # Video dosyası
            "-i", audio_path,  # Ses dosyası
            "-c:v", "copy",  # Video codec
            "-c:a", "aac",   # Ses codec
            "-strict", "experimental",  # AAC ses codec kullanımı
            output_path
        ]

        # FFmpeg komutunu çalıştır
        subprocess.run(ffmpeg_cmd, check=True)

        # Geçici video ve ses dosyalarını sil
        os.remove(video_path)
        os.remove(audio_path)

        # İşlem tamamlandığında kullanıcıyı bilgilendir
        messagebox.showinfo("Tamamlandı", "Video ve ses dosyası başarıyla indirildi ve birleştirildi!")

    except Exception as e:
        # Hata mesajı göster
        messagebox.showerror("Hata", f"Birleştirme hatası: {str(e)}")



# Video sesini indirme
def youtube_ses_indir(url, kayit_yeri):
    with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
        info = ydl.extract_info(url, download=False)
        audio_title = info.get("title", "indirilen_ses")

    # Türkçe karakterleri temizle
    temiz_video_title = temizle_dosya_adi(audio_title)
    output_filename = unique_filename(kayit_yeri, f"{temiz_video_title}.mp3")

    ydl_opts_audio = {
        "format": "bestaudio",
        "outtmpl": os.path.join(kayit_yeri, output_filename),
        "progress_hooks": [progress_hook]
    }
    with yt_dlp.YoutubeDL(ydl_opts_audio) as ydl:
        ydl.download([url])

    update_file_timestamp(os.path.join(kayit_yeri, output_filename))



# İndir butonuna ait fonksiyon
def indir():
    url = url_entry.get()
    secim = secenek_var.get()
    kayit_yeri = os.path.join(os.path.expanduser("~"), "Downloads")

    if not url:
        messagebox.showwarning("Uyarı", "Lütfen bir video linki girin!")
        return

    progress_bar.pack(pady=10)
    progress_bar["value"] = 0
    progress_label.pack()

    def indirme_islemi():
        try:
            if secim == "720p":
                youtube_720p_video_indir(url, kayit_yeri)
            elif secim == "Ses":
                youtube_ses_indir(url, kayit_yeri)
            elif secim == "1080p":
                youtube_1080p_video_indir(url, kayit_yeri)
            elif secim == "4K":
                youtube_4k_video_indir(url, kayit_yeri)
            messagebox.showinfo("Başarılı", "İşlem tamamlandı!")
        except Exception as e:
            messagebox.showerror("Hata", f"Bir hata oluştu:\n{str(e)}")
        finally:
            progress_bar.pack_forget()
            progress_label.pack_forget()

    threading.Thread(target=indirme_islemi, daemon=True).start()



# Arayüz oluşturma
root = tk.Tk()
root.title("Video Downloader")
root.geometry("800x300")
root.config(bg="#fbfbfb")

frame = tk.Frame(root, bg="#fbfbfb")
frame.pack(pady=30, padx=30)

# İndirme seçenekleri
secenek_var = tk.StringVar()
secenekler = ["4K","1080p", "720p", "Ses"]
secenek_var.set(secenekler[0])

# 'İndirme Seçeneği' yazısı
indirme_secenegi_label = tk.Label(frame, text="İndirme Seçeneği:", font=("Helvetica", 12 , ""), bg="#fbfbfb", fg="#2e2e2e")
indirme_secenegi_label.grid(row=0, column=0, padx=10, pady=5)

# 'Video URL' yazısı
video_url_label = tk.Label(frame, text="Video URL:", font=("Helvetica", 12 , ""), bg="#fbfbfb", fg="#2e2e2e")
video_url_label.grid(row=0, column=2, padx=10, pady=5)

# URL alanı
url_entry = tk.Entry(frame, width=50)
url_entry.grid(row=0, column=3, padx=10, pady=5)

# Stil ayarı (Combobox için)
style = ttk.Style()
style.configure("TCombobox", background="white", fieldbackground="white")

# Combobox'u oluşturma
secenek_menu = ttk.Combobox(frame, textvariable=secenek_var, values=secenekler, state="readonly", width=20)
secenek_menu.grid(row=0, column=1, padx=10, pady=5)


# İndir butonu
indir_buton = tk.Button(root, text="⬇ İndir", command=indir, width=11, height=2,
                        font=("Helvetica", 12, "bold"),
                        fg="#fbfbfb", bg="#458bc6",
                        relief="flat",
                        activebackground="#3a688d",
                        activeforeground="#fbfbfb",
                        bd=0,
                        highlightthickness=0)
indir_buton.pack(pady=20)

# ProgressBar
progress_bar = ttk.Progressbar(root, mode="determinate", length=300)
progress_label = tk.Label(root, text="İndirme Başlıyor...", bg="#fbfbfb", fg="#2e2e2e")


# İndirilenler klasörünü açma fonksiyonu
def open_downloads_folder():
    downloads_path = os.path.expanduser("~/Downloads")
    if os.name == "nt":  # Windows
        os.startfile(downloads_path)
    elif os.name == "posix":  # macOS & Linux
        webbrowser.open(downloads_path)


# İndirilenler klasörünü açma butonu (Sol alt köşe)
downloads_button = tk.Button(root, text="📁", command=open_downloads_folder,
                             font=("Helvetica", 13, "bold"), fg="black", bg="#ddd",
                             relief="flat", activebackground="#bbb",
                             activeforeground="black", bd=0, highlightthickness=0)
downloads_button.place(relx=0, rely=1, anchor="sw", x=10, y=-10)


# Koyu mod değişkeni
dark_mode = False

# Tema değiştirme fonksiyonu
def toggle_theme():
    global dark_mode
    if dark_mode:
        root.config(bg="#fbfbfb")
        frame.config(bg="#fbfbfb")
        theme_button.config(text="🌙", bg="#ddd", fg="black", activebackground="#bbb", activeforeground="black")
        downloads_button.config(bg="#ddd", fg="black", activebackground="#bbb", activeforeground="black")

        # Label renklerini açık moda uygun hale getir
        indirme_secenegi_label.config(bg="#fbfbfb", fg="#2e2e2e")
        video_url_label.config(bg="#fbfbfb", fg="#2e2e2e")
        progress_label.config(bg="#fbfbfb", fg="#2e2e2e")

    else:
        root.config(bg="#2e2e2e")
        frame.config(bg="#2e2e2e")
        theme_button.config(text="☀", bg="#444", fg="white", activebackground="#666", activeforeground="#fbfbfb")
        downloads_button.config(bg="#444", fg="white", activebackground="#666", activeforeground="#fbfbfb")

        # Label renklerini koyu moda uygun hale getir
        indirme_secenegi_label.config(bg="#2e2e2e", fg="#fbfbfb")
        video_url_label.config(bg="#2e2e2e", fg="#fbfbfb")
        progress_label.config(bg="#2e2e2e", fg="#fbfbfb")

    dark_mode = not dark_mode

# Koyu mod butonu
theme_button = tk.Button(root, text="🌙", command=toggle_theme,
                         font=("Helvetica", 13, "bold"),
                         fg="black", bg="#ddd",
                         relief="flat",
                         activebackground="#bbb",
                         activeforeground="black",
                         bd=0, highlightthickness=0)
theme_button.place(relx=1, rely=1, anchor="se", x=-10, y=-10)

root.mainloop()
