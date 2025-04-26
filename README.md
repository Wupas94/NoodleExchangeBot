# Noodle Exchange Bot

Bot Discord do zarządzania pracownikami i systemem punktowym.

## Funkcje

- System punktowy (dodawanie/odejmowanie punktów)
- System awansów i degradacji
- Zarządzanie rolami pracowników
- System ostrzeżeń
- Historia pracownika
- Lista pracowników

## Wymagania

- Python 3.8 lub nowszy
- Discord.py 2.3.2 lub nowszy
- Python-dotenv 1.0.0 lub nowszy

## Instalacja

1. Sklonuj repozytorium:
```bash
git clone https://github.com/twoj-username/noodle-exchange-bot.git
cd noodle-exchange-bot
```

2. Zainstaluj wymagane pakiety:
```bash
pip install -r requirements.txt
```

3. Utwórz plik `.env` w głównym katalogu projektu i dodaj swój token Discord:
```
DISCORD_TOKEN=twoj_token_discord
```

## Konfiguracja

1. Upewnij się, że bot ma odpowiednie uprawnienia na serwerze Discord:
   - Zarządzanie rolami
   - Czytanie wiadomości
   - Wysyłanie wiadomości
   - Zarządzanie wiadomościami

2. Skonfiguruj role w pliku `bot.py`:
   - Ustaw odpowiednie ID ról dla ścieżek kariery
   - Ustaw role uprawnień (manager, admin)

## Uruchomienie

```bash
python bot.py
```

## Komendy

- `/punkty` - Zarządzanie punktami pracownika
- `/awansuj` - Awansowanie pracownika
- `/degrad` - Degradacja pracownika
- `/historia` - Historia pracownika
- `/warn` - Dodawanie ostrzeżenia
- `/zwolnij` - Zwolnienie pracownika
- `/lista_pracownikow` - Lista wszystkich pracowników
- `/test_uprawnienia` - Test uprawnień użytkownika
- `/sprawdz_role` - Sprawdzenie ról użytkownika

## Bezpieczeństwo

- Token bota jest przechowywany w pliku `.env`
- Wszystkie komendy wymagają odpowiednich uprawnień
- Historia działań jest logowana

## Wsparcie

W przypadku problemów, utwórz issue w repozytorium projektu. 