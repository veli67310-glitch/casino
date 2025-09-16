@echo off
title Bot ve Webhook Başlatıcı
color 0A

echo ================================================
echo        BOT VE WEBHOOK BAŞLATILIYOR...
echo ================================================
echo.

REM Python'un yüklenip yüklenmediğini kontrol et
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo HATA: Python bulunamadı!
    echo Lütfen Python'u yükleyin.
    pause
    exit /b 1
)

REM Gerekli kütüphaneleri yükle
echo Gerekli kütüphaneler kontrol ediliyor...
pip install -r requirements.txt >nul 2>&1

REM Yeni pencerede webhook'u başlat
echo Webhook başlatılıyor...
start "Helius Webhook" /MIN python helius_webhook.py

REM 2 saniye bekle
timeout /t 2 /nobreak >nul

REM Ana bot'u başlat
echo Bot başlatılıyor...
python main.py

REM Bot kapandığında webhook'u da kapat
echo.
echo Bot kapandı. Webhook kapatılıyor...
taskkill /f /fi "WindowTitle eq Helius Webhook*" >nul 2>&1

echo.
echo Tüm servisler durduruldu.
pause