# Noodle Exchange BOT

Bot Discord do zarządzania pracownikami i systemem punktowym.

## Funkcje

- System zatrudniania pracowników (`/job`)
- System punktowy (plusy, minusy, upomnienia)
- System awansów i degradacji
- Historia pracowników
- System ostrzeżeń

## Wymagania

- Python 3.8+
- discord.py 2.0+
- Uprawnienia bota na Discord:
  - Zarządzanie rolami
  - Wysyłanie wiadomości
  - Zarządzanie wiadomościami
  - Wyświetlanie członków serwera

## Instalacja

1. Sklonuj repozytorium:
```bash
git clone https://github.com/twojuser/Noodle_Exchange_BOT.git
cd Noodle_Exchange_BOT
```

2. Zainstaluj wymagane pakiety:
```bash
pip install -r requirements.txt
```

3. Utwórz plik `.env` i dodaj token bota:
```env
DISCORD_TOKEN=twoj_token_bota
```

4. Uruchom bota:
```bash
python bot.py
```

## Konfiguracja

1. W pliku `bot.py` znajdziesz klasę `Role` - zaktualizuj ID ról zgodnie z Twoim serwerem
2. Dostosuj uprawnienia do zarządzania w zmiennej `ROLE_ZARZADZAJACE`

## Komendy

- `/job @użytkownik` - zatrudnia nowego pracownika
- `/plus @użytkownik powód` - dodaje plus
- `/minus @użytkownik powód` - dodaje minus
- `/upomnienie @użytkownik powód` - dodaje upomnienie
- `/warn @użytkownik powód` - dodaje ostrzeżenie
- `/historia @użytkownik` - wyświetla historię pracownika
- `/awansuj @użytkownik ścieżka poziom` - awansuje pracownika
- `/degrad @użytkownik powód` - degraduje pracownika
- `/zwolnij @użytkownik powód` - zwalnia pracownika

## Licencja

MIT 