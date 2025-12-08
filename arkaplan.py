#!/usr/bin/env python3
"""Arkaplan yardımcı sınıfı

Bu modül küçük bir `Arkaplan` sınıfı sağlar. Kullanım amaçları:
- Çalışan uygulamanın kendi PID'sini almak
- Belirli bir süreç adıyla eşleşen PID(leri) bulmak
- Aynı anda birden fazla örneğin çalışmasını engellemek

Basit CLI desteklenir: çalıştırıldığında kendi PID'sini yazdırır.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import signal
import time
from typing import List, Optional


class Arkaplan: 

    def __init__(self, root=None) -> None: 
        self.root = root

    def get_current_pid(self) -> int:
        """Bu Python sürecinin PID'sini döner."""
        return os.getpid()

    def check_double_instance(self, process_name: str = "bilgi_penceresi.py") -> None:
        """Tekil instance kilidi için basit kontrol.

        - Geçerli lock dosyası: `<tempdir>/<process_basename>.lock`.
        - Lock yoksa oluşturup kendi PID'imizi yazar.
        - Lock varsa içindeki PID'i okur. PID çalışan bir süreçse onu SIGTERM ile durdurmaya çalışır
          (başarısız olursa kısa bekleyip SIGKILL gönderir). PID çalışmıyorsa lock dosyasını güncelleyip
          kendi PID'imizi yazar.
        """

        # lock dosya adını process_name'den türet (örn. bilgi_penceresi.py -> bilgi_penceresi.lock)
        base = os.path.splitext(os.path.basename(process_name))[0]
        lock_filename = f"{base}.lock"
        tmpdir = tempfile.gettempdir()
        lock_path = os.path.join(tmpdir, lock_filename)

        current_pid = self.get_current_pid()

        # Eğer lock dosyası yoksa oluştur ve kendi PID'ini yaz
        if not os.path.exists(lock_path):
            try:
                with open(lock_path, "w") as f:
                    f.write(str(current_pid))
            except OSError:
                pass
            return

        # Lock dosyasından PID oku
        try:
            with open(lock_path, "r") as f:
                content = f.read().strip()
            other_pid = int(content) if content else None
        except Exception:
            other_pid = None

        # Eğer dosyada geçerli bir PID yoksa üzerine kendi PID'imizi yaz
        if not other_pid or other_pid <= 0:
            try:
                with open(lock_path, "w") as f:
                    f.write(str(current_pid))
            except OSError:
                pass
            return

        # PID ile bir process var mı kontrol et
        exists = False
        try:
            os.kill(other_pid, 0)
            exists = True
        except ProcessLookupError:
            exists = False
        except PermissionError:
            # Başka kullanıcıya ait olabilir; var olduğunu kabul et
            exists = True

        if exists:
            # Önce SIGTERM dene, kısa süre bekle, sonra zorla SIGKILL
            try:
                os.kill(other_pid, signal.SIGTERM)
            except PermissionError:
                # Yetki yoksa ilerleyemeyiz
                return
            except ProcessLookupError:
                # Zaten yok
                pass

            # Küçük bir bekleme döngüsü ile sürecin bitip bitmediğini kontrol et
            for _ in range(30):
                time.sleep(0.1)
                try:
                    os.kill(other_pid, 0)
                except ProcessLookupError:
                    break
            else:
                try:
                    os.kill(other_pid, signal.SIGKILL)
                except Exception:
                    pass

            # Son durumda lock dosyasını kendi PID'imizle güncelle
            try:
                with open(lock_path, "w") as f:
                    f.write(str(current_pid))
            except OSError:
                pass
        else:
            # Eski (stale) PID için lock dosyasını güncelle
            try:
                with open(lock_path, "w") as f:
                    f.write(str(current_pid))
            except OSError:
                pass

    def auto_start_control(self) -> None:
        """Otomatik başlatma kontrolü yapar.

        Bu metod, sürecin ebeveyn süreç zincirini inceleyerek uygulamanın
        oturum açıldığında otomatik olarak mı başlatıldığını yoksa kullanıcı
        etkileşimiyle mi başlatıldığını (örn. terminal veya dosya yöneticisi)
        tahmin etmeye çalışır.

        Sonuç olarak bu nesnenin `start_mode` özniteliğini ayarlar ve
        tahmini döndürür: `'auto'`, `'interactive'` veya `'unknown'`.
        """

        def _read_proc_comm(pid: int) -> str:
            try:
                with open(f"/proc/{pid}/comm", "r", encoding="utf-8") as f:
                    return f.read().strip()
            except Exception:
                return ""

        def _read_proc_cmdline(pid: int) -> str:
            try:
                with open(f"/proc/{pid}/cmdline", "rb") as f:
                    data = f.read()
                    return data.replace(b"\x00", b" ").decode("utf-8", errors="ignore").strip()
            except Exception:
                return ""

        # Bilinen oturum yöneticileri / autostart kaynakları ve terminaller
        session_parents = {
            "gnome-session", "gnome-session-binary", "startkde", "ksmserver",
            "lxsession", "xfce4-session", "mate-session", "lightdm", "gdm", "sdm",
            "systemd"
        }

        interactive_parents = {
            "bash", "zsh", "fish", "sh", "dash",
            "gnome-terminal", "konsole", "xterm", "terminator", "tilix", "alacritty",
            "uxterm", "rxvt", "tmux", "screen", "kitty",
            "nautilus", "thunar", "dolphin"
        }

        # Topla ebeveyn zinciri
        chain = []  # list of (pid, comm, cmdline)
        try:
            pid = os.getpid()
            # Yüksüz döngü ile üst süreçlere bak
            for _ in range(20):
                try:
                    # PPid almak için /proc/<pid>/status oku
                    with open(f"/proc/{pid}/status", "r", encoding="utf-8") as sf:
                        lines = sf.readlines()
                    ppid = None
                    for l in lines:
                        if l.startswith("PPid:"):
                            try:
                                ppid = int(l.split()[1])
                            except Exception:
                                ppid = None
                            break
                    if ppid is None or ppid <= 0 or ppid == pid:
                        break
                except Exception:
                    break

                comm = _read_proc_comm(ppid)
                cmdline = _read_proc_cmdline(ppid)
                chain.append((ppid, comm, cmdline))
                if ppid == 1:
                    break
                pid = ppid
        except Exception:
            chain = []

        # Karar verme: zincirde terminal veya shell varsa kullanıcı etkileşimi
        found_interactive = False
        found_session = False
        for pid, comm, cmdline in chain:
            name = (comm or "").lower()
            cmd = (cmdline or "").lower()
            # systemd için user-service olup olmadığını kontrol et
            if name.startswith("systemd") and "--user" in cmd:
                found_session = True
            if any(s in name for s in session_parents):
                found_session = True
            if any(t in name for t in interactive_parents):
                found_interactive = True

        if found_interactive and not found_session:
            self.start_mode = "interactive"
        elif found_session and not found_interactive:
            self.start_mode = "auto"
        elif found_session and found_interactive:
            # Eğer her ikisi varsa daha kesin bilgi için zinciri baştan yorumla:
            # en yakın ebeveyn hangisi ise ona öncelik ver
            if chain:
                nearest = chain[0][1].lower()
                if any(t in nearest for t in interactive_parents):
                    self.start_mode = "interactive"
                else:
                    self.start_mode = "auto"
            else:
                self.start_mode = "unknown"
        else:
            self.start_mode = "unknown"

        # Ayrıca zinciri yardımcı amaçla sakla
        self._start_parent_chain = chain
        return self.start_mode

# Modül-seviyesinde kullanılmak üzere tek bir Arkaplan nesnesi oluştur
arka = Arkaplan()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Arkaplan yardımcı - PID alma aracı")
    parser.add_argument("--name", "-n", help="Süreç adı ile PID ara", default=None)
    args = parser.parse_args()

    if args.name:
        pids = arka.find_pids_by_name(args.name)
        if pids:
            print("Bulunan PID'ler:", ",".join(str(p) for p in pids))
        else:
            print("Eşleşen süreç bulunamadı")
    else:
        print(arka.get_current_pid())
