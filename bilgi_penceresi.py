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
            "okul_turu": "lise",
            "zaman_asimi_dakika": 1,
            "mesaj_konumu": "merkez",
            "boyut_yuzde": 25
        }

        self.json_yukle()
        self.timer_aktif = False
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
        """Zamanlayıcıyı başlat"""
        if not self.timer_aktif:
            self.timer_aktif = True
            self.timer_thread = threading.Thread(target=self.timer_loop, daemon=True)
            self.timer_thread.start()

    def timer_loop(self):
        """Arkaplanda sürekli çalışan zamanlayıcı"""
        while self.timer_aktif:
            try:
                # Ayarları yükle
                with open(AYAR_DOSYASI, 'r', encoding='utf-8') as f:
                    settings = json.load(f)

                # zaman_asimi_dakika'i saniyeye çevir
                saniye = settings.get('zaman_asimi_dakika', 1) * 1

                #print(f"⏱ Zamanlayıcı başladı: {saniye} saniye sonra create_image.py çalıştırılacak...")

                # Ayarlanmış süre kadar bekle
                time.sleep(saniye)

                # create_image.py çalıştır
                if self.timer_aktif:
                    #print(f"✓ {saniye} saniye geçti. create_image.py çalıştırılıyor...")
                    subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "create_image.py")])
                    #print("✓ create_image.py tamamlandı.")

            except Exception as e:
                print(f"✗ Hata: {e}")
                time.sleep(5)

    def on_closing(self):
        """Pencere kapatılırken"""
        self.timer_aktif = False
        self.destroy()

    # ---------------------------------------------------------------------

    def arayuz(self):

        # Arka plan
        self.config(bg="#34495e")

        # Kapatma düğmesi (sol üst köşe)
        kapat_frame = tk.Frame(self, bg="#34495e")
        kapat_frame.pack(side="top", anchor="nw", padx=5, pady=5)

        # GİZLE DÜĞMESİ
        gizle_buton = ttk.Button(
            kapat_frame,
            text="Gizle",
            command=self.withdraw  # Pencereyi gizler
        )
        gizle_buton.pack(side="left")

        ana_frame = tk.Frame(self, bg="#138d90", padx=15, pady=15)
        ana_frame.pack(pady=20)

        ic_frame = tk.Frame(ana_frame, bg="#aeb6bf", padx=15, pady=15)
        ic_frame.pack()

        # ---------------------------------------------------------------
        # OKUL TÜRÜ
        # ---------------------------------------------------------------

        baslik1 = tk.Label(ic_frame, text="Okul Türü Seçin",
                           font=("Arial", 12, "bold"), bg="#aeb6bf")
        baslik1.pack()

        self.okul_var = tk.StringVar(value=self.settings["okul_turu"])

        for tur in ["ilkokul", "ortaokul", "lise"]:
            ttk.Radiobutton(ic_frame, text=tur,
                            value=tur,
                            variable=self.okul_var,
                            command=lambda t=tur: self.set_okul_turu(t)
                            ).pack(anchor="w", pady=2)

        ttk.Separator(ic_frame).pack(fill="x", pady=10)

        # ---------------------------------------------------------------
        # ZAMAN AŞIMI (Dakika)
        # ---------------------------------------------------------------

        tk.Label(ic_frame, text="Zaman Aşımı (dakika)",
                 font=("Arial", 12, "bold"), bg="#aeb6bf").pack()

        self.zaman_slider = ttk.Scale(
            ic_frame, from_=1, to=60, orient="horizontal",
            command=lambda x: self.update_zaman_label()
        )
        self.zaman_slider.pack(fill="x")

        self.zaman_label = tk.Label(
            ic_frame,
            text=f"{self.settings['zaman_asimi_dakika']} Dakika",
            bg="#aeb6bf"
        )
        self.zaman_label.pack()

        self.zaman_slider.set(self.settings["zaman_asimi_dakika"])

        ttk.Separator(ic_frame).pack(fill="x", pady=10)

        # ---------------------------------------------------------------
        # MESAJ KONUMU
        # ---------------------------------------------------------------

        tk.Label(ic_frame, text="Mesaj Konumu",
                 font=("Arial", 12, "bold"), bg="#aeb6bf").pack()

        self.mesaj_konum_var = tk.StringVar(
            value=self.settings["mesaj_konumu"])

        konumlar = [
            "ust_sol_kose",
            "ust_sag_kose",
            "alt_sol_kose",
            "alt_sag_kose",
            "merkez"
        ]

        for k in konumlar:
            ttk.Radiobutton(ic_frame, text=k,
                            value=k,
                            variable=self.mesaj_konum_var
                            ).pack(anchor="w", pady=2)

        ttk.Separator(ic_frame).pack(fill="x", pady=10)

        # ---------------------------------------------------------------
        # BOYUT (%)
        # ---------------------------------------------------------------

        tk.Label(ic_frame, text="Boyut (%)",
                 font=("Arial", 12, "bold"), bg="#aeb6bf").pack()

        self.boyut_slider = ttk.Scale(
            ic_frame,
            from_=25,
            to=100,
            orient="horizontal",
            command=lambda x: self.update_boyut_label()
        )
        self.boyut_slider.pack(fill="x")

        self.boyut_label = tk.Label(
            ic_frame,
            text=f"%{self.settings['boyut_yuzde']}",
            bg="#aeb6bf"
        )
        self.boyut_label.pack()

        self.boyut_slider.set(self.settings["boyut_yuzde"])

        # ---------------------------------------------------------------
        # KAYDET BUTONU
        # ---------------------------------------------------------------

        ttk.Button(self, text=f"Ayarları Kaydet {arka.auto_start_control()}" ,
               command=self.ayar_kaydet).pack(pady=15)

 

    # ---------------------------------------------------------------------

    def set_okul_turu(self, tur):
        self.settings["okul_turu"] = tur

    # ---------------------------------------------------------------------

    def update_zaman_label(self):
        dakika = int(float(self.zaman_slider.get()))
        self.settings["zaman_asimi_dakika"] = dakika
        self.zaman_label.config(text=f"{dakika} dakika")

    # ---------------------------------------------------------------------

    def update_boyut_label(self):
        raw = float(self.boyut_slider.get())
        yuvarlak = int(round(raw / 25) * 25)  # 25, 50, 75, 100

        # 25–100 arasında tut
        yuvarlak = max(25, min(100, yuvarlak))

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
        subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "create_image.py")])

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