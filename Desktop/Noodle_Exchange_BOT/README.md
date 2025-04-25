# Noodle Exchange BOT

Bot Discord do zarządzania personelem restauracji Noodle Exchange.

## Funkcje

- Zarządzanie pracownikami (zatrudnianie, zwalnianie)
- System awansów i degradacji
- System punktowy (plusy, minusy, upomnienia)
- Historia pracowników
- System ostrzeżeń

## Wymagania

- Python 3.8+
- discord.py
- python-dotenv

## Instalacja

1. Sklonuj repozytorium
2. Zainstaluj wymagane pakiety:
```bash
pip install -r requirements.txt
```
3. Stwórz plik `.env` i dodaj token bota:
```
DISCORD_TOKEN=twój_token_bota
```
4. Uruchom bota:
```bash
python bot.py
```

## Komendy

- `/job` - zatrudnia nowego pracownika
- `/awansuj` - awansuje pracownika
- `/degrad` - degraduje pracownika
- `/plus` - dodaje plus
- `/minus` - dodaje minus
- `/upomnienie` - dodaje upomnienie
- `/warn` - dodaje ostrzeżenie
- `/historia` - wyświetla historię pracownika
- `/lista_pracownikow` - wyświetla listę wszystkich pracowników
- `/zwolnij` - zwalnia pracownika

## Licencja

MIT 