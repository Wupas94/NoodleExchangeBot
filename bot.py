# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
from discord import app_commands
import os
import json
import asyncio
from datetime import datetime
import traceback
from typing import Optional, Dict, List, Any
from dotenv import load_dotenv

# --- Konfiguracja Początkowa ---
load_dotenv()
# !!! Lista ID serwerów, na których bot ma działać !!!
# Używamy teraz listy ID liczbowych
GUILD_IDS_LIST = [
    1021373051272704130

    # Dodaj więcej ID serwerów tutaj, jeśli potrzebujesz
]
# Tworzymy listę obiektów discord.Object dla setup_hook
GUILD_OBJS = [discord.Object(id=gid) for gid in GUILD_IDS_LIST]

JSON_FILE = 'pracownicy.json'
ITEMS_PER_PAGE = 7 # Używane w /historia? (nie widać implementacji paginacji)

# --- Role IDs ---
# !!! KRYTYCZNE ZAŁOŻENIE: Poniższe ID ról MUSZĄ być IDENTYCZNE !!!
# !!! na WSZYSTKICH serwerach wymienionych w GUILD_IDS_LIST !!!
# !!! Jeśli ID się różnią, funkcjonalność bota będzie BŁĘDNA na niektórych serwerach !!!
class Role:
    # Role administracyjne
    NADZOR_PRACY = 1031216295905079336
    WLASCICIEL_FIRMY = 1021376435530760233
    ZASTEPCA_SZEFA = 1094378926333243434
    MENADZER = 1021687974104141864
    KIEROWNIK = 1322094531302395935
    ASYSTENT_KIEROWNIKA = 1359944124932948111
    TECHNIK = 1364712468680806532
    # Role podstawowe
    REKRUT = 1119626832262738000
    PRACOWNIK = 1021384419740753970
    OCHRONA = 1022826867960582204
    # Ścieżka Ochrony - Zarządzanie
    NADZOR_OCHRONY = 1283101978129469515
    SZEF_OCHRONY = 1022827507302543450
    ZASTEPCA_SZEFA_OCHRONY = 1107424252824653834
    ASYSTENT_SZEFA_OCHRONY = 1343271396737945600
    EGZAMINATOR_OCHRONY = 1343272656602005524
    SZKOLENIOWIEC_OCHRONY = 1343272696233857106
    # Ścieżka Ochrony - Rozwój
    STARSZY_OCHRONIARZ = 1283104625037279296
    DOSWIADCZONY_OCHRONIARZ = 1283104620658556948
    OCHRONIARZ_LICENCJONOWANY = 1259930187232051283
    OCHRONIARZ = 1118303102618046505
    MLODSZY_OCHRONIARZ = 1118302455013322923
    PIES_OCHRONY = 1270883261458939975
    # Ścieżka Gastronomii
    OBSLUGA_BARU = 1335274785541722143
    SZEF_KUCHNI = 1166755931015622737
    KUCHARZ = 1119627473634734220
    ASYSTENT_KUCHARZA = 1119627348074045512
    KELNER = 1119627033589338183
    # System punktowy - Plusy (Role Poziomowe)
    PLUS1 = 1125425345433194506
    PLUS2 = 1125425435535212544
    PLUS3 = 1125425499980709909
    # System punktowy - Minusy (Role Poziomowe)
    MINUS1 = 1021686482236354590
    MINUS2 = 1021687044793188372
    MINUS3 = 1021687258815922230
    # System punktowy - Upomnienia (Role Poziomowe)
    UPOMNIENIE1 = 1292900587868000287
    UPOMNIENIE2 = 1292900582192840856
    UPOMNIENIE3 = 1292900560093188096

# --- Ścieżki awansu i mapowanie ---
SCIEZKA_OCHRONY = [Role.REKRUT, Role.MLODSZY_OCHRONIARZ, Role.OCHRONIARZ, Role.OCHRONIARZ_LICENCJONOWANY, Role.DOSWIADCZONY_OCHRONIARZ, Role.STARSZY_OCHRONIARZ]
SCIEZKA_GASTRONOMII = [Role.REKRUT, Role.KELNER, Role.ASYSTENT_KUCHARZA, Role.KUCHARZ, Role.SZEF_KUCHNI, Role.OBSLUGA_BARU]
SCIEZKI_MAP = {"ochrona": SCIEZKA_OCHRONY, "gastronomia": SCIEZKA_GASTRONOMII}
SCIEZKI_WYBORY = [app_commands.Choice(name=n.replace('_',' ').title(), value=n) for n in SCIEZKI_MAP.keys()]

# --- Grupy Ról ---
ROLE_ZARZADZAJACE = [r for r in [
    Role.NADZOR_PRACY, Role.WLASCICIEL_FIRMY, Role.ZASTEPCA_SZEFA, Role.MENADZER, Role.KIEROWNIK, Role.ASYSTENT_KIEROWNIKA,
    Role.TECHNIK, Role.NADZOR_OCHRONY, Role.SZEF_OCHRONY, Role.ZASTEPCA_SZEFA_OCHRONY, Role.ASYSTENT_SZEFA_OCHRONY,
    Role.EGZAMINATOR_OCHRONY, Role.SZKOLENIOWIEC_OCHRONY
] if r is not None]

ROLE_STANOWISKOWE_SCIEZKI = list(set([
    Role.MLODSZY_OCHRONIARZ, Role.OCHRONIARZ, Role.OCHRONIARZ_LICENCJONOWANY, Role.DOSWIADCZONY_OCHRONIARZ, Role.STARSZY_OCHRONIARZ,
    Role.KELNER, Role.ASYSTENT_KUCHARZA, Role.KUCHARZ, Role.SZEF_KUCHNI, Role.OBSLUGA_BARU
]))

ROLE_PRACOWNICZE_PODSTAWOWE = list(set([
    Role.REKRUT, Role.PRACOWNIK, Role.OCHRONA]
    + ROLE_STANOWISKOWE_SCIEZKI
))

ROLE_WSZYSTKIE_PRACA = list(set(ROLE_ZARZADZAJACE + ROLE_PRACOWNICZE_PODSTAWOWE))

ROLE_PUNKTOWE = [
    Role.PLUS1, Role.PLUS2, Role.PLUS3,
    Role.MINUS1, Role.MINUS2, Role.MINUS3,
    Role.UPOMNIENIE1, Role.UPOMNIENIE2, Role.UPOMNIENIE3
]

ROLE_WSZYSTKIE_DO_USUNIECIA = set(ROLE_WSZYSTKIE_PRACA + ROLE_PUNKTOWE)

# --- Mapowanie Punktów ---
POINT_ROLE_LEVELS_MAP = {
    "plusy": {1: Role.PLUS1, 2: Role.PLUS2, 3: Role.PLUS3},
    "minusy": {1: Role.MINUS1, 2: Role.MINUS2, 3: Role.MINUS3},
    "upomnienia": {1: Role.UPOMNIENIE1, 2: Role.UPOMNIENIE2, 3: Role.UPOMNIENIE3}
}

# --- Kanały Logowania ---
# !!! UWAGA: Poniższe ID kanałów muszą istnieć na KAŻDYM serwerze z GUILD_IDS_LIST, !!!
# !!! na którym chcesz mieć logowanie! To jest uproszczenie. Lepszym rozwiązaniem !!!
# !!! byłoby przechowywanie ID kanałów per serwer (np. w pliku konfiguracyjnym). !!!
LOG_CHANNEL_IDS: Dict[str, int] = {
    "hr": 1307741954938765342,       # Logi zatrudnień, zwolnień itp.
    "punkty": 1307741954938765342,   # Logi plusów, minusów, upomnień
    "awanse": 1307741954938765342    # Logi awansów, degradacji
    # Upewnij się, że ten kanał (ID: 1307741954938765342) istnieje na WSZYSTKICH serwerach z GUILD_IDS_LIST
    # i że bot ma uprawnienia do pisania na nim.
}

# --- Słownik pracowników (teraz zagnieżdżony per serwer) i Lock ---
pracownicy: Dict[str, Dict[str, Dict[str, Any]]] = {} # Klucz: str(guild_id), Wartość: dict pracowników dla tego serwera {user_id_str: data}
json_lock = asyncio.Lock()

# --- Funkcje Pomocnicze ---
async def zapisz_pracownikow():
    """Bezpiecznie zapisuje CAŁĄ strukturę danych (wszystkie serwery) do JSON."""
    async with json_lock:
        try:
            with open(JSON_FILE, 'w', encoding='utf-8') as f:
                json.dump(pracownicy, f, ensure_ascii=False, indent=4)
            # print(f"[DEBUG] Zapisano dane dla {len(pracownicy)} serwerów do {JSON_FILE}")
            return True
        except Exception as e:
            print(f"[ERROR] Błąd zapisywania {JSON_FILE}: {str(e)}")
            traceback.print_exc()
            return False

async def wczytaj_pracownikow():
    """Wczytuje CAŁĄ strukturę danych pracowników z JSON."""
    global pracownicy
    async with json_lock:
        try:
            if os.path.exists(JSON_FILE):
                with open(JSON_FILE, 'r', encoding='utf-8') as f:
                    pracownicy_temp = json.load(f)
                    # Walidacja struktury - oczekujemy dict[str, dict[str, dict]]
                    if isinstance(pracownicy_temp, dict):
                        pracownicy = pracownicy_temp
                        print(f"[INFO] Wczytano dane dla {len(pracownicy)} serwerów z {JSON_FILE}")
                    else:
                        print(f"[ERROR] Nieprawidłowa struktura danych w {JSON_FILE}. Oczekiwano słownika serwerów.")
                        pracownicy = {} # Resetuj do pustego, aby uniknąć błędów
                        # Można dodać backup tutaj jak poniżej
                        raise json.JSONDecodeError("Nieprawidłowy główny typ danych", "", 0)

            else:
                print(f"[INFO] Plik {JSON_FILE} nie istnieje. Tworzę pustą strukturę.")
                pracownicy = {}
            return True
        except json.JSONDecodeError as e:
            print(f"[ERROR] Błąd dekodowania JSON {JSON_FILE}: {str(e)}")
            print(f"[WARN] Tworzę backup uszkodzonego pliku.")
            try:
                backup_filename = f"{JSON_FILE}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                os.rename(JSON_FILE, backup_filename)
                print(f"[INFO] Utworzono backup: {backup_filename}")
            except OSError as os_err:
                print(f"[ERROR] Nie udało się utworzyć backupu: {os_err}")
            pracownicy = {} # Resetuj do pustego słownika po błędzie
            return False
        except Exception as e:
            print(f"[ERROR] Inny błąd wczytywania {JSON_FILE}: {str(e)}")
            traceback.print_exc()
            pracownicy = {} # Resetuj do pustego słownika po błędzie
            return False

def get_guild_data(guild_id: int) -> Dict[str, Dict[str, Any]]:
    """Pobiera (lub tworzy pusty) słownik danych dla konkretnego serwera."""
    guild_id_str = str(guild_id) # Używamy stringów jako kluczy w głównym dict
    if guild_id_str not in pracownicy:
        print(f"[INFO] Tworzenie struktury danych dla nowego serwera {guild_id_str}")
        pracownicy[guild_id_str] = {} # Tworzy pusty słownik dla użytkowników tego serwera
    # Zwraca słownik użytkowników dla danego serwera
    return pracownicy[guild_id_str]

def _ma_wymagane_uprawnienia(member: Optional[discord.Member]) -> bool:
    """Sprawdza czy użytkownik ma rolę zarządzającą LUB jest adminem serwera."""
    if not member or not isinstance(member, discord.Member):
        # print("[DEBUG Perm Check] Brak obiektu Member.")
        return False
    # 1. Sprawdź permisję administratora na serwerze
    if member.guild_permissions.administrator:
        # print(f"[DEBUG Perm Check] {member} jest adminem.")
        return True
    # 2. Sprawdź czy ma którąś z ról zarządzających
    # Zakładamy, że ROLE_ZARZADZAJACE są takie same na wszystkich serwerach (patrz KRYTYCZNE ZAŁOŻENIE na górze)
    user_role_ids = {role.id for role in member.roles}
    has_management_role = any(role_id in user_role_ids for role_id in ROLE_ZARZADZAJACE if role_id is not None)
    # if has_management_role: print(f"[DEBUG Perm Check] {member} ma rolę zarządzającą.")
    # else: print(f"[DEBUG Perm Check] {member} NIE MA uprawnień.")
    return has_management_role

def is_manager():
    """Dekorator @app_commands.check sprawdzający uprawnienia zarządzające LUB admina."""
    async def predicate(interaction: discord.Interaction) -> bool:
        if not interaction.guild: # Komenda musi być na serwerze
            # print("[DEBUG Perm Check] Użyto poza serwerem.")
            # Sprawdź, czy odpowiedź nie została już wysłana (np. przez on_tree_error)
            if not interaction.response.is_done():
                await interaction.response.send_message("Tej komendy można używać tylko na serwerze.", ephemeral=True)
            return False

        # Interaction.user jest typu User | Member. Potrzebujemy Member do sprawdzenia ról.
        user_to_check = interaction.user
        if not isinstance(user_to_check, discord.Member):
            # print(f"[DEBUG Perm Check] interaction.user jest typu User ({user_to_check.id}), pobieram Member...")
            user_to_check = interaction.guild.get_member(interaction.user.id) # Pobierz obiekt Member
            if not user_to_check: # Nie znaleziono członka (bardzo rzadkie, ale możliwe)
                print(f"[ERROR Perm Check] Nie można pobrać obiektu Member dla {interaction.user.id} na serwerze {interaction.guild_id}")
                allowed = False
            else:
                # print(f"[DEBUG Perm Check] Pobrany Member: {user_to_check}")
                allowed = _ma_wymagane_uprawnienia(user_to_check)
        else: # interaction.user jest już typu Member
            # print(f"[DEBUG Perm Check] interaction.user jest typu Member ({user_to_check})")
            allowed = _ma_wymagane_uprawnienia(user_to_check)

        # print(f"[DEBUG Perm Check] Wynik dla {interaction.user}: {allowed}")
        if not allowed and not interaction.response.is_done():
            # print("[DEBUG Perm Check] Wysyłam brak uprawnień.")
            await interaction.response.send_message("❌ Nie masz wymaganych uprawnień do użycia tej komendy!", ephemeral=True)
        # elif not allowed: # Już wysłano odpowiedź lub błąd gdzie indziej
            # print(f"[WARN Perm Check] Brak uprawnień dla {interaction.user}, ale odpowiedź już wysłana.")

        return allowed
    return app_commands.check(predicate)

# TUTAJ DODANO FUNKCJĘ check_if_owner
async def check_if_owner(interaction: discord.Interaction) -> bool:
    """Sprawdza, czy użytkownik, który wywołał interakcję, jest właścicielem bota."""
    # `bot.is_owner()` sprawdza ID użytkownika względem właściciela(i)
    # zdefiniowanych w ustawieniach aplikacji bota na Discord Developer Portal.
    if not await bot.is_owner(interaction.user):
        # Jeśli użytkownik NIE jest właścicielem, wyślij wiadomość i zwróć False
        # Używamy try-except na wypadek, gdyby interakcja już otrzymała odpowiedź
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ Ta komenda jest dostępna tylko dla właściciela bota!", ephemeral=True)
            else:
                # Jeśli 'defer' lub inna odpowiedź już poszła, użyj followup
                await interaction.followup.send("❌ Ta komenda jest dostępna tylko dla właściciela bota!", ephemeral=True)
        except discord.errors.NotFound: # Interaction might expire
            print(f"[WARN CheckOwner] Interakcja wygasła przed wysłaniem wiadomości o braku uprawnień dla {interaction.user}.")
        except Exception as e:
            print(f"[ERROR CheckOwner] Nie można było wysłać wiadomości o braku uprawnień właściciela: {e}")
        return False # Sprawdzenie nie powiodło się
    return True # Sprawdzenie powiodło się, użytkownik jest właścicielem

def czy_jest_zatrudniony(guild_id: int, member: discord.Member) -> bool:
    """Sprawdza czy użytkownik jest w bazie DANEGO SERWERA LUB ma jakąkolwiek rolę pracowniczą/zarządzającą."""
    if not member or not isinstance(member, discord.Member): return False

    # 1. Sprawdź w bazie danych JSON dla tego serwera
    guild_data = get_guild_data(guild_id) # Pobierz dane dla TEGO serwera
    if str(member.id) in guild_data:
        # print(f"[DEBUG Hired Check] {member} znaleziony w JSON dla {guild_id}")
        return True

    # 2. Sprawdź czy ma jakąkolwiek rolę z listy WSZYSTKIE_PRACA (zarządzające + podstawowe)
    user_role_ids = {role.id for role in member.roles}
    # Zakładamy, że ROLE_WSZYSTKIE_PRACA są takie same na wszystkich serwerach (patrz KRYTYCZNE ZAŁOŻENIE)
    if any(role_id in user_role_ids for role_id in ROLE_WSZYSTKIE_PRACA):
        # print(f"[DEBUG Hired Check] {member} ma rolę pracowniczą/zarządzającą na {guild_id}")
        return True

    # print(f"[DEBUG Hired Check] {member} nie jest zatrudniony na {guild_id}")
    return False


# Poprawiona funkcja logowania, świadoma serwera
async def log_to_channel(interaction: Optional[discord.Interaction] = None, bot_instance: Optional[commands.Bot] = None, guild_id: Optional[int] = None, log_type: str = "hr", message: str = None, embed: discord.Embed = None):
    """Wysyła log na kanał specyficzny dla danego serwera."""
    # Potrzebujemy albo interaction, albo bota I guild_id
    if not interaction and not (bot_instance and guild_id):
        print("[ERROR LOG] Brak wystarczających danych do logowania (interaction lub bot+guild_id).")
        return

    current_guild_id = interaction.guild_id if interaction else guild_id
    current_guild = interaction.guild if interaction else bot_instance.get_guild(current_guild_id) if bot_instance else None

    if not current_guild:
        print(f"[ERROR LOG] Nie znaleziono serwera o ID {current_guild_id}.")
        return

    channel_id = LOG_CHANNEL_IDS.get(log_type)
    if not channel_id:
        # print(f"[WARN LOG] Brak skonfigurowanego kanału logów typu '{log_type}'.")
        return # Nie logujemy, jeśli typ nie jest zdefiniowany

    channel = current_guild.get_channel(channel_id) # Szukamy kanału na TYM serwerze
    if not isinstance(channel, discord.TextChannel):
        print(f"[ERROR LOG] Kanał logów (ID: {channel_id}) nie jest tekstowy lub nie istnieje na serwerze {current_guild.name} ({current_guild_id}).")
        return

    try:
        await channel.send(content=message, embed=embed)
    except discord.Forbidden:
        print(f"[ERROR LOG] Brak uprawnień Discord do pisania na kanale {channel.name} ({channel_id}) na serwerze {current_guild.name}.")
    except Exception as e:
        print(f"[ERROR LOG] Nieznany błąd wysyłania logu na {channel.name} ({channel_id}) na serwerze {current_guild.name}: {e}")
        traceback.print_exc()


# --- Funkcja Punktów (Wersja z Rolami Poziomowymi) ---
async def _dodaj_punkt_z_rolami(interaction: discord.Interaction, member: discord.Member, typ: str, powod: Optional[str] = None) -> bool:
    """Zarządza punktami i rolami poziomowymi 1/3, 2/3, 3/3 dla danego serwera."""
    try:
        if not interaction.guild or not interaction.guild_id:
            if not interaction.response.is_done(): await interaction.response.send_message("Błąd: Ta komenda musi być użyta na serwerze.", ephemeral=True)
            return False

        guild = interaction.guild
        guild_id = interaction.guild_id
        member_id_str = str(member.id)
        log_prefix = f"[DEBUG RolePoints][G:{guild_id}][T:{typ}][U:{member.name}]"
        print(f"{log_prefix} Start.")

        # Defer response
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=False) # Odpowiedź będzie widoczna dla innych

        # Sprawdź, czy pracownik jest zatrudniony na TYM serwerze
        if not czy_jest_zatrudniony(guild_id, member):
            await interaction.followup.send(f"❌ {member.mention} nie jest rozpoznany jako zatrudniony na tym serwerze. Użyj /zatrudnij lub nadaj rolę, jeśli potrzebne.", ephemeral=True)
            return False

        # Pobierz dane serwera i upewnij się, że pracownik istnieje w JSON
        guild_data = get_guild_data(guild_id)
        pracownik_data = guild_data.get(member_id_str)
        if not pracownik_data:
             # Mógł mieć rolę, ale nie być w JSON - dodajmy podstawowy wpis
             print(f"{log_prefix} Użytkownik nie był w JSON, tworzenie wpisu.")
             now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
             pracownik_data = {"nazwa": str(member), "data_zatrudnienia": now, "rola": "Nieznana (brak w JSON)", "plusy": 0, "minusy": 0, "upomnienia": 0, "ostrzezenia": [], "historia_awansow": []}
             guild_data[member_id_str] = pracownik_data
             # Nie zapisujemy jeszcze, zrobimy to po aktualizacji punktów


        # --- Walidacja Ról Poziomowych ---
        level_role_ids_map = POINT_ROLE_LEVELS_MAP.get(typ)
        if not level_role_ids_map:
            print(f"{log_prefix} BŁĄD WEWNĘTRZNY: Nieznany typ punktu: {typ}")
            await interaction.followup.send("❌ Błąd wewnętrzny serwera (nieznany typ punktu).", ephemeral=True)
            return False

        roles_objects: Dict[int, Optional[discord.Role]] = {}
        missing_roles_info: List[str] = []
        hierarchy_ok = True
        bot_member = guild.me # Obiekt bota na tym serwerze
        if not bot_member: # Bot nie jest na serwerze? Coś bardzo źle.
             await interaction.followup.send("❌ Krytyczny błąd: Nie znaleziono bota na tym serwerze.", ephemeral=True); return False
        bot_top_role_pos = bot_member.top_role.position if bot_member.top_role else 0

        # Sprawdź uprawnienia bota
        if not bot_member.guild_permissions.manage_roles:
            print(f"{log_prefix} BŁĄD: Bot nie ma uprawnień 'Zarządzanie Rolami' na serwerze {guild.name}.")
            await interaction.followup.send("❌ Błąd: Bot nie ma uprawnień do zarządzania rolami na tym serwerze!", ephemeral=True)
            return False

        # Sprawdź istnienie i hierarchię ról punktowych
        for level, role_id in level_role_ids_map.items():
            role = guild.get_role(role_id)
            roles_objects[level] = role
            if role is None:
                print(f"{log_prefix} BŁĄD KRYTYCZNY: Rola dla Poziomu {level} (ID: {role_id}) NIE ZNALEZIONA na serwerze {guild.name}!")
                missing_roles_info.append(f"Poziom {level} (ID: {role_id})")
            else:
                # print(f"{log_prefix} Rola Poziom {level}: '{role.name}' (Poz: {role.position})")
                if role.position >= bot_top_role_pos:
                    print(f"{log_prefix} BŁĄD HIERARCHII: Rola '{role.name}' (Poz: {role.position}) jest na równi lub wyżej niż rola bota '{bot_member.top_role.name}' (Poz: {bot_top_role_pos}) na serwerze {guild.name}!")
                    hierarchy_ok = False

        if missing_roles_info:
            await interaction.followup.send(f"❌ Błąd Konfiguracji Ról na tym serwerze! Brakujące role dla '{typ}': {', '.join(missing_roles_info)}. Skontaktuj się z administratorem.", ephemeral=True)
            return False
        if not hierarchy_ok:
            await interaction.followup.send(f"❌ Błąd Hierarchii Ról na tym serwerze! Rola bota ({bot_member.top_role.name}) musi być wyżej niż wszystkie role punktowe ({typ}). Skontaktuj się z administratorem.", ephemeral=True)
            return False
        print(f"{log_prefix} Walidacja ról i hierarchii OK.")
        # --- Koniec Walidacji Ról ---

        # --- Logika Poziomów ---
        current_level = 0
        current_role_obj = None
        user_role_ids = {r.id for r in member.roles}

        # Sprawdź od najwyższego poziomu w dół, która rola jest aktualnie przypisana
        for level in sorted(roles_objects.keys(), reverse=True): # Sortuj [3, 2, 1]
            role_obj = roles_objects.get(level)
            if role_obj and role_obj.id in user_role_ids:
                current_level = level
                current_role_obj = role_obj
                break # Znaleziono najwyższą posiadaną rolę dla tego typu
        print(f"{log_prefix} Aktualny poziom użytkownika: {current_level}")

        new_level = current_level + 1
        osiagnieto_limit = new_level > 3 # Czy przekroczono maksymalny poziom (3)?

        role_to_remove = current_role_obj # Rola do usunięcia (jeśli była)
        role_to_add = roles_objects.get(new_level) if not osiagnieto_limit else None # Rola do dodania (jeśli nie osiągnięto limitu)

        # Jeśli osiągnięto limit, licznik w bazie resetujemy do 0
        final_level_in_db = 0 if osiagnieto_limit else new_level
        print(f"{log_prefix} Nowy poziom: {new_level}, Osiągnięto Limit?: {osiagnieto_limit}, Usuń: {role_to_remove}, Dodaj: {role_to_add}, Poziom w DB: {final_level_in_db}")
        # --- Koniec Logiki Poziomów ---

        # --- Zarządzanie Rolami Discord ---
        role_action_success = True
        reason = f"{typ.capitalize()} ({new_level if not osiagnieto_limit else 'LIMIT/RESET'}) przez {interaction.user} (ID: {interaction.user.id})" + (f" Powód: {powod}" if powod else "")

        try:
            current_user_roles_set = {r.id for r in member.roles} # Odśwież role użytkownika przed operacjami

            # Usuń starą rolę, jeśli istnieje i użytkownik ją ma
            if role_to_remove and role_to_remove.id in current_user_roles_set:
                print(f"{log_prefix} Usuwanie roli {role_to_remove.name}...")
                await member.remove_roles(role_to_remove, reason=reason)
                print(f"{log_prefix} Usunięto.")

            # Dodaj nową rolę, jeśli istnieje (nie osiągnięto limitu) i użytkownik jej nie ma
            if role_to_add and role_to_add.id not in current_user_roles_set:
                print(f"{log_prefix} Dodawanie roli {role_to_add.name}...")
                await member.add_roles(role_to_add, reason=reason)
                print(f"{log_prefix} Dodano.")

        except discord.Forbidden as e:
            print(f"[ERROR Forbidden] {log_prefix} Błąd uprawnień Discord przy zarządzaniu rolami: {e}")
            await interaction.followup.send(f"❌ Błąd Uprawnień Discord! Bot nie mógł zarządzać rolami dla {member.mention}. Sprawdź uprawnienia bota i hierarchię ról.", ephemeral=True)
            role_action_success = False
            return False # Zwracamy False, bo operacja się nie powiodła
        except discord.HTTPException as e:
            print(f"[ERROR HTTP] {log_prefix} Błąd sieci Discord przy zarządzaniu rolami: {e}")
            await interaction.followup.send(f"❌ Błąd Sieci Discord ({e.status})! Spróbuj ponownie za chwilę.", ephemeral=True)
            role_action_success = False
            return False
        except Exception as e:
            print(f"[ERROR Generyczny] {log_prefix} Niespodziewany błąd przy zarządzaniu rolami:")
            traceback.print_exc()
            await interaction.followup.send("❌ Wystąpił niespodziewany błąd serwera przy zarządzaniu rolami!", ephemeral=True)
            role_action_success = False
            return False
        # --- Koniec Zarządzania Rolami ---

        # --- Aktualizacja Danych w JSON i Odpowiedź ---
        if role_action_success:
            # Aktualizuj dane w słowniku dla TEGO serwera i TEGO użytkownika
            guild_data = get_guild_data(guild_id) # Pobierz najnowsze dane serwera
            # Upewnij się, że klucz użytkownika istnieje (choć powinien po sprawdzeniu na początku)
            if member_id_str not in guild_data:
                 print(f"{log_prefix} KRYTYCZNY BŁĄD: Klucz użytkownika zniknął z danych serwera?")
                 # Stwórzmy go ponownie
                 now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                 guild_data[member_id_str] = {"nazwa": str(member), "data_zatrudnienia": now, "rola": "Nieznana (brak w JSON)", "plusy": 0, "minusy": 0, "upomnienia": 0, "ostrzezenia": [], "historia_awansow": []}

            pracownik_data = guild_data[member_id_str] # Teraz mamy pewność, że istnieje
            pracownik_data[typ] = final_level_in_db # Zaktualizuj licznik punktów dla danego typu
            pracownik_data["nazwa"] = str(member) # Zaktualizuj nazwę na wszelki wypadek
            print(f"{log_prefix} Zapisuję poziom {final_level_in_db} w JSON dla typu '{typ}'.")

            # Zapisz CAŁĄ strukturę do pliku
            if not await zapisz_pracownikow():
                # Jeśli zapis się nie udał, to duży problem, ale rola już została zmieniona. Poinformuj użytkownika.
                await interaction.followup.send("⚠️ **Krytyczny Błąd Zapisu Danych!** Zmiana roli została zastosowana, ale nie udało się zapisać punktów w bazie. Skontaktuj się z administratorem!", ephemeral=False) # Widoczne dla wszystkich
            else:
                # Zapis udany, przygotuj finalną wiadomość
                emoji_map = {"plusy": "⭐", "minusy": "❌", "upomnienia": "⚠️"}
                emoji = emoji_map.get(typ, "")
                final_message = ""
                role_change_info = ""
                if role_to_remove: role_change_info += f"Usunięto: {role_to_remove.mention}. "
                if role_to_add: role_change_info += f"Nadano: {role_to_add.mention}."

                if osiagnieto_limit:
                    final_message = f"{emoji} {member.mention} otrzymał(a) punkt ({typ.capitalize()} {new_level}/3)."
                    if powod: final_message += f"\nPowód: {powod}"
                    final_message += f"\n**Osiągnięto limit 3! Licznik '{typ}' został zresetowany.**"
                    if role_to_remove: final_message += f"\n*{role_change_info.strip()}*" # Pokaż tylko usuniętą rolę
                else:
                    final_message = f"{emoji} {member.mention} otrzymał(a) punkt ({typ.capitalize()} {new_level}/3)."
                    if powod: final_message += f"\nPowód: {powod}"
                    if role_change_info: final_message += f"\n*{role_change_info.strip()}*" # Pokaż zmiany ról

                await interaction.followup.send(final_message, ephemeral=False) # Widoczne dla wszystkich

                # Logowanie do kanału
                log_msg_base = f"`{datetime.now().strftime('%H:%M')}` {interaction.user.mention} -> {member.mention}"
                log_msg_details = f"({typ.capitalize()} {new_level if not osiagnieto_limit else 'LIMIT/RESET'})"
                log_msg_reason = f" Powód: {powod or '-'}"
                log_msg_roles = f" Rola: {'Brak zmian' if not role_change_info else role_change_info.strip()}"
                await log_to_channel(interaction=interaction, log_type="punkty", message=f"{emoji} {log_msg_base} {log_msg_details}.{log_msg_reason}.{log_msg_roles}")

            return osiagnieto_limit # Zwróć True jeśli osiągnięto limit (może być przydatne)

        else: # role_action_success == False
            print(f"{log_prefix} Akcja zmiany ról nie powiodła się, nie zapisano zmian w JSON.")
            # Odpowiedź do użytkownika została już wysłana w bloku except zarządzania rolami
            return False # Zwracamy False, bo operacja się nie powiodła

    except Exception as e:
        print(f"[ERROR KRYTYCZNY] {log_prefix} Niespodziewany błąd w głównej funkcji _dodaj_punkt_z_rolami:")
        traceback.print_exc()
        # Spróbuj wysłać wiadomość o błędzie, jeśli jeszcze można
        error_message = f"Wystąpił nieoczekiwany krytyczny błąd serwera przy obsłudze punktów: {e}"
        try:
            if interaction.response.is_done():
                await interaction.followup.send(error_message, ephemeral=True)
            else:
                # Jeśli defer się nie wykonał, a response jest możliwy
                await interaction.response.send_message(error_message, ephemeral=True)
        except Exception as e2:
            print(f"[ERROR Handler] Nie można było wysłać wiadomości o błędzie krytycznym: {e2}")
        return False # Zwracamy False, bo operacja się nie powiodła


# --- Funkcja zmiany stanowiska ---
async def _zmien_stanowisko(interaction: discord.Interaction, member: discord.Member, sciezka_key: str, poziom: int, powod: Optional[str], czy_awans: bool):
    """Wewnętrzna funkcja do awansu/degradacji na podstawie ścieżki i poziomu."""
    try:
        if not interaction.guild or not interaction.guild_id:
            if not interaction.response.is_done(): await interaction.response.send_message("Błąd: Ta komenda musi być użyta na serwerze.", ephemeral=True)
            return False

        guild = interaction.guild
        guild_id = interaction.guild_id
        member_id_str = str(member.id)
        log_prefix = f"[DEBUG ChangePos][G:{guild_id}][P:{sciezka_key}][L:{poziom}][U:{member.name}]"
        typ_operacji_log = "AWANS" if czy_awans else "DEGRADACJA"
        print(f"{log_prefix} Start {typ_operacji_log}.")

        # Defer response (zrobione w komendzie wywołującej)

        # Sprawdź, czy pracownik jest zatrudniony i w JSON
        if not czy_jest_zatrudniony(guild_id, member):
            await interaction.followup.send(f"❌ {member.mention} nie jest rozpoznany jako zatrudniony na tym serwerze.", ephemeral=True)
            return False
        guild_data = get_guild_data(guild_id)
        if member_id_str not in guild_data:
             await interaction.followup.send(f"❌ {member.mention} nie jest zarejestrowany w systemie tego serwera (brak wpisu JSON). Użyj /zatrudnij.", ephemeral=True)
             return False

        # --- Walidacja Ścieżki i Poziomu ---
        sciezka_awansu_ids = SCIEZKI_MAP.get(sciezka_key)
        # Znajdź ładną nazwę ścieżki
        nazwa_sciezki = sciezka_key # Domyślnie
        for choice in SCIEZKI_WYBORY:
            if choice.value == sciezka_key:
                nazwa_sciezki = choice.name
                break

        if not sciezka_awansu_ids:
            print(f"{log_prefix} BŁĄD: Nieznana ścieżka: {sciezka_key}")
            await interaction.followup.send(f"❌ Błąd wewnętrzny: Nieznana ścieżka '{sciezka_key}'.", ephemeral=True)
            return False

        # Sprawdź, czy użytkownik ma wymaganą rolę bazową (Pracownik lub Ochrona dla ścieżki ochrony)
        # Zakładamy, że Role.PRACOWNIK i Role.OCHRONA mają te same ID na wszystkich serwerach
        rola_bazowa_wymagana_id = Role.OCHRONA if sciezka_key == "ochrona" else Role.PRACOWNIK # Poprawione: sprawdzamy klucz, nie ścieżkę zarządu
        rola_bazowa_wymagana = guild.get_role(rola_bazowa_wymagana_id)
        if not rola_bazowa_wymagana:
             await interaction.followup.send(f"❌ Błąd Konfiguracji: Brak roli bazowej '{'Ochrona' if sciezka_key == 'ochrona' else 'Pracownik'}' (ID: {rola_bazowa_wymagana_id}) na tym serwerze!", ephemeral=True)
             return False
        if rola_bazowa_wymagana not in member.roles:
             await interaction.followup.send(f"❌ Użytkownik {member.mention} nie posiada wymaganej roli bazowej '{rola_bazowa_wymagana.name}' do tej ścieżki.", ephemeral=True)
             return False

        # Znajdź aktualną rolę użytkownika na DANEJ ścieżce
        aktualna_rola: Optional[discord.Role] = None
        aktualny_poziom_idx: int = -1 # Index w liście sciezka_awansu_ids
        user_role_ids = {r.id for r in member.roles}

        # Iteruj po ID ról w ścieżce, aby znaleźć najwyższą posiadaną przez użytkownika
        for i, rola_id in enumerate(sciezka_awansu_ids):
             if rola_id in user_role_ids:
                 # Znaleziono rolę ze ścieżki, sprawdźmy czy jest najwyższa do tej pory
                 if i > aktualny_poziom_idx:
                     temp_rola = guild.get_role(rola_id)
                     if temp_rola: # Upewnijmy się, że rola istnieje na serwerze
                         aktualna_rola = temp_rola
                         aktualny_poziom_idx = i
                     else: # To nie powinno się zdarzyć jeśli role istnieją, ale na wszelki wypadek
                         print(f"{log_prefix} OSTRZEŻENIE: Użytkownik ma ID roli {rola_id} ze ścieżki, ale rola nie istnieje na serwerze?")

        aktualny_poziom_num = aktualny_poziom_idx + 1 # Poziom "ludzki" (1-based)
        docelowy_poziom_idx = poziom - 1 # Index docelowy (0-based)
        max_poziom_idx = len(sciezka_awansu_ids) - 1

        print(f"{log_prefix} Aktualna Rola: {aktualna_rola.name if aktualna_rola else 'Brak'}, Poziom Idx: {aktualny_poziom_idx}, Poziom Num: {aktualny_poziom_num}")
        print(f"{log_prefix} Docelowy Poziom Idx: {docelowy_poziom_idx}, Max Idx: {max_poziom_idx}")

        # Walidacja logiki awansu/degradacji
        if docelowy_poziom_idx < 0 or docelowy_poziom_idx > max_poziom_idx:
            await interaction.followup.send(f"❌ Nieprawidłowy numer poziomu docelowego ({poziom}). Dostępne: 1-{max_poziom_idx + 1}.", ephemeral=True)
            return False

        if czy_awans: # Logika dla awansu
            if aktualny_poziom_idx == -1 and docelowy_poziom_idx != 0: # Jeśli nie ma roli ze ścieżki, można awansować tylko na poziom 1 (index 0)
                await interaction.followup.send(f"❌ Użytkownik nie ma roli z tej ścieżki. Można awansować tylko na Poziom 1.", ephemeral=True)
                return False
            if aktualny_poziom_idx != -1 and docelowy_poziom_idx <= aktualny_poziom_idx: # Jeśli ma rolę, można awansować tylko na wyższy poziom
                 await interaction.followup.send(f"❌ Nie można awansować na ten sam lub niższy poziom (Aktualny: {aktualny_poziom_num}, Docelowy: {poziom}).", ephemeral=True)
                 return False
            # Dodatkowa walidacja - czy awansujemy o więcej niż 1 poziom? Można dodać ostrzeżenie.
            if aktualny_poziom_idx != -1 and docelowy_poziom_idx > aktualny_poziom_idx + 1:
                 print(f"{log_prefix} OSTRZEŻENIE: Awans o więcej niż 1 poziom ({aktualny_poziom_num} -> {poziom}).")
                 # Można dodać confirmation tutaj, ale na razie pozwalamy.

        else: # Logika dla degradacji
            if aktualny_poziom_idx == -1: # Nie można degradować kogoś bez roli ze ścieżki
                await interaction.followup.send(f"❌ Użytkownik nie posiada żadnej roli z wybranej ścieżki do zdegradowania.", ephemeral=True)
                return False
            if docelowy_poziom_idx >= aktualny_poziom_idx: # Nie można degradować na ten sam lub wyższy poziom
                await interaction.followup.send(f"❌ Nie można degradować na ten sam lub wyższy poziom (Aktualny: {aktualny_poziom_num}, Docelowy: {poziom}).", ephemeral=True)
                return False

        # Pobierz obiekt nowej roli
        nowa_rola_id = sciezka_awansu_ids[docelowy_poziom_idx]
        nowa_rola = guild.get_role(nowa_rola_id)
        if not nowa_rola:
            await interaction.followup.send(f"❌ Błąd Konfiguracji: Nie znaleziono roli dla poziomu {poziom} (ID: {nowa_rola_id}) na tym serwerze!", ephemeral=True)
            return False

        # Sprawdź hierarchię bota względem nowej i starej roli
        bot_member = guild.me
        if not bot_member: await interaction.followup.send("❌ Błąd: Nie można pobrać bota.", ephemeral=True); return False
        bot_top_role_pos = bot_member.top_role.position if bot_member.top_role else 0

        if nowa_rola.position >= bot_top_role_pos:
             await interaction.followup.send(f"❌ Błąd Hierarchii: Rola docelowa '{nowa_rola.name}' jest na równi lub wyżej niż rola bota '{bot_member.top_role.name}'!", ephemeral=True)
             return False
        if aktualna_rola and aktualna_rola.position >= bot_top_role_pos:
             await interaction.followup.send(f"❌ Błąd Hierarchii: Aktualna rola użytkownika '{aktualna_rola.name}' jest na równi lub wyżej niż rola bota '{bot_member.top_role.name}'!", ephemeral=True)
             return False

        print(f"{log_prefix} Walidacja ścieżki, poziomu i hierarchii OK.")
        # --- Koniec Walidacji ---

        # --- Zarządzanie Rolami Discord ---
        roles_to_remove: List[discord.Role] = []
        roles_to_add: List[discord.Role] = []
        reason = f"{'Awans' if czy_awans else 'Degradacja'} na {nowa_rola.name} ({nazwa_sciezki}) przez {interaction.user} (ID: {interaction.user.id})" + (f" Powód: {powod}" if powod and not czy_awans else "")

        # Role do usunięcia:
        # Przy awansie: usuń WSZYSTKIE role ze ścieżki, które użytkownik aktualnie ma, a które są PONIŻEJ nowej roli (lub wszystkie jeśli zaczynał bez roli)
        # Przy degradacji: usuń tylko AKTUALNĄ rolę (jeśli ją miał)
        if czy_awans:
            for i, rid in enumerate(sciezka_awansu_ids):
                 if i < docelowy_poziom_idx and rid in user_role_ids: # Sprawdź role poniżej docelowej
                     r = guild.get_role(rid)
                     if r and r.position < bot_top_role_pos: # Upewnij się, że możemy nią zarządzać
                         roles_to_remove.append(r)
            # Usuń też starą rolę, jeśli istniała i jest inna niż role poniżej (na wypadek skoku o >1 poziom)
            if aktualna_rola and aktualna_rola not in roles_to_remove and aktualna_rola.id != nowa_rola_id:
                roles_to_remove.append(aktualna_rola)
        elif aktualna_rola: # Degradacja - usuwamy tylko aktualną
            roles_to_remove.append(aktualna_rola)

        # Rola do dodania:
        if nowa_rola.id not in user_role_ids:
            roles_to_add.append(nowa_rola)

        print(f"{log_prefix} Role do usunięcia: {[r.name for r in roles_to_remove]}")
        print(f"{log_prefix} Role do dodania: {[r.name for r in roles_to_add]}")

        try:
            if roles_to_remove:
                await member.remove_roles(*roles_to_remove, reason=reason)
                print(f"{log_prefix} Usunięto role: {[r.name for r in roles_to_remove]}")
            if roles_to_add:
                await member.add_roles(*roles_to_add, reason=reason)
                print(f"{log_prefix} Dodano role: {[r.name for r in roles_to_add]}")

            # --- Aktualizacja Danych w JSON ---
            pracownik_data = guild_data[member_id_str] # Pobierz ponownie dane
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            pracownik_data["rola"] = nowa_rola.name # Ustaw aktualną rolę w JSON
            pracownik_data["nazwa"] = str(member) # Upewnij się, że nazwa jest aktualna

            # Dodaj wpis do historii awansów/degradacji
            historia_entry = {
                "data": now_str,
                "rola": nowa_rola.name,
                "sciezka": nazwa_sciezki,
                "poziom": poziom,
                "operator": str(interaction.user),
                "typ": "awans" if czy_awans else "degradacja"
            }
            if not czy_awans and powod: # Dodaj powód tylko przy degradacji
                historia_entry["powod"] = powod
            # Dodaj wpis do listy, tworząc ją jeśli nie istnieje
            pracownik_data.setdefault("historia_awansow", []).append(historia_entry)

            print(f"{log_prefix} Aktualizacja JSON zakończona.")

            # Zapisz CAŁĄ strukturę
            if not await zapisz_pracownikow():
                 await interaction.followup.send("⚠️ **Krytyczny Błąd Zapisu Danych!** Zmiana roli została zastosowana, ale nie udało się zapisać zmian w bazie. Skontaktuj się z administratorem!", ephemeral=False)
                 # Kontynuuj, aby poinformować o zmianie roli
            else:
                 print(f"{log_prefix} Zapisano dane do JSON.")

            # --- Finalna Odpowiedź i Logowanie ---
            emoji = "✅" if czy_awans else "⬇️"
            operation_verb = "awansowano" if czy_awans else "zdegradowano"
            final_msg = f"{emoji} Pomyślnie {operation_verb} {member.mention}!\n"
            final_msg += f"**Ścieżka:** {nazwa_sciezki}\n"
            final_msg += f"**Nowa Rola:** {nowa_rola.mention} ({nowa_rola.name})\n"
            final_msg += f"**Poziom:** {poziom} / {len(sciezka_awansu_ids)}"
            if not czy_awans and powod:
                final_msg += f"\n**Powód:** {powod}"

            await interaction.followup.send(final_msg)

            # Logowanie
            log_msg_base = f"`{datetime.now().strftime('%H:%M')}` {interaction.user.mention} {operation_verb} {member.mention}"
            log_msg_details = f"na {nowa_rola.name} ({nazwa_sciezki} Poz. {poziom})"
            log_msg_reason = f" Powód: {powod or '-'}" if not czy_awans else ""
            await log_to_channel(interaction=interaction, log_type="awanse", message=f"{emoji} {log_msg_base} {log_msg_details}.{log_msg_reason}")

            return True # Operacja zakończona sukcesem

        except discord.Forbidden as e:
            print(f"[ERROR Forbidden] {log_prefix} Błąd uprawnień Discord przy zarządzaniu rolami: {e}")
            await interaction.followup.send(f"❌ Błąd Uprawnień Discord! Bot nie mógł zarządzać rolami dla {member.mention}. Sprawdź uprawnienia bota i hierarchię ról.", ephemeral=True)
            return False
        except discord.HTTPException as e:
            print(f"[ERROR HTTP] {log_prefix} Błąd sieci Discord przy zarządzaniu rolami: {e}")
            await interaction.followup.send(f"❌ Błąd Sieci Discord ({e.status})! Spróbuj ponownie za chwilę.", ephemeral=True)
            return False
        except Exception as e:
            print(f"[ERROR Generyczny] {log_prefix} Niespodziewany błąd przy zarządzaniu rolami lub aktualizacji JSON:")
            traceback.print_exc()
            await interaction.followup.send(f"❌ Wystąpił niespodziewany błąd serwera: {e}", ephemeral=True)
            return False

    except Exception as e: # Ogólny handler błędów dla całej funkcji
        print(f"[ERROR KRYTYCZNY] {log_prefix} Niespodziewany błąd w głównej funkcji _zmien_stanowisko:")
        traceback.print_exc()
        error_message = f"Wystąpił nieoczekiwany krytyczny błąd serwera przy zmianie stanowiska: {e}"
        try:
             if not interaction.response.is_done(): await interaction.response.send_message(error_message, ephemeral=True)
             else: await interaction.followup.send(error_message, ephemeral=True)
        except Exception as e2: print(f"[ERROR Handler] Nie można wysłać wiadomości o błędzie krytycznym: {e2}")
        return False


# --- Konfiguracja Bota ---
# Ustawienie intencji - co bot może "widzieć"
intents = discord.Intents.default()
intents.message_content = False # Nie potrzebujemy dostępu do treści wiadomości
intents.members = True       # Potrzebne do śledzenia członków (role, dołączanie itp.) - WYMAGA WŁĄCZENIA W DEVELOPER PORTAL
intents.guilds = True        # Potrzebne do informacji o serwerach

# --- Klasa Bota i Eventy ---
class CustomBot(commands.Bot):
    def __init__(self):
        # Inicjalizujemy bota z wymaganym prefixem (nawet jeśli go nie używamy) i intencjami
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        """Wywoływane asynchronicznie przy starcie bota, przed on_ready."""
        print("--- Rozpoczynam setup_hook ---")
        # 1. Wczytaj dane pracowników z pliku JSON
        print("Wczytywanie danych pracowników...")
        if await wczytaj_pracownikow():
            print("Wczytywanie danych zakończone.")
        else:
            print("Wystąpiły błędy podczas wczytywania danych. Bot startuje z pustą bazą (lub backupem).")

        # 2. Synchronizuj komendy slash dla KAŻDEGO serwera z listy konfiguracyjnej
        print(f"Synchronizowanie komend dla serwerów: {GUILD_IDS_LIST}...")
        synced_guilds = 0
        failed_guilds = []
        for guild_obj in GUILD_OBJS:
            try:
                # Kopiuje globalne komendy do drzewa komend danego serwera i synchronizuje
                # self.tree.copy_global_to(guild=guild_obj) # Opcjonalne, jeśli masz globalne komendy
                await self.tree.sync(guild=guild_obj)
                print(f" -> Komendy zsynchronizowane dla serwera ID: {guild_obj.id}")
                synced_guilds += 1
            except discord.errors.Forbidden as e:
                # NAJCZĘSTSZY BŁĄD: Bot nie ma uprawnień `application.commands` na tym serwerze
                # Trzeba go ponownie zaprosić z odpowiednimi uprawnieniami LUB nadać mu je ręcznie.
                print(f"[BŁĄD KRYTYCZNY] Brak uprawnień do synchronizacji komend na serwerze ID: {guild_obj.id}!")
                print(f"  -> Wiadomość: {e}")
                print(f"  -> Upewnij się, że bot został zaproszony z zakresem 'application.commands' lub ma odpowiednie uprawnienia na serwerze.")
                failed_guilds.append(str(guild_obj.id))
            except Exception as e:
                # Inne możliwe błędy (np. sieć, API Discord)
                print(f"[BŁĄD] Nieoczekiwany błąd synchronizacji dla serwera ID: {guild_obj.id}: {str(e)}")
                traceback.print_exc()
                failed_guilds.append(str(guild_obj.id))

        print(f"Synchronizacja zakończona. Zsynchronizowano: {synced_guilds}/{len(GUILD_OBJS)}.")
        if failed_guilds:
            print(f"Błędy synchronizacji na serwerach: {', '.join(failed_guilds)}")
        print("--- Setup_hook zakończony ---")

    async def on_ready(self):
        """Wywoływane, gdy bot pomyślnie połączy się z Discordem."""
        print(f'=============================================')
        print(f' Bot zalogowany jako: {self.user.name} (ID: {self.user.id})')
        print(f' Wersja discord.py: {discord.__version__}')
        print(f'=============================================')
        print(' Bot jest obecny na następujących serwerach:')
        guild_count = 0
        for guild in self.guilds:
             # Sprawdź, czy serwer jest na liście obsługiwanych
             is_configured = guild.id in GUILD_IDS_LIST
             marker = "[*]" if is_configured else "[ ]" # Oznacz obsługiwane
             print(f' {marker} {guild.name} (ID: {guild.id})')
             guild_count += 1
             # Dodatkowe info o bocie na tym serwerze (opcjonalne)
             try:
                 bot_member = guild.me
                 if bot_member:
                     print(f"     - Rola bota: {bot_member.top_role.name if bot_member.top_role else 'Brak'} (Poz: {bot_member.top_role.position if bot_member.top_role else 'N/A'})")
                     print(f"     - Ma 'Zarządzanie Rolami': {bot_member.guild_permissions.manage_roles}")
                 else: print("     - Nie można pobrać informacji o bocie na tym serwerze.")
             except Exception as e: print(f"     - Błąd przy pobieraniu info o bocie: {e}")

        print(f'---------------------------------------------')
        print(f' Łączna liczba serwerów: {guild_count}')
        print(f' Skonfigurowane serwery: {len(GUILD_IDS_LIST)}')
        print(f'=============================================')
        print(' Bot jest gotowy do przyjmowania komend!')
        # Ustawienie statusu bota (opcjonalne)
        await self.change_presence(activity=discord.Game(name="/pomoc - Zarządzanie HR"))

    # Globalny handler błędów dla komend slash (tree commands)
    async def on_tree_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Obsługuje błędy возникающие podczas wykonywania komend slash."""
        original_error = getattr(error, 'original', error) # Spróbuj uzyskać oryginalny błąd
        error_msg = f"Wystąpił nieoczekiwany błąd: {original_error}" # Domyślna wiadomość
        ephemeral_error = True # Domyślnie błędy są widoczne tylko dla użytkownika

        # Rozpoznawanie specyficznych typów błędów
        if isinstance(error, app_commands.CommandOnCooldown):
            error_msg = f"⏳ Zwolnij trochę! Możesz użyć tej komendy ponownie za {error.retry_after:.1f}s."
        elif isinstance(error, app_commands.MissingPermissions):
            error_msg = f"❌ Nie masz wymaganych uprawnień Discord: `{', '.join(error.missing_permissions)}`."
        elif isinstance(error, app_commands.BotMissingPermissions):
            error_msg = f"❌ Bot nie ma wymaganych uprawnień Discord: `{', '.join(error.missing_permissions)}`. Poproś administratora o ich nadanie."
        elif isinstance(error, app_commands.CheckFailure):
            # Ten błąd jest często wynikiem naszego niestandardowego `is_manager()` lub `check_if_owner()`
            # Wiadomość o błędzie jest już wysyłana w tych funkcjach, więc tutaj możemy nic nie robić lub tylko logować.
            print(f"[INFO CheckFailure] Sprawdzenie uprawnień nie powiodło się dla {interaction.user} (komenda: {interaction.command.name if interaction.command else 'N/A'}). Wiadomość powinna być już wysłana.")
            return # Zakończ, bo funkcja sprawdzająca już odpowiedziała
        elif isinstance(original_error, discord.errors.Forbidden): # Zmieniono na original_error
            # Ten błąd często oznacza problem z hierarchią ról lub brakujące uprawnienia bota,
            # które nie zostały złapane przez BotMissingPermissions.
            error_msg = "❌ Błąd Uprawnień lub Hierarchii! Bot nie mógł wykonać akcji. Sprawdź, czy rola bota jest wystarczająco wysoko i ma potrzebne uprawnienia."
        elif isinstance(error, app_commands.CommandNotFound):
             # To się raczej nie zdarzy przy synchronizacji, ale na wszelki wypadek
             error_msg = "❌ Nie znaleziono takiej komendy."
        elif isinstance(error, app_commands.CommandSignatureMismatch):
             error_msg = "❌ Niezgodność sygnatury komendy. Bot mógł zostać zaktualizowany. Spróbuj ponownie za chwilę lub skontaktuj się z adminem."
        elif isinstance(error, app_commands.TransformerError):
             error_msg = f"❌ Nieprawidłowy argument: {error}"
        elif isinstance(original_error, json.JSONDecodeError):
             error_msg = "❌ Krytyczny błąd odczytu danych. Skontaktuj się z administratorem."
             print(f"[ERROR Command] Błąd JSON podczas wykonywania komendy '{interaction.command.name if interaction.command else 'N/A'}':")
             traceback.print_exception(type(original_error), original_error, original_error.__traceback__)

        # Logowanie pełnego błędu do konsoli dla administratora
        if not isinstance(error, app_commands.CheckFailure): # Nie loguj pełnego CheckFailure, bo to spam
            print(f"\n--- BŁĄD KOMENDY ---")
            print(f"Serwer: {interaction.guild.name if interaction.guild else 'DM'} ({interaction.guild_id})")
            print(f"Kanał: {interaction.channel.name if interaction.channel else 'DM'} ({interaction.channel_id})")
            print(f"Użytkownik: {interaction.user} ({interaction.user.id})")
            print(f"Komenda: {interaction.command.name if interaction.command else 'N/A'}")
            print(f"Typ Błędu: {type(error).__name__}")
            print(f"Oryginalny Błąd: {type(original_error).__name__}")
            print(f"Wiadomość: {original_error}")
            print(f"Pełny Traceback:")
            # Użyj traceback.print_exception dla lepszego formatowania
            traceback.print_exception(type(error), error, error.__traceback__)
            print(f"--- KONIEC BŁĘDU KOMENDY ---\n")

        # Wysyłanie wiadomości o błędzie do użytkownika
        try:
            if interaction.response.is_done():
                # Jeśli odpowiedź (nawet defer) została już wysłana, użyj followup
                await interaction.followup.send(error_msg, ephemeral=ephemeral_error)
            else:
                # Jeśli żadna odpowiedź nie została wysłana, użyj response
                await interaction.response.send_message(error_msg, ephemeral=ephemeral_error)
        except discord.errors.NotFound:
             print(f"[WARN Handler] Interakcja wygasła przed wysłaniem wiadomości o błędzie: {error_msg}")
        except Exception as e_send:
            # Ostateczność - jeśli nawet wysłanie wiadomości o błędzie zawiedzie
            print(f"[ERROR Handler] Krytyczny błąd: Nie można było wysłać wiadomości o błędzie do użytkownika: {e_send}")


# --- Inicjalizacja Bota ---
# Tworzymy instancję naszej niestandardowej klasy bota
bot = CustomBot()


# --- Komendy Slash ---

@bot.tree.command(name="test", description="Sprawdza czy bot odpowiada i ma dostęp do danych.")
# Ta komenda nie wymaga uprawnień, dostępna dla każdego
async def slash_test(interaction: discord.Interaction):
    """Prosta komenda testowa."""
    if not interaction.guild_id:
        await interaction.response.send_message("Bot działa (DM).", ephemeral=True)
        return

    guild_id = interaction.guild_id
    guild_data = get_guild_data(guild_id) # Spróbuj pobrać dane serwera
    response_msg = f"Bot działa na serwerze: **{interaction.guild.name}**!\n"
    response_msg += f"ID Serwera: `{guild_id}`\n"
    response_msg += f"Liczba znanych pracowników w JSON dla tego serwera: `{len(guild_data)}`\n"
    response_msg += f"Twoje ID: `{interaction.user.id}`\n"

    # Sprawdzamy, czy interaction.user to Member, aby bezpiecznie użyć _ma_wymagane_uprawnienia
    is_manager_status = "N/A (nie na serwerze)"
    if isinstance(interaction.user, discord.Member):
        is_manager_status = f"**{_ma_wymagane_uprawnienia(interaction.user)}**"
    response_msg += f"Czy masz uprawnienia zarządcze (wg bota)?: {is_manager_status}"

    await interaction.response.send_message(response_msg, ephemeral=True)


@bot.tree.command(name="zatrudnij", description="Rejestruje użytkownika w systemie i nadaje role Rekrut & Pracownik.")
@app_commands.describe(member="Użytkownik Discord, którego chcesz zatrudnić.")
@is_manager() # Wymaga uprawnień zarządzających
async def slash_zatrudnij(interaction: discord.Interaction, member: discord.Member):
    """Komenda do 'zatrudniania' - dodaje wpis do JSON i nadaje role bazowe."""
    if member.bot:
        await interaction.response.send_message("❌ Nie można zatrudnić innego bota!", ephemeral=True)
        return

    # Sprawdzenia wstępne (powinny być obsłużone przez dekoratory/handler, ale dla pewności)
    if not interaction.guild or not interaction.guild_id:
        # Odpowiedź powinna być wysłana przez is_manager(), ale na wszelki wypadek
        if not interaction.response.is_done():
             await interaction.response.send_message("Błąd: Ta komenda musi być użyta na serwerze.", ephemeral=True)
        return

    # Defer - operacja może chwilę potrwać (nadawanie ról, zapis do pliku)
    await interaction.response.defer(ephemeral=False) # Odpowiedź widoczna dla innych

    guild = interaction.guild
    guild_id = interaction.guild_id
    member_id_str = str(member.id)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    reason = f"Zatrudnienie/Aktualizacja przez {interaction.user} (ID: {interaction.user.id})"

    # --- Walidacja Ról Bazowych ---
    rekrut_role = guild.get_role(Role.REKRUT)
    pracownik_role = guild.get_role(Role.PRACOWNIK)

    missing_role_ids = []
    if not rekrut_role: missing_role_ids.append(f"'Rekrut' (ID: {Role.REKRUT})")
    if not pracownik_role: missing_role_ids.append(f"'Pracownik' (ID: {Role.PRACOWNIK})")

    if missing_role_ids:
        await interaction.followup.send(f"❌ Błąd Konfiguracji Ról na tym serwerze! Brakujące role: {', '.join(missing_role_ids)}. Skontaktuj się z administratorem.", ephemeral=True)
        return

    bot_member = guild.me
    if not bot_member: await interaction.followup.send("❌ Błąd: Nie można pobrać bota.", ephemeral=True); return
    bot_top_role_pos = bot_member.top_role.position if bot_member.top_role else 0

    hierarchy_issue = False
    if rekrut_role.position >= bot_top_role_pos: hierarchy_issue = True
    if pracownik_role.position >= bot_top_role_pos: hierarchy_issue = True

    if hierarchy_issue:
        await interaction.followup.send(f"❌ Błąd Hierarchii Ról! Rola bota ({bot_member.top_role.name if bot_member.top_role else 'Brak'}) musi być wyżej niż role 'Rekrut' i 'Pracownik'.", ephemeral=True)
        return

    if not bot_member.guild_permissions.manage_roles:
       await interaction.followup.send("❌ Błąd: Bot nie ma uprawnień 'Zarządzanie Rolami' na tym serwerze!", ephemeral=True)
       return
    # --- Koniec Walidacji Ról ---

    guild_data = get_guild_data(guild_id) # Pobierz słownik użytkowników dla TEGO serwera
    roles_to_add_obj: List[discord.Role] = []
    final_message = ""
    is_new_hire = False # Flaga do logowania

    # Sprawdź, czy role są już nadane
    user_has_rekrut = rekrut_role in member.roles
    user_has_pracownik = pracownik_role in member.roles

    if not user_has_rekrut: roles_to_add_obj.append(rekrut_role)
    if not user_has_pracownik: roles_to_add_obj.append(pracownik_role)

    try:
        # Zarządzanie wpisem w JSON
        if member_id_str not in guild_data:
            # Nowy pracownik - tworzymy wpis w JSON
            print(f"[Zatrudnij] Tworzenie nowego wpisu dla {member} na serwerze {guild_id}")
            is_new_hire = True
            pracownik_data = {
                "nazwa": str(member), # Zapisz aktualną nazwę
                "data_zatrudnienia": now_str,
                "rola": pracownik_role.name, # Domyślna rola startowa
                "plusy": 0,
                "minusy": 0,
                "upomnienia": 0,
                "ostrzezenia": [], # Lista na przyszłe ostrzeżenia tekstowe?
                "historia_awansow": [{ # Dodaj wpis o zatrudnieniu do historii
                     "data": now_str,
                     "rola": f"{rekrut_role.name}, {pracownik_role.name}", # Role nadane przy starcie
                     "sciezka": "Start",
                     "poziom": 0,
                     "operator": str(interaction.user),
                     "typ": "zatrudnienie"
                 }]
            }
            guild_data[member_id_str] = pracownik_data # Dodaj do danych serwera
            final_message = f"✅ Pomyślnie zatrudniono {member.mention} i zarejestrowano w systemie!\n"

        else:
            # Pracownik już istnieje w JSON - aktualizujemy tylko nazwę i ew. dodajemy brakujące role
            print(f"[Zatrudnij] Aktualizacja danych dla istniejącego {member} na serwerze {guild_id}")
            guild_data[member_id_str]["nazwa"] = str(member) # Zaktualizuj nazwę
            # Można by dodać logikę aktualizacji roli jeśli np. była "Nieznana"
            final_message = f"🔄 {member.mention} jest już zarejestrowany w systemie.\n"

        # Nadawanie brakujących ról
        if roles_to_add_obj:
            await member.add_roles(*roles_to_add_obj, reason=reason)
            added_roles_str = ", ".join(r.mention for r in roles_to_add_obj)
            final_message += f"Nadano role: {added_roles_str}."
            print(f"[Zatrudnij] Nadano role: {[r.name for r in roles_to_add_obj]} dla {member}")
        else:
            final_message += "Posiadał już wymagane role bazowe (Rekrut, Pracownik)."
            print(f"[Zatrudnij] {member} posiadał już role bazowe.")

        # Zapisz zmiany w JSON (całą strukturę)
        if not await zapisz_pracownikow():
            # Błąd zapisu - poinformuj, ale role mogły zostać nadane
            await interaction.followup.send("⚠️ **Krytyczny Błąd Zapisu Danych!** Role mogły zostać nadane, ale nie udało się zapisać zmian w bazie. Skontaktuj się z administratorem!", ephemeral=False)
            # Nie wysyłaj final_message, bo stan jest niepewny
            return # Zakończ w tym miejscu
        else:
            # Zapis udany - wyślij finalną wiadomość
            await interaction.followup.send(final_message)

            # Logowanie do kanału
            log_action = "zatrudnił" if is_new_hire else "zaktualizował/potwierdził role dla"
            await log_to_channel(interaction=interaction, log_type="hr", message=f"📄 `{datetime.now().strftime('%H:%M')}` {interaction.user.mention} {log_action} {member.mention}.")

    except discord.Forbidden as e:
        print(f"[ERROR Forbidden][Zatrudnij] Błąd uprawnień Discord: {e}")
        await interaction.followup.send(f"❌ Błąd Uprawnień Discord! Bot nie mógł nadać ról ({', '.join(r.name for r in roles_to_add_obj)}) dla {member.mention}. Sprawdź uprawnienia bota i hierarchię.", ephemeral=True)
    except discord.HTTPException as e:
        print(f"[ERROR HTTP][Zatrudnij] Błąd sieci Discord: {e}")
        await interaction.followup.send(f"❌ Błąd Sieci Discord ({e.status})! Spróbuj ponownie za chwilę.", ephemeral=True)
    except Exception as e:
        print(f"[ERROR Generyczny][Zatrudnij] Niespodziewany błąd:")
        traceback.print_exc()
        await interaction.followup.send(f"❌ Wystąpił niespodziewany błąd serwera przy zatrudnianiu: {e}", ephemeral=True)


@bot.tree.command(name="plus", description="Dodaje plus pracownikowi (+1/3, +2/3, +3/3 i reset).")
@app_commands.describe(
    member="Pracownik, który otrzymuje plusa.",
    powod="Powód przyznania plusa (opcjonalny)."
)
@is_manager() # Wymaga uprawnień
async def slash_plus(interaction: discord.Interaction, member: discord.Member, powod: Optional[str] = None):
    """Komenda do dodawania plusów."""
    # Logika jest w funkcji pomocniczej
    await _dodaj_punkt_z_rolami(interaction, member, "plusy", powod)


@bot.tree.command(name="minus", description="Dodaje minus pracownikowi (-1/3, -2/3, -3/3 i reset).")
@app_commands.describe(
    member="Pracownik, który otrzymuje minusa.",
    powod="Powód przyznania minusa (wymagany)."
)
@is_manager() # Wymaga uprawnień
async def slash_minus(interaction: discord.Interaction, member: discord.Member, powod: str):
    """Komenda do dodawania minusów."""
    if not powod or powod.isspace():
       # Sprawdźmy czy interaction już odpowiedziało (np. w is_manager)
       if not interaction.response.is_done():
            await interaction.response.send_message("❌ Powód dla minusa jest wymagany!", ephemeral=True)
       else: # Jeśli is_manager już odpowiedział, użyj followup
            await interaction.followup.send("❌ Powód dla minusa jest wymagany!", ephemeral=True)
       return
    # Logika jest w funkcji pomocniczej
    await _dodaj_punkt_z_rolami(interaction, member, "minusy", powod)


@bot.tree.command(name="upomnienie", description="Dodaje upomnienie pracownikowi (U1/3, U2/3, U3/3 i reset).")
@app_commands.describe(
    member="Pracownik, który otrzymuje upomnienie.",
    powod="Powód przyznania upomnienia (wymagany)."
)
@is_manager() # Wymaga uprawnień
async def slash_upomnienie(interaction: discord.Interaction, member: discord.Member, powod: str):
    """Komenda do dodawania upomnień."""
    if not powod or powod.isspace():
        if not interaction.response.is_done():
             await interaction.response.send_message("❌ Powód dla upomnienia jest wymagany!", ephemeral=True)
        else:
             await interaction.followup.send("❌ Powód dla upomnienia jest wymagany!", ephemeral=True)
        return
    # Logika jest w funkcji pomocniczej
    await _dodaj_punkt_z_rolami(interaction, member, "upomnienia", powod)


@bot.tree.command(name="awansuj", description="Awansuje pracownika na wyższe stanowisko w ramach ścieżki.")
@app_commands.describe(
    member="Pracownik do awansowania.",
    sciezka="Ścieżka rozwoju (np. Ochrona, Gastronomia).",
    poziom="Docelowy poziom na ścieżce (numer roli w kolejności)."
)
@app_commands.choices(sciezka=SCIEZKI_WYBORY) # Dynamiczne wybory ścieżek
@is_manager() # Wymaga uprawnień
async def slash_awansuj(
    interaction: discord.Interaction,
    member: discord.Member,
    sciezka: app_commands.Choice[str],
    poziom: app_commands.Range[int, 1, 6] # Ograniczenie poziomu (max 6 ról w ścieżkach)
):
    """Komenda do awansowania pracownika."""
    # Defer - zmiana ról i zapis może potrwać
    await interaction.response.defer(ephemeral=False)
    # Logika jest w funkcji pomocniczej
    await _zmien_stanowisko(interaction, member, sciezka.value, poziom, None, czy_awans=True)


@bot.tree.command(name="degraduj", description="Degraduje pracownika na niższe stanowisko w ramach ścieżki.")
@app_commands.describe(
    member="Pracownik do zdegradowania.",
    sciezka="Ścieżka rozwoju (np. Ochrona, Gastronomia).",
    poziom="Docelowy poziom na ścieżce (numer roli w kolejności).",
    powod="Powód degradacji (wymagany)."
)
@app_commands.choices(sciezka=SCIEZKI_WYBORY) # Dynamiczne wybory ścieżek
@is_manager() # Wymaga uprawnień
async def slash_degraduj(
    interaction: discord.Interaction,
    member: discord.Member,
    sciezka: app_commands.Choice[str],
    poziom: app_commands.Range[int, 1, 5], # Nie można degradować na ostatni (6) poziom, tylko do 5. Zakładając ścieżki max 6 ról
    powod: str
):
    """Komenda do degradacji pracownika."""
    if not powod or powod.isspace():
       if not interaction.response.is_done(): await interaction.response.send_message("❌ Powód degradacji jest wymagany!", ephemeral=True)
       else: await interaction.followup.send("❌ Powód degradacji jest wymagany!", ephemeral=True)
       return

    # Defer - zmiana ról i zapis może potrwać
    await interaction.response.defer(ephemeral=False)
    # Logika jest w funkcji pomocniczej
    await _zmien_stanowisko(interaction, member, sciezka.value, poziom, powod, czy_awans=False)


@bot.tree.command(name="zwolnij", description="Usuwa pracownika z systemu i odbiera WSZYSTKIE role pracownicze/punktowe.")
@app_commands.describe(
    member="Pracownik do zwolnienia.",
    powod="Powód zwolnienia (opcjonalny, zostanie zapisany w logach)."
)
@is_manager() # Wymaga uprawnień
async def slash_zwolnij(interaction: discord.Interaction, member: discord.Member, powod: Optional[str] = None):
    """Komenda do całkowitego usunięcia pracownika z systemu."""
    if member.id == interaction.user.id:
        await interaction.response.send_message("❌ Nie możesz zwolnić samego siebie.", ephemeral=True); return
    if member.id == bot.user.id:
        await interaction.response.send_message("❌ Nie możesz zwolnić mnie!", ephemeral=True); return
    # Sprawdź, czy osoba zwalniana nie ma wyższych uprawnień niż zwalniający (prosta ochrona)
    # Upewnij się, że interaction.user to Member
    if isinstance(interaction.user, discord.Member) and member.top_role >= interaction.user.top_role and not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Nie możesz zwolnić kogoś z równą lub wyższą rolą.", ephemeral=True); return

    await interaction.response.defer(ephemeral=False) # Odpowiedź widoczna dla innych

    guild = interaction.guild
    guild_id = interaction.guild_id
    member_id_str = str(member.id)
    reason = f"Zwolnienie przez {interaction.user} (ID: {interaction.user.id})" + (f" Powód: {powod}" if powod else "")

    # --- Usuwanie Ról ---
    roles_to_remove_obj: List[discord.Role] = []
    user_role_ids = {r.id for r in member.roles}
    bot_member = guild.me # Pobierzmy obiekt bota na tym serwerze
    if not bot_member:
        await interaction.followup.send("❌ Błąd: Nie można pobrać obiektu bota na serwerze.", ephemeral=True)
        return
    bot_top_role_pos = bot_member.top_role.position if bot_member.top_role else 0

    # Iteruj po WSZYSTKICH rolach do usunięcia zdefiniowanych w konfiguracji
    # Zakładamy, że ROLE_WSZYSTKIE_DO_USUNIECIA mają te same ID na wszystkich serwerach
    roles_not_removed_due_to_hierarchy = []
    for role_id in ROLE_WSZYSTKIE_DO_USUNIECIA:
        if role_id in user_role_ids:
            role = guild.get_role(role_id)
            # Usuwaj tylko jeśli rola istnieje i jest NIŻEJ niż rola bota
            if role and role.position < bot_top_role_pos:
                roles_to_remove_obj.append(role)
            elif role: # Rola istnieje, ale jest za wysoko
                 print(f"[WARN Zwolnij] Nie można usunąć roli {role.name} (ID: {role_id}) - jest na równi/wyżej niż bot.")
                 roles_not_removed_due_to_hierarchy.append(role.name)
            # Jeśli rola == None (nie istnieje na serwerze), nic nie rób

    removed_roles_count = 0
    try:
        if roles_to_remove_obj:
            await member.remove_roles(*roles_to_remove_obj, reason=reason)
            removed_roles_count = len(roles_to_remove_obj)
            print(f"[Zwolnij] Usunięto {removed_roles_count} ról dla {member}: {[r.name for r in roles_to_remove_obj]}")
        else:
            print(f"[Zwolnij] {member} nie posiadał żadnych ról do usunięcia (które bot mógł usunąć).")

        # --- Usuwanie z JSON ---
        guild_data = get_guild_data(guild_id)
        removed_from_json = False
        if member_id_str in guild_data:
            del guild_data[member_id_str] # Usuń wpis użytkownika z danych TEGO serwera
            removed_from_json = True
            print(f"[Zwolnij] Usunięto wpis dla {member} z JSON dla serwera {guild_id}.")

            # Zapisz zmiany w JSON
            if not await zapisz_pracownikow():
                await interaction.followup.send("⚠️ **Krytyczny Błąd Zapisu Danych!** Role zostały usunięte, ale nie udało się usunąć wpisu z bazy. Skontaktuj się z administratorem!", ephemeral=False)
                # Kontynuuj, aby poinformować o usunięciu ról
            else:
                print(f"[Zwolnij] Zapisano zmiany w JSON po usunięciu.")

        # --- Finalna Odpowiedź i Logowanie ---
        final_msg = f"🗑️ Pomyślnie zwolniono {member.mention}.\n"
        if removed_roles_count > 0:
             final_msg += f"- Usunięto role: {removed_roles_count}.\n"
             # final_msg += f"- Role: {', '.join(r.name for r in roles_to_remove_obj)}\n" # Opcjonalnie, może być długie
        else:
             final_msg += "- Nie posiadał ról pracowniczych/punktowych do usunięcia (lub bot nie mógł ich usunąć).\n"

        if roles_not_removed_due_to_hierarchy:
             final_msg += f"⚠️ Nie usunięto ról (problem z hierarchią): {', '.join(roles_not_removed_due_to_hierarchy)}.\n"

        if removed_from_json:
            final_msg += "- Usunięto wpis z bazy danych tego serwera."
        else:
            final_msg += "- Nie był zarejestrowany w bazie danych tego serwera."

        await interaction.followup.send(final_msg)

        # Logowanie
        log_msg_base = f"`{datetime.now().strftime('%H:%M')}` {interaction.user.mention} zwolnił {member.mention}"
        log_msg_reason = f" Powód: {powod or '-'}"
        log_msg_details = f" (Usunięto ról: {removed_roles_count}, Z JSON: {'Tak' if removed_from_json else 'Nie'})"
        await log_to_channel(interaction=interaction, log_type="hr", message=f"🗑️ {log_msg_base}.{log_msg_reason}.{log_msg_details}")

    except discord.Forbidden as e:
        print(f"[ERROR Forbidden][Zwolnij] Błąd uprawnień Discord: {e}")
        await interaction.followup.send(f"❌ Błąd Uprawnień Discord! Bot nie mógł usunąć wszystkich ról dla {member.mention}. Sprawdź uprawnienia bota i hierarchię.", ephemeral=True)
    except discord.HTTPException as e:
        print(f"[ERROR HTTP][Zwolnij] Błąd sieci Discord: {e}")
        await interaction.followup.send(f"❌ Błąd Sieci Discord ({e.status})! Spróbuj ponownie za chwilę.", ephemeral=True)
    except Exception as e:
        print(f"[ERROR Generyczny][Zwolnij] Niespodziewany błąd:")
        traceback.print_exc()
        await interaction.followup.send(f"❌ Wystąpił niespodziewany błąd serwera przy zwalnianiu: {e}", ephemeral=True)


@bot.tree.command(name="historia", description="Wyświetla historię punktów i stanowisk pracownika.")
@app_commands.describe(
    member="Pracownik, którego historię chcesz zobaczyć (domyślnie Ty)."
)
async def slash_historia(interaction: discord.Interaction, member: Optional[discord.Member] = None):
    """Wyświetla dane o pracowniku z pliku JSON."""
    # Celuj w podanego członka lub w autora interakcji, jeśli nikt nie został podany
    target_member = member or interaction.user
    # Upewnijmy się, że target_member to obiekt Member, a nie User (jeśli interaction.user to User)
    if not isinstance(target_member, discord.Member):
        if interaction.guild:
             target_member = interaction.guild.get_member(target_member.id)
             if not target_member:
                 await interaction.response.send_message("❌ Nie można znaleźć tego użytkownika na serwerze.", ephemeral=True)
                 return
        else: # DM
             await interaction.response.send_message("Błąd: Nie można pobrać obiektu Member poza serwerem.", ephemeral=True)
             return

    # Sprawdź uprawnienia, jeśli pytamy o kogoś innego niż my sami
    if target_member.id != interaction.user.id:
        # Upewnij się, że interaction.user to Member do sprawdzenia uprawnień
        requesting_member = interaction.user
        if not isinstance(requesting_member, discord.Member):
            if interaction.guild:
                requesting_member = interaction.guild.get_member(interaction.user.id)
            # Jeśli nadal nie jest Member (np. błąd pobierania), odmów dostępu
            if not isinstance(requesting_member, discord.Member):
                 await interaction.response.send_message("❌ Błąd: Nie można zweryfikować Twoich uprawnień na serwerze.", ephemeral=True)
                 return

        if not _ma_wymagane_uprawnienia(requesting_member):
            await interaction.response.send_message("❌ Nie masz uprawnień do przeglądania historii innych pracowników.", ephemeral=True)
            return

    if not interaction.guild_id:
        await interaction.response.send_message("Błąd: Ta komenda działa tylko na serwerze.", ephemeral=True)
        return

    guild_id = interaction.guild_id
    member_id_str = str(target_member.id)

    guild_data = get_guild_data(guild_id) # Pobierz dane dla TEGO serwera
    pracownik_data = guild_data.get(member_id_str)

    if not pracownik_data:
        # Dodatkowo sprawdźmy role - może ma role, ale nie ma go w JSON?
        if czy_jest_zatrudniony(guild_id, target_member):
             await interaction.response.send_message(f"ℹ️ {target_member.mention} ma role pracownicze, ale nie znaleziono jego historii w bazie danych tego serwera. Użyj /zatrudnij, aby go zarejestrować.", ephemeral=True)
        else:
             await interaction.response.send_message(f"❌ Nie znaleziono danych dla {target_member.mention} w systemie tego serwera.", ephemeral=True)
        return

    # --- Tworzenie Embeda ---
    embed = discord.Embed(
        title=f"📄 Historia Pracownika",
        description=f"Dane dla: {target_member.mention} (`{target_member.id}`)",
        color=discord.Color.blue(),
        timestamp=datetime.now() # Użyj importu datetime
    )
    embed.set_thumbnail(url=target_member.display_avatar.url)
    embed.set_footer(text=f"Serwer: {interaction.guild.name}")

    # Podstawowe informacje
    embed.add_field(name="👤 Nazwa", value=pracownik_data.get("nazwa", "Brak danych"), inline=True)
    embed.add_field(name="📅 Data Zatrudnienia", value=pracownik_data.get("data_zatrudnienia", "Brak danych"), inline=True)
    embed.add_field(name="👔 Aktualna Rola (wg bazy)", value=pracownik_data.get("rola", "Brak danych"), inline=True)

    # Punkty
    embed.add_field(
        name="📊 Punkty",
        value=f"⭐ Plusy: **{pracownik_data.get('plusy', 0)}/3**\n"
              f"❌ Minusy: **{pracownik_data.get('minusy', 0)}/3**\n"
              f"⚠️ Upomnienia: **{pracownik_data.get('upomnienia', 0)}/3**",
        inline=False
    )

    # Historia Awansów/Degradacji (ostatnie kilka)
    historia = pracownik_data.get("historia_awansow", [])
    if historia:
        historia_str = ""
        # Pokaż tylko ostatnie X wpisów (np. 5)
        limit = 5 # Możesz zmienić limit wyświetlanych wpisów
        for wpis in reversed(historia[-limit:]): # Iteruj od końca
             data = wpis.get('data', 'Brak daty')
             rola = wpis.get('rola', 'Brak roli')
             typ = wpis.get('typ', 'zmiana')
             operator = wpis.get('operator', 'System')
             powod = wpis.get('powod')
             emoji = "⬆️" if typ == "awans" else "⬇️" if typ == "degradacja" else "📄" if typ == "zatrudnienie" else "🔄"
             # Formatuj datę do DD-MM-YYYY HH:MM, jeśli to możliwe
             try:
                 data_obj = datetime.strptime(data, "%Y-%m-%d %H:%M:%S")
                 formatted_data = data_obj.strftime("%d-%m-%Y %H:%M")
             except (ValueError, TypeError):
                 formatted_data = data[:16] # Pokaż pierwsze 16 znaków, jeśli format jest inny

             historia_str += f"`{formatted_data}` {emoji} **{rola}** ({typ}) przez *{operator}*"
             if powod: historia_str += f" - Powód: *{powod[:50]}...*" if len(powod) > 50 else f" - Powód: *{powod}*"
             historia_str += "\n"

        if historia_str: # Upewnij się, że coś jest do wyświetlenia
             embed.add_field(name=f"📜 Historia Stanowisk (ost. {min(limit, len(historia))})", value=historia_str, inline=False)
        else:
             embed.add_field(name="📜 Historia Stanowisk", value="Brak historii zmian stanowisk.", inline=False)
    else:
        embed.add_field(name="📜 Historia Stanowisk", value="Brak historii zmian stanowisk.", inline=False)

    # TODO: Dodać paginację dla historii, jeśli jest długa
    # TODO: Dodać wyświetlanie ostrzeżeń tekstowych, jeśli pole "ostrzezenia" jest używane

    # Historia widoczna tylko dla pytającego (lub managera)
    # Sprawdzamy czy interakcja nie została już obsłużona (np. przez błąd uprawnień)
    if not interaction.response.is_done():
        await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        # Jeśli interaction.response.is_done() jest True, a nie było błędu uprawnień,
        # to znaczy, że coś innego (np. defer) już odpowiedziało. Wtedy używamy followup.
        # Jednak w tym przypadku nie robiliśmy defer, więc ta ścieżka jest mniej prawdopodobna
        # dla /historia, chyba że wystąpi inny błąd przed wysłaniem.
        try:
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
             print(f"[ERROR Historia] Nie można wysłać followup dla historii: {e}")


# Komenda do czyszczenia komend (tylko dla właściciela)
@bot.tree.command(name="clear_guild_commands", description="[DEV] Usuwa WSZYSTKIE komendy slash bota dla danego serwera.")
@app_commands.check(check_if_owner) # Używa dodanej funkcji sprawdzającej
@app_commands.describe(guild_id_clear="ID serwera, z którego usunąć komendy bota.")
async def slash_clear_guild_commands(interaction: discord.Interaction, guild_id_clear: str):
    """Tymczasowa komenda do czyszczenia komend dla serwera."""
    await interaction.response.defer(ephemeral=True)
    print(f"[DEV] Użytkownik {interaction.user} zainicjował clear_guild_commands.")

    try:
        gid_to_clear = int(guild_id_clear)
        guild_obj_to_clear = discord.Object(id=gid_to_clear)

        # Możesz dodać sprawdzenie, czy ID jest na liście GUILD_IDS_LIST, jeśli chcesz
        # if gid_to_clear not in GUILD_IDS_LIST:
        #     await interaction.followup.send(f"⚠️ Serwer {gid_to_clear} nie jest na liście skonfigurowanych. Mimo to spróbuję wyczyścić.", ephemeral=True)

        print(f"[DEV] Czyszczę komendy dla serwera ID: {gid_to_clear}...")
        bot.tree.clear_commands(guild=guild_obj_to_clear) # Usuń komendy z drzewa dla tego serwera
        await bot.tree.sync(guild=guild_obj_to_clear)     # Zsynchronizuj (wyślij pustą listę do Discorda)
        print(f"[DEV] Komendy dla serwera {gid_to_clear} WYSŁANO PROŚBĘ O WYCZYSZCZENIE.")

        # WAŻNE: Po wyczyszczeniu Discord może potrzebować chwili.
        # Teoretycznie setup_hook przy następnym restarcie powinien je dodać.
        # Można też dodać force_sync zaraz po clear, ale czasem lepiej dać Discordowi oddech.

        await interaction.followup.send(f"✅ Wysłano żądanie wyczyszczenia komend dla serwera `{gid_to_clear}`. **ZRESTARTUJ BOTA TERAZ**, aby zarejestrować poprawne komendy. Po restarcie bota, zrestartuj też swojego klienta Discord.", ephemeral=True)

    except ValueError:
        await interaction.followup.send("❌ Nieprawidłowe ID serwera.", ephemeral=True)
    except discord.errors.Forbidden as e:
        error_info = f"🚫 FORBIDDEN: {guild_id_clear} - Brak uprawnień `application.commands`?"
        print(f"[DEV ERROR][Clear] {error_info} - {e}")
        await interaction.followup.send(f"Błąd uprawnień przy czyszczeniu dla `{guild_id_clear}`: {e}", ephemeral=True)
    except Exception as e:
        error_info = f"❌ ERROR: {guild_id_clear} - {type(e).__name__}: {e}"
        print(f"[DEV ERROR][Clear] {error_info}")
        traceback.print_exc()
        await interaction.followup.send(f"Niespodziewany błąd przy czyszczeniu dla `{guild_id_clear}`: {e}", ephemeral=True)


# --- Uruchomienie Bota ---
if __name__ == "__main__":
    BOT_TOKEN = os.getenv("DISCORD_TOKEN")
    if not BOT_TOKEN:
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("!!!  BŁĄD KRYTYCZNY: Brak tokenu bota w zmiennej        !!!")
        print("!!!  środowiskowej DISCORD_TOKEN. Ustaw go w systemie    !!!")
        print("!!!  lub pliku .env i uruchom ponownie.                 !!!")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    else:
        try:
            print("Próba uruchomienia bota...")
            bot.run(BOT_TOKEN)
        except discord.PrivilegedIntentsRequired:
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print("!!!  BŁĄD KRYTYCZNY: Brak uprawnień Privileged Intents!    !!!")
            print("!!!  Bot wymaga 'Server Members Intent'. Włącz go w       !!!")
            print("!!!  ustawieniach bota na portalu Discord Developer.      !!!")
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        except discord.LoginFailure:
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print("!!!  BŁĄD KRYTYCZNY: Nieprawidłowy token bota!            !!!")
            print("!!!  Sprawdź, czy token w DISCORD_TOKEN jest poprawny.   !!!")
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        except Exception as e:
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print(f"!!!  Nieoczekiwany błąd podczas uruchamiania bota: {e}      !!!")
            traceback.print_exc()
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
