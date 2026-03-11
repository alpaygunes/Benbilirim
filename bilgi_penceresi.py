#!/usr/bin/env python3
import fcntl
import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import subprocess
import threading
import time
import sys

# Modül seviyesinden `arka` nesnesini içe aktar
try:
    from arkaplan import arka
except Exception:
    arka = None

AYAR_DOSYASI = os.path.join(os.path.dirname(__file__), "ayarlar.json")

arka.check_double_instance(__file__) if arka is not None else None

class AyarPenceresi(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Bilgi Penceresi")
        self.geometry("420x650")
        self.resizable(False, False)
        self.withdraw()  # Pencereyi gizle

        # Varsayılan ayarlar
        self.settings = { 
            "zaman_asimi_dakika": 120,
            "mesaj_konumu": "merkez",
            "boyut_yuzde": 25
        }

        self.json_yukle()
        self.timer_stop_event = None
        self.timer_thread = None

        # Tray ikonu veya kontrol penceresi
        self.show_control_window()
        self.baslat_timer()

        # Mevcut süreç PID'sini al (arkaplan nesnesi kullanılarak, varsa)
        try:
            self.arka_pid = arka.get_current_pid() if arka is not None else None
        except Exception:
            self.arka_pid = None

        # Arkaplan kontrolünü başlat (auto-start flag'ini ayarlar)
        try:
            if arka is not None:
                start_mode = arka.auto_start_control()
                if start_mode != "interactive":
                    pass
                    self.after(1000, self.withdraw) 
        except Exception:
            pass
    

    # ---------------------------------------------------------------------

    def show_control_window(self):
        """Kontrol penceresini göster"""
        self.deiconify()
        self.arayuz()

    def baslat_timer(self):
        """Zamanlayıcıyı başlat veya yeniden başlat"""
        if self.timer_stop_event:
            self.timer_stop_event.set()
        
        self.timer_stop_event = threading.Event()
        self.timer_thread = threading.Thread(target=self.timer_loop, args=(self.timer_stop_event,), daemon=True)
        self.timer_thread.start()

    def timer_loop(self, stop_event):
        """Arkaplanda sürekli çalışan zamanlayıcı"""
        if not os.path.exists(os.path.join(os.path.dirname(__file__), "data", "data.json")):
            print("data.json dosyası yok, timer_loop fonksiyonu sonlandırılıyor...")
            return

        while not stop_event.is_set():
            try:
                # Ayarları yükle
                with open(AYAR_DOSYASI, 'r', encoding='utf-8') as f:
                    settings = json.load(f)

                # zaman_asimi_dakika'i saniyeye çevir
                saniye = settings.get('zaman_asimi_dakika', 1) 

                # Ayarlanmış süre kadar bekle (veya durdurulana kadar)
                if stop_event.wait(saniye):
                    break

                if not stop_event.is_set():
                    subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "create_image.py")])

            except Exception as e:
                print(f"✗ Hata: {e}")
                if stop_event.wait(5):
                    break

    def on_closing(self):
        """Pencere kapatılırken"""
        if self.timer_stop_event:
            self.timer_stop_event.set()
        self.destroy()

    # ---------------------------------------------------------------------

    def arayuz(self):

        # Arka plan
        # Pencere varsayılanı kullanılacak

        # Kapatma düğmesi (sol üst köşe)
        kapat_frame = tk.Frame(self)
        kapat_frame.pack(side="top", anchor="nw", padx=5, pady=5)

        # GİZLE DÜĞMESİ
        gizle_buton = ttk.Button(
            kapat_frame,
            text="Gizle",
            command=self.withdraw  # Pencereyi gizler
        )
        gizle_buton.pack(side="left")
 

        ic_frame = tk.Frame(self, padx=15, pady=35)
        ic_frame.pack()

        # ---------------------------------------------------------------
        # ZAMAN AŞIMI (Dakika)
        # ---------------------------------------------------------------

        tk.Label(ic_frame, text="Zaman Aşımı (dakika)",
                 font=("Arial", 12, "bold")).pack(anchor="w")

        self.zaman_slider = ttk.Scale(
            ic_frame, from_=1, to=60, orient="horizontal",
            command=lambda x: self.update_zaman_label()
        )
        self.zaman_slider.pack(fill="x")

        self.zaman_label = tk.Label(
            ic_frame,
            text=f"{self.settings['zaman_asimi_dakika']} Dakika"
        )
        self.zaman_label.pack()

        self.zaman_slider.set(self.settings["zaman_asimi_dakika"])

        ttk.Separator(ic_frame).pack(fill="x", pady=30)

        # ---------------------------------------------------------------
        # MESAJ KONUMU
        # ---------------------------------------------------------------

        tk.Label(ic_frame, text="Bilgi Kutusu Konumu",
                 font=("Arial", 12, "bold")).pack(pady=10,anchor="w")

        self.mesaj_konum_var = tk.StringVar(
            value=self.settings["mesaj_konumu"])

        konumlar = [
            "ust_sol_kose",
            "ust_sag_kose",
            "alt_sol_kose",
            "alt_sag_kose",
            "merkez"
        ]

        konum_etiketleri = {
            "ust_sol_kose": "Sol Üst Köşe",
            "ust_sag_kose": "Sağ Üst Köşe",
            "alt_sol_kose": "Sol Alt Köşe",
            "alt_sag_kose": "Sağ Alt Köşe",
            "merkez": "Merkez"
        }

        for k in konumlar:
            txt = konum_etiketleri.get(k, k)
            ttk.Radiobutton(ic_frame, 
                            text=txt,
                            value=k,
                            variable=self.mesaj_konum_var
                            ).pack(anchor="w", pady=2)

        ttk.Separator(ic_frame).pack(fill="x", pady=30)

        # ---------------------------------------------------------------
        # BOYUT (%)
        # ---------------------------------------------------------------

        tk.Label(ic_frame, text="Kutu Boyutu (%)",
                 font=("Arial", 12, "bold")).pack(pady=10,anchor="w")

        self.boyut_slider = ttk.Scale(
            ic_frame,
            from_=10,
            to=100,
            orient="horizontal",
            command=lambda x: self.update_boyut_label()
        )
        self.boyut_slider.pack(fill="x")

        self.boyut_label = tk.Label(
            ic_frame,
            text=f"%{self.settings['boyut_yuzde']}"
        )
        self.boyut_label.pack()

        self.boyut_slider.set(self.settings["boyut_yuzde"])

        # ---------------------------------------------------------------
        # KAYDET BUTONU
        # ---------------------------------------------------------------

        ttk.Button(self, text=f"Ayarları Kaydet" ,
               command=self.ayar_kaydet).pack(pady=15)

        tk.Label(self, text="Kayseri İl Milli Eğitim Müdürlüğü - 2026",
                 font=("Arial", 9, "italic"), fg="gray").pack(side="bottom", pady=10)

 

 

    def update_zaman_label(self):
        dakika = int(float(self.zaman_slider.get()))
        self.settings["zaman_asimi_dakika"] = dakika
        self.zaman_label.config(text=f"{dakika} dakika")

    # ---------------------------------------------------------------------

    def update_boyut_label(self):
        raw = float(self.boyut_slider.get())
        yuvarlak = int(round(raw / 5) * 5)  # 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100

        # 10 arasında tut
        yuvarlak = max(10, min(100, yuvarlak))

        self.boyut_label.config(text=f"%{yuvarlak}")
        self.settings["boyut_yuzde"] = yuvarlak

    # ---------------------------------------------------------------------

    def ayar_kaydet(self):

        self.settings["mesaj_konumu"] = self.mesaj_konum_var.get()
        with open(AYAR_DOSYASI, "w", encoding="utf-8") as f:
            json.dump(self.settings, f, indent=4, ensure_ascii=False)

        # data.json yoksa excel2json çalıştır
        if not os.path.exists(os.path.join(os.path.dirname(__file__), "data", "data.json")):
            subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "excel2json.py")])

        messagebox.showinfo("Bilgi", "Ayarlar kaydedildi.")
        self.baslat_timer() # Zamanlayıcıyı yeni ayarlarla başlat
        

    # ---------------------------------------------------------------------

    def json_yukle(self):
        if os.path.exists(AYAR_DOSYASI):
            try:
                with open(AYAR_DOSYASI, "r", encoding="utf-8") as f:
                    yuklenen = json.load(f)
                    self.settings.update(yuklenen)
            except:
                pass


# -------------------------------------------------------------------------
if __name__ == "__main__":
    app = AyarPenceresi()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()