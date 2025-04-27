# -*- coding: utf-8 -*-
import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import asyncio
from dotenv import load_dotenv
from datetime import datetime
from typing import Literal, Optional
import traceback

# --- Konfiguracja Początkowa ---
load_dotenv()
# !!! Lista ID serwerów, na których bot ma działać !!!
# Używamy teraz listy ID liczbowych
GUILD_IDS_LIST = [
    1021373051272704130,
    1364669344180863088
]
# Tworzymy listę obiektów discord.Object dla setup_hook
GUILD_OBJS = [discord.Object(id=gid) for gid in GUILD_IDS_LIST]

JSON_FILE = 'pracownicy.json'
ITEMS_PER_PAGE = 7

# --- Role IDs (Zakładamy, że są takie same na wszystkich serwerach z listy GUILD_IDS_LIST) ---
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

# --- Ścieżki awansu i mapowanie (bez zmian) ---
SCIEZKA_OCHRONY = [Role.REKRUT, Role.MLODSZY_OCHRONIARZ, Role.OCHRONIARZ, Role.OCHRONIARZ_LICENCJONOWANY, Role.DOSWIADCZONY_OCHRONIARZ, Role.STARSZY_OCHRONIARZ]
SCIEZKA_GASTRONOMII = [Role.REKRUT, Role.KELNER, Role.ASYSTENT_KUCHARZA, Role.KUCHARZ, Role.SZEF_KUCHNI, Role.OBSLUGA_BARU]
SCIEZKA_ZARZADU = [Role.REKRUT, Role.PRACOWNIK, Role.ASYSTENT_KIEROWNIKA, Role.KIEROWNIK, Role.MENADZER, Role.ZASTEPCA_SZEFA]
SCIEZKA_ZARZADU_OCHRONY = [Role.OCHRONA, Role.SZKOLENIOWIEC_OCHRONY, Role.EGZAMINATOR_OCHRONY, Role.ASYSTENT_SZEFA_OCHRONY, Role.ZASTEPCA_SZEFA_OCHRONY, Role.SZEF_OCHRONY]
SCIEZKI_MAP = {"ochrona": SCIEZKA_OCHRONY, "gastronomia": SCIEZKA_GASTRONOMII, "zarząd": SCIEZKA_ZARZADU, "zarzad_ochrony": SCIEZKA_ZARZADU_OCHRONY}
SCIEZKI_WYBORY = [app_commands.Choice(name=n.replace('_',' ').title(), value=n) for n in SCIEZKI_MAP.keys()]

# --- Grupy Ról (bez zmian) ---
ROLE_ZARZADZAJACE = [r for r in [Role.NADZOR_PRACY, Role.WLASCICIEL_FIRMY, Role.ZASTEPCA_SZEFA, Role.MENADZER, Role.KIEROWNIK, Role.ASYSTENT_KIEROWNIKA, Role.TECHNIK, Role.NADZOR_OCHRONY, Role.SZEF_OCHRONY, Role.ZASTEPCA_SZEFA_OCHRONY, Role.ASYSTENT_SZEFA_OCHRONY, Role.EGZAMINATOR_OCHRONY, Role.SZKOLENIOWIEC_OCHRONY] if r is not None]
ROLE_PRACOWNICZE_WSZYSTKIE = list(set([rid for rid in (ROLE_ZARZADZAJACE + [Role.REKRUT, Role.PRACOWNIK, Role.OCHRONA] + SCIEZKA_OCHRONY + SCIEZKA_GASTRONOMII + SCIEZKA_ZARZADU + SCIEZKA_ZARZADU_OCHRONY) if rid is not None]))
ROLE_PUNKTOWE = [Role.PLUS1, Role.PLUS2, Role.PLUS3, Role.MINUS1, Role.MINUS2, Role.MINUS3, Role.UPOMNIENIE1, Role.UPOMNIENIE2, Role.UPOMNIENIE3]
ROLE_WSZYSTKIE_DO_USUNIECIA = set(ROLE_PRACOWNICZE_WSZYSTKIE + ROLE_PUNKTOWE)

# --- Mapowanie Punktów (bez zmian) ---
POINT_ROLE_LEVELS_MAP = {
    "plusy": {1: Role.PLUS1, 2: Role.PLUS2, 3: Role.PLUS3},
    "minusy": {1: Role.MINUS1, 2: Role.MINUS2, 3: Role.MINUS3},
    "upomnienia": {1: Role.UPOMNIENIE1, 2: Role.UPOMNIENIE2, 3: Role.UPOMNIENIE3}
}

# --- Kanały Logowania ---
class Kanaly:
    # TODO: Rozważ trzymanie ID kanałów per serwer (np. w pliku config)
    LOGI_HR = 1234567890
    LOGI_PUNKTY = 1234567890
    LOGI_AWANSE = 1234567890

# --- Słownik pracowników (teraz zagnieżdżony per serwer) i Lock ---
pracownicy = {} # Klucz: str(guild_id), Wartość: dict pracowników dla tego serwera
json_lock = asyncio.Lock()

# --- Funkcje Pomocnicze ---
async def zapisz_pracownikow():
    """Bezpiecznie zapisuje CAŁĄ strukturę danych (wszystkie serwery) do JSON."""
    async with json_lock:
        try:
            with open(JSON_FILE, 'w', encoding='utf-8') as f: json.dump(pracownicy, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e: print(f"[ERROR] Błąd zapisywania {JSON_FILE}: {str(e)}"); traceback.print_exc(); return False

async def wczytaj_pracownikow():
    """Wczytuje CAŁĄ strukturę danych pracowników z JSON."""
    global pracownicy
    async with json_lock:
        try:
            if os.path.exists(JSON_FILE):
                with open(JSON_FILE, 'r', encoding='utf-8') as f: pracownicy = json.load(f)
                # Klucze (ID serwerów) są stringami w JSON, ale będziemy używać int
                # Można przekonwertować klucze na int, ale wymaga to ostrożności
                print(f"[INFO] Wczytano dane dla {len(pracownicy)} serwerów z {JSON_FILE}")
            else: print(f"[INFO] Plik {JSON_FILE} nie istnieje."); pracownicy = {}
            return True
        except json.JSONDecodeError as e:
            print(f"[ERROR] Błąd dekodowania JSON {JSON_FILE}: {str(e)}"); print(f"[WARN] Tworzę backup.")
            try: os.rename(JSON_FILE, f"{JSON_FILE}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            except OSError as os_err: print(f"[ERROR] Nie udało się utworzyć backupu: {os_err}")
            pracownicy = {}; return False
        except Exception as e: print(f"[ERROR] Inny błąd wczytywania {JSON_FILE}: {str(e)}"); traceback.print_exc(); pracownicy = {}; return False

def get_guild_data(guild_id: int) -> dict:
    """Pobiera (lub tworzy) słownik danych dla konkretnego serwera."""
    guild_id_str = str(guild_id) # Używamy stringów jako kluczy w głównym dict
    if guild_id_str not in pracownicy:
        print(f"[INFO] Tworzenie struktury danych dla serwera {guild_id_str}")
        pracownicy[guild_id_str] = {}
    return pracownicy[guild_id_str]

def _ma_wymagane_uprawnienia(member: discord.Member) -> bool:
    """Sprawdza czy użytkownik ma rolę zarządzającą lub jest adminem."""
    if not member or not isinstance(member, discord.Member): return False
    if member.guild_permissions.administrator: return True
    user_role_ids = {role.id for role in member.roles}
    # Zakładamy, że ROLE_ZARZADZAJACE są takie same na wszystkich serwerach
    return any(role_id in user_role_ids for role_id in ROLE_ZARZADZAJACE if role_id is not None)

def is_manager():
    """Dekorator @app_commands.check sprawdzający uprawnienia zarządzające."""
    async def predicate(interaction: discord.Interaction) -> bool:
        if not interaction.guild: # Komenda musi być na serwerze
            await interaction.response.send_message("Tej komendy można używać tylko na serwerze.", ephemeral=True)
            return False
        user_to_check = interaction.user
        if not isinstance(user_to_check, discord.Member): # Zapewnij, że mamy obiekt Member
             user_to_check = interaction.guild.get_member(interaction.user.id)
             if not isinstance(user_to_check, discord.Member): allowed = False
             else: allowed = _ma_wymagane_uprawnienia(user_to_check)
        else: allowed = _ma_wymagane_uprawnienia(user_to_check)
        if not allowed and not interaction.response.is_done(): await interaction.response.send_message("❌ Nie masz uprawnień!", ephemeral=True)
        elif not allowed: print(f"[WARN Perm Check] {interaction.user} brak uprawnień (interakcja zakończona).")
        return allowed
    return app_commands.check(predicate)

def czy_jest_zatrudniony(guild_id: int, member: discord.Member) -> bool:
    """Sprawdza czy użytkownik jest w bazie DANEGO SERWERA LUB ma rolę pracowniczą."""
    if not member or not isinstance(member, discord.Member): return False
    guild_data = get_guild_data(guild_id) # Pobierz dane dla TEGO serwera
    if str(member.id) in guild_data: return True
    user_role_ids = {role.id for role in member.roles}
    return any(role_id in user_role_ids for role_id in ROLE_PRACOWNICZE_WSZYSTKIE)

async def log_to_channel(bot_instance: commands.Bot, channel_id: int, message: str = None, embed: discord.Embed = None):
    """Wysyła wiadomość lub embed na określony kanał."""
    if not channel_id or channel_id == 1234567890: return
    channel = bot_instance.get_channel(channel_id)
    if not isinstance(channel, discord.TextChannel): print(f"[ERROR LOG] Kanał {channel_id} nie jest tekstowy."); return
    try: await channel.send(content=message, embed=embed)
    except discord.Forbidden: print(f"[ERROR LOG] Brak uprawnień do pisania na kanale {channel_id}.")
    except Exception as e: print(f"[ERROR LOG] Błąd wysyłania logu na {channel_id}: {e}"); traceback.print_exc()

# --- Funkcja Punktów (Wersja z Rolami Poziomowymi) ---
async def _dodaj_punkt_z_rolami(interaction: discord.Interaction, member: discord.Member, typ: str, powod: Optional[str] = None) -> bool:
    """Zarządza punktami i rolami poziomowymi 1/3, 2/3, 3/3 dla danego serwera."""
    try:
        if not interaction.guild_id: # Dodatkowe zabezpieczenie
             await interaction.response.send_message("Błąd: Brak ID serwera.", ephemeral=True); return False

        guild_id = interaction.guild_id
        member_id_str = str(member.id)
        log_prefix = f"[DEBUG RolePoints][{interaction.guild_id}][{typ}][{member.name}]"
        print(f"{log_prefix} Rozpoczęto.")

        if not interaction.response.is_done(): await interaction.response.defer(ephemeral=False)

        guild_data = get_guild_data(guild_id) # Pobierz dane dla tego serwera

        if member_id_str not in guild_data:
            # Sprawdźmy, czy użytkownik ma role, jeśli tak, poinformuj, że trzeba go zatrudnić
            if czy_jest_zatrudniony(guild_id, member): # Przekaż guild_id
                 await interaction.followup.send(f"❌ {member.mention} nie jest formalnie zarejestrowany w systemie tego serwera. Użyj /zatrudnij.", ephemeral=True); return False
            else: # Jeśli nie ma ani wpisu, ani roli - nie jest zatrudniony
                 await interaction.followup.send(f"❌ {member.mention} nie jest zatrudniony na tym serwerze.", ephemeral=True); return False

        level_role_ids = POINT_ROLE_LEVELS_MAP.get(typ)
        if not level_role_ids: print(f"{log_prefix} BŁĄD: Nieznany typ punktu: {typ}"); await interaction.followup.send(f"❌ Błąd wewnętrzny.", ephemeral=True); return False

        roles, missing_roles_info, hierarchy_ok = {}, [], True
        bot_member = interaction.guild.me; bot_top_role_pos = bot_member.top_role.position
        print(f"{log_prefix} Pozycja bota ({bot_member.top_role.name}): {bot_top_role_pos}")
        for level, role_id in level_role_ids.items():
            role = interaction.guild.get_role(role_id); roles[level] = role
            if role is None: print(f"{log_prefix} BŁĄD: Rola Poziom {level} (ID: {role_id}) NIE ZNALEZIONA!"); missing_roles_info.append(f"Poziom {level} (ID: {role_id})")
            else:
                print(f"{log_prefix} Rola Poziom {level}: '{role.name}' (Poz: {role.position})")
                if role.position >= bot_top_role_pos: print(f"{log_prefix} BŁĄD HIERARCHII: Rola '{role.name}' >= bot!"); hierarchy_ok = False
        if missing_roles_info: await interaction.followup.send(f"❌ Błąd Konf: Brakujące role dla '{typ}': {', '.join(missing_roles_info)}!", ephemeral=True); return False
        if not hierarchy_ok: await interaction.followup.send(f"❌ Błąd Hierarchii: Rola bota ({bot_member.top_role.name}) jest zbyt nisko!", ephemeral=True); return False
        if not bot_member.guild_permissions.manage_roles: await interaction.followup.send("❌ Bot nie ma uprawnień 'Zarządzanie Rolami'!", ephemeral=True); return False
        print(f"{log_prefix} Walidacja OK.")

        current_level, current_role_obj = 0, None
        user_roles_set = {r.id for r in member.roles}
        # Używamy poprawnie pobranych obiektów ról z 'roles'
        for level in [3, 2, 1]:
            role_obj = roles.get(level)
            if role_obj and role_obj.id in user_roles_set: current_level, current_role_obj = level, role_obj; break
        print(f"{log_prefix} Aktualny poziom: {current_level}")

        new_level = current_level + 1; osiagnieto_limit = new_level > 3
        role_to_remove, role_to_add = current_role_obj, roles.get(new_level) if not osiagnieto_limit else None
        final_level_in_db = 0 if osiagnieto_limit else new_level
        print(f"{log_prefix} Nowy poziom: {new_level}, Limit?: {osiagnieto_limit}, Usuń: {role_to_remove}, Dodaj: {role_to_add}")

        role_action_success = True; reason = f"Punkt {typ} ({new_level if not osiagnieto_limit else 'LIMIT'}) przez {interaction.user}"
        try:
            current_user_roles_set = {r.id for r in member.roles} # Odśwież
            if role_to_remove and role_to_remove.id in current_user_roles_set:
                print(f"{log_prefix} Usuwanie {role_to_remove.name}...")
                await member.remove_roles(role_to_remove, reason=reason)
            if role_to_add and role_to_add.id not in current_user_roles_set:
                print(f"{log_prefix} Dodawanie {role_to_add.name}...")
                await member.add_roles(role_to_add, reason=reason)
        except discord.Forbidden as e: print(f"[ERROR Forbidden] {log_prefix} {e}"); await interaction.followup.send(f"❌ Bot nie ma uprawnień Discord!", ephemeral=True); role_action_success = False; return False
        except discord.HTTPException as e: print(f"[ERROR HTTP] {log_prefix} {e}"); await interaction.followup.send(f"❌ Błąd sieci Discord!", ephemeral=True); role_action_success = False; return False
        except Exception as e: print(f"[ERROR Generyczny] {log_prefix}"); traceback.print_exc(); await interaction.followup.send(f"❌ Błąd zarządzania rolą!", ephemeral=True); role_action_success = False; return False

        if role_action_success:
            guild_data = get_guild_data(guild_id) # Pobierz ponownie dane serwera
            pracownik_data = guild_data.setdefault(member_id_str, {"nazwa": str(member), "plusy":0, "minusy":0, "upomnienia":0}) # Upewnij się, że pracownik istnieje
            pracownik_data[typ] = final_level_in_db # Zaktualizuj punkty
            print(f"{log_prefix} Zapisuję poziom {final_level_in_db} do bazy dla serwera {guild_id}.")
            if not await zapisz_pracownikow(): await interaction.followup.send("⚠️ Błąd zapisu punktów!", ephemeral=True)

        emoji_map = {"plusy": "⭐", "minusy": "❌", "upomnienia": "⚠️"}; emoji = emoji_map.get(typ, "")
        final_message, role_change_info = "", ""
        if role_to_remove: role_change_info += f"Usunięto: {role_to_remove.mention}. "
        if role_to_add: role_change_info += f"Nadano: {role_to_add.mention}."

        if osiagnieto_limit:
            final_message = f"{emoji} {member.mention} otrzymał(a) punkt ({new_level}/3)" + (f"\nPowód: {powod}" if powod else "") + f"\n**Osiągnięto limit 3! Licznik '{typ}' i role zresetowane.**"
            if role_to_remove: final_message += f"\n*{role_change_info.strip()}*"
        else:
            final_message = f"{emoji} {member.mention} otrzymał(a) punkt ({new_level}/3)" + (f"\nPowód: {powod}" if powod else "")
            if role_change_info: final_message += f"\n*{role_change_info.strip()}*"

        await interaction.followup.send(final_message, ephemeral=False)
        log_msg = f"{emoji} `{datetime.now().strftime('%H:%M')}` {interaction.user.mention} -> {member.mention} ({typ} {new_level if not osiagnieto_limit else 'LIMIT/RESET'}). Powód: {powod or '-'}. {role_change_info.strip()}"
        await log_to_channel(bot, Kanaly.LOGI_PUNKTY, message=log_msg) # Używamy globalnego ID kanału
        return osiagnieto_limit

    except Exception as e:
        print(f"[ERROR KRYTYCZNY] {log_prefix} Błąd:"); traceback.print_exc()
        try:
            if interaction.response.is_done(): await interaction.followup.send(f"Wystąpił krytyczny błąd: {e}", ephemeral=True)
        except Exception as e2: print(f"[ERROR Handler] Nie można wysłać wiad. o błędzie krytycznym: {e2}")
        return False


# --- Funkcja zmiany stanowiska ---
async def _zmien_stanowisko(interaction: discord.Interaction, member: discord.Member, sciezka_key: str, poziom: int, powod: Optional[str], czy_awans: bool):
    """Wewnętrzna funkcja do awansu/degradacji."""
    if not interaction.guild_id: await interaction.response.send_message("Błąd: Brak ID serwera.", ephemeral=True); return False

    guild_id = interaction.guild_id
    guild_data = get_guild_data(guild_id)
    member_id_str = str(member.id)

    sciezka_awansu = SCIEZKI_MAP.get(sciezka_key)
    nazwa_sciezki = sciezka_key;
    for choice in SCIEZKI_WYBORY:
        if choice.value == sciezka_key: nazwa_sciezki = choice.name; break
    if not sciezka_awansu: await interaction.followup.send(f"❌ Błąd: Ścieżka '{sciezka_key}'?", ephemeral=True); return False
    rola_bazowa_wymagana_id = Role.OCHRONA if sciezka_key == "zarzad_ochrony" else Role.PRACOWNIK
    rola_bazowa_wymagana = interaction.guild.get_role(rola_bazowa_wymagana_id)
    if not rola_bazowa_wymagana or rola_bazowa_wymagana not in member.roles: await interaction.followup.send(f"❌ Brak roli bazowej!", ephemeral=True); return False
    aktualna_rola, aktualny_poziom_idx = None, -1
    for i, rola_id in enumerate(sciezka_awansu):
        rola = interaction.guild.get_role(rola_id)
        if rola and rola in member.roles:
             if i > aktualny_poziom_idx: aktualna_rola, aktualny_poziom_idx = rola, i
    aktualny_poziom_num = aktualny_poziom_idx + 1; docelowy_poziom_idx = poziom - 1; max_poziom_idx = len(sciezka_awansu) - 1
    typ_operacji = "Awans" if czy_awans else "Degradacja"
    if docelowy_poziom_idx > max_poziom_idx or docelowy_poziom_idx < 0: await interaction.followup.send(f"❌ Zły poziom ({poziom})!", ephemeral=True); return False
    if czy_awans:
         if aktualny_poziom_idx == -1 and poziom != 1: await interaction.followup.send(f"❌ Tylko na Poziom 1.", ephemeral=True); return False
         if aktualny_poziom_idx != -1 and poziom <= aktualny_poziom_num: await interaction.followup.send(f"❌ Już na tym/wyższym poziomie.", ephemeral=True); return False
    else: # Degradacja
         if aktualny_poziom_idx == -1: await interaction.followup.send(f"❌ Brak roli ze ścieżki.", ephemeral=True); return False
         if docelowy_poziom_idx >= aktualny_poziom_idx: await interaction.followup.send(f"❌ Nie można degradować na ten sam/wyższy.", ephemeral=True); return False
    nowa_rola_id = sciezka_awansu[docelowy_poziom_idx]; nowa_rola = interaction.guild.get_role(nowa_rola_id)
    if not nowa_rola: await interaction.followup.send(f"❌ Błąd Konf: Brak roli poz. {poziom}!", ephemeral=True); return False
    bot_member = interaction.guild.me
    if nowa_rola.position >= bot_member.top_role.position or (aktualna_rola and aktualna_rola.position >= bot_member.top_role.position): await interaction.followup.send(f"❌ Błąd hierarchii!", ephemeral=True); return False
    try:
        roles_to_remove = []
        if czy_awans:
             for i, rid in enumerate(sciezka_awansu):
                 if i == docelowy_poziom_idx: continue
                 r = interaction.guild.get_role(rid)
                 if r and r in member.roles and r.position < bot_member.top_role.position: roles_to_remove.append(r)
        elif aktualna_rola: roles_to_remove.append(aktualna_rola)
        if roles_to_remove: await member.remove_roles(*roles_to_remove, reason=f"{typ_operacji} przez {interaction.user}")
        if nowa_rola not in member.roles: await member.add_roles(nowa_rola, reason=f"{typ_operacji} przez {interaction.user}")

        # Aktualizacja danych DLA TEGO SERWERA
        pracownik_data = guild_data.setdefault(member_id_str, {"nazwa": str(member), "plusy":0, "minusy":0, "upomnienia":0, "ostrzezenia":[], "historia_awansow":[]})
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if "data_zatrudnienia" not in pracownik_data: pracownik_data["data_zatrudnienia"] = now # Ustaw jeśli brak
        pracownik_data["rola"] = nowa_rola.name
        historia_entry = {"data": now, "rola": nowa_rola.name, "awansujacy": str(interaction.user), "typ": "awans" if czy_awans else "degradacja"}
        if not czy_awans and powod: historia_entry["powod"] = powod
        pracownik_data.setdefault("historia_awansow", []).append(historia_entry)

        if not await zapisz_pracownikow(): await interaction.followup.send("⚠️ Błąd zapisu!", ephemeral=True)
        emoji = "✅" if czy_awans else "⬇️"; msg = f"{emoji} Pomyślnie {'awansowano' if czy_awans else 'zdegradowano'} {member.mention}!\nŚcieżka: {nazwa_sciezki} | Rola: {nowa_rola.name} (Poz: {poziom}/{len(sciezka_awansu)})"
        if not czy_awans and powod: msg += f"\nPowód: {powod}"
        await interaction.followup.send(msg)
        await log_to_channel(bot, Kanaly.LOGI_AWANSE, message=msg.replace(f"{member.mention}", f"**{member.display_name}** (`{member.id}`)"))
        return True
    except discord.Forbidden: await interaction.followup.send("❌ Błąd uprawnień bota!", ephemeral=True); return False
    except Exception as e: await interaction.followup.send(f"❌ Błąd: {str(e)}", ephemeral=True); print(f"Błąd w _zmien_stanowisko: {e}"); traceback.print_exc(); return False

# --- Konfiguracja Bota ---
intents = discord.Intents.default()
intents.message_content = False # Wyłączone
intents.members = True
intents.guilds = True

# --- Klasa Bota i Eventy ---
class CustomBot(commands.Bot):
    def __init__(self):
        super().__init__(intents=intents, command_prefix="!") # Prefix wymagany

    async def setup_hook(self):
        print("Rozpoczynam normalny setup hook...")
        await wczytaj_pracownikow()
        # Synchronizuj komendy dla KAŻDEGO serwera z listy GUILD_OBJS
        for guild_obj in GUILD_OBJS:
            try:
                await self.tree.sync(guild=guild_obj)
                print(f"Komendy zsynchronizowane dla serwera {guild_obj.id}")
            except discord.errors.Forbidden as e: print(f"BŁĄD KRYTYCZNY: Bot nie ma uprawnień do synchronizacji komend na {guild_obj.id}! ({e})")
            except Exception as e: print(f"Błąd synchronizacji dla {guild_obj.id}: {str(e)}"); traceback.print_exc()
        print("Normalny Setup hook zakończony!")

    async def on_ready(self):
        print(f'Bot zalogowany jako {self.user.name} ({self.user.id}), discord.py {discord.__version__}')
        print('-------------------')
        for guild in self.guilds: # Pokaż info dla wszystkich serwerów, na których jest bot
            print(f'- Serwer: {guild.name} (ID: {guild.id})')
            bot_member = guild.me
            if bot_member: print(f"  - Rola bota: {bot_member.top_role.name} (Poz: {bot_member.top_role.position}), Ma Zarządzanie Rolami: {bot_member.guild_permissions.manage_roles}")
            else: print("  - Nie można pobrać info o bocie.")
        print('-------------------'); print('Bot gotowy!')

    # Globalny handler błędów
    async def on_tree_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        error_msg = f"Wystąpił błąd: {error}"; ephemeral_error = True
        if isinstance(error, app_commands.CommandOnCooldown): error_msg = f"⏳ Zwolnij! Spróbuj za {error.retry_after:.1f}s."
        elif isinstance(error, (app_commands.MissingPermissions, app_commands.CheckFailure)): error_msg = "❌ Brak uprawnień."
        elif isinstance(error, app_commands.BotMissingPermissions): error_msg = f"❌ Bot nie ma uprawnień: `{', '.join(error.missing_permissions)}`."
        elif isinstance(error, discord.errors.Forbidden): error_msg = "❌ Błąd uprawnień bota / hierarchii ról."
        elif isinstance(error, app_commands.CommandSignatureMismatch): error_msg = "❌ Niezgodność komendy. Spróbuj /force_sync lub skontaktuj się z adminem."
        print(f"[ERROR Command] '{interaction.command.name if interaction.command else 'N/A'}':"); traceback.print_exception(type(error), error, error.__traceback__)
        try:
            if interaction.response.is_done(): await interaction.followup.send(error_msg, ephemeral=ephemeral_error)
            else: await interaction.response.send_message(error_msg, ephemeral=ephemeral_error)
        except Exception as e_send: print(f"[ERROR Handler] Nie wysłano wiad. o błędzie: {e_send}")

# --- Inicjalizacja Bota ---
bot = CustomBot()

# --- Komendy Slash ---

@bot.tree.command(name="test", description="Sprawdza czy bot działa")
async def slash_test(interaction: discord.Interaction):
    await interaction.response.send_message("Bot działa!", ephemeral=True)

@bot.tree.command(name="zatrudnij", description="Rejestruje użytkownika i nadaje role Rekrut & Pracownik")
@app_commands.describe(member="Użytkownik do zatrudnienia")
@is_manager()
async def slash_zatrudnij(interaction: discord.Interaction, member: discord.Member):
    if member.bot: await interaction.response.send_message("❌ Nie można zatrudnić bota!", ephemeral=True); return
    if not interaction.guild_id: await interaction.response.send_message("Błąd: Brak ID serwera.", ephemeral=True); return
    await interaction.response.defer(ephemeral=False)

    guild_id = interaction.guild_id
    guild_data = get_guild_data(guild_id) # Pobierz dane dla TEGO serwera

    rekrut_role = interaction.guild.get_role(Role.REKRUT); pracownik_role = interaction.guild.get_role(Role.PRACOWNIK)
    if not rekrut_role or not pracownik_role: await interaction.followup.send(f"❌ Błąd Konf: Brak roli Rekrut/Pracownik!", ephemeral=True); return
    bot_member = interaction.guild.me
    if rekrut_role.position >= bot_member.top_role.position or pracownik_role.position >= bot_member.top_role.position: await interaction.followup.send("❌ Bot ma zbyt niską rolę!", ephemeral=True); return

    member_id_str = str(member.id); zatrudnienie_info = ""; now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    roles_to_add_obj = [r for r in [rekrut_role, pracownik_role] if r not in member.roles]

    try:
        # Działamy na guild_data zamiast globalnego pracownicy
        if member_id_str not in guild_data:
            await member.add_roles(*roles_to_add_obj, reason=f"Zatrudniony przez {interaction.user}")
            # Zapisujemy w słowniku dla danego serwera
            guild_data[member_id_str] = {"nazwa": str(member), "data_zatrudnienia": now, "rola": pracownik_role.name, "plusy": 0, "minusy": 0, "upomnienia": 0, "ostrzezenia": [], "historia_awansow": [{"data": now, "rola": f"{rekrut_role.name}, {pracownik_role.name}", "awansujacy": str(interaction.user)}]}
            zatrudnienie_info = f"✅ Pomyślnie zatrudniono {member.mention}!\nNadano role: {', '.join(r.name for r in roles_to_add_obj) if roles_to_add_obj else 'Brak nowych'}"
        else:
             if roles_to_add_obj:
                 await member.add_roles(*roles_to_add_obj, reason=f"Uzupełnienie przez {interaction.user}")
                 zatrudnienie_info = f"🔄 {member.mention} był w systemie, nadano brakujące role: {', '.join(r.name for r in roles_to_add_obj)}."
                 guild_data[member_id_str]['rola'] = pracownik_role.name # Aktualizacja w danych serwera
             else:
                 await interaction.followup.send(f"ℹ️ {member.mention} jest już w systemie i ma wymagane role.", ephemeral=True); return

        if not await zapisz_pracownikow(): await interaction.followup.send("⚠️ KRYTYCZNY błąd zapisu danych!", ephemeral=True); return

        await interaction.followup.send(zatrudnienie_info)
        await log_to_channel(bot, Kanaly.LOGI_HR, message=f"📄 {interaction.user.mention} zatrudnił/zaktualizował {member.mention} na serwerze {interaction.guild.name}.")
    except discord.Forbidden: await interaction.followup.send("❌ Bot nie ma uprawnień do nadania ról!", ephemeral=True)
    except Exception as e: await interaction.followup.send(f"❌ Błąd /zatrudnij: {str(e)}", ephemeral=True); print(f"Błąd w /zatrudnij: {e}"); traceback.print_exc()

@bot.tree.command(name="plus", description="Dodaje plus pracownikowi (+1/3, +2/3, +3/3)")
@app_commands.describe(member="Pracownik", powod="Powód (opcjonalny)")
@is_manager()
async def slash_plus(interaction: discord.Interaction, member: discord.Member, powod: Optional[str] = None):
    print(f"\n=== /plus | {interaction.user} -> {member} ===")
    await _dodaj_punkt_z_rolami(interaction, member, "plusy", powod)

@bot.tree.command(name="minus", description="Dodaje minus pracownikowi (-1/3, -2/3, -3/3)")
@app_commands.describe(member="Pracownik", powod="Powód (wymagany)")
@is_manager()
async def slash_minus(interaction: discord.Interaction, member: discord.Member, powod: str):
    print(f"\n=== /minus | {interaction.user} -> {member} ===")
    await _dodaj_punkt_z_rolami(interaction, member, "minusy", powod)

@bot.tree.command(name="upomnienie", description="Dodaje upomnienie pracownikowi (U1/3, U2/3, U3/3)")
@app_commands.describe(member="Pracownik", powod="Powód (wymagany)")
@is_manager()
async def slash_upomnienie(interaction: discord.Interaction, member: discord.Member, powod: str):
    print(f"\n=== /upomnienie | {interaction.user} -> {member} ===")
    await _dodaj_punkt_z_rolami(interaction, member, "upomnienia", powod)

@bot.tree.command(name="awansuj", description="Awansuje pracownika na wyższe stanowisko")
@app_commands.describe(member="Pracownik", sciezka="Ścieżka awansu", poziom="Poziom docelowy (1-6)")
@app_commands.choices(sciezka=SCIEZKI_WYBORY)
@is_manager()
async def slash_awansuj(interaction: discord.Interaction, member: discord.Member, sciezka: app_commands.Choice[str], poziom: app_commands.Range[int, 1, 6]):
    await interaction.response.defer()
    await _zmien_stanowisko(interaction, member, sciezka.value, poziom, None, czy_awans=True)

@bot.tree.command(name="degrad", description="Degraduje pracownika na niższe stanowisko")
@app_commands.describe(member="Pracownik", sciezka="Ścieżka", poziom="Poziom docelowy (1-5)", powod="Powód")
@app_commands.choices(sciezka=SCIEZKI_WYBORY)
@is_manager()
async def slash_degrad(interaction: discord.Interaction, member: discord.Member, sciezka: app_commands.Choice[str], poziom: app_commands.Range[int, 1, 5], powod: str):
    await interaction.response.defer()
    await _zmien_stanowisko(interaction, member, sciezka.value, poziom, powod, czy_awans=False)

@bot.tree.command(name="historia", description="Wyświetla historię pracownika (punkty, awanse, ostrzeżenia)")
@app_commands.describe(member="Pracownik (opcjonalnie - ty)")
async def slash_historia(interaction: discord.Interaction, member: Optional[discord.Member] = None):
    target_member = member or interaction.user
    # Sprawdzamy uprawnienia jeśli pytamy o kogoś innego
    if target_member.id != interaction.user.id and not _ma_wymagane_uprawnienia(interaction.user):
        await interaction.response.send_message("❌ Brak uprawnień do sprawdzania historii innych.", ephemeral=True); return

    if not interaction.guild_id: await interaction.response.send_message("Błąd: Brak ID serwera.", ephemeral=True); return
    await interaction.response.defer(ephemeral=True);
    guild_id = interaction.guild_id
    guild_data = get_guild_data(guild_id)
    member_id_str = str(target_member.id)

    if member_id_str not in guild_data:
         is_emp = False; user_role_ids={role.id for role in target_member.roles}; is_emp=any(rid in user_role_ids for rid in ROLE_PRACOWNICZE_WSZYSTKIE) if isinstance(target_member,discord.Member) else False
         msg = f"ℹ️ {target_member.mention} ma role, ale brak wpisu w bazie." if is_emp else f"❌ {target_member.mention} nie jest zatrudniony."; await interaction.followup.send(msg, ephemeral=True); return

    dane = guild_data[member_id_str]; embed = discord.Embed(title=f"📜 Historia: {dane.get('nazwa', target_member.display_name)}", color=discord.Color.blue())
    if isinstance(target_member, discord.Member): embed.set_thumbnail(url=target_member.display_avatar.url)
    embed.add_field(name="👤 Użytkownik", value=f"{target_member.mention} (`{target_member.id}`)", inline=False)
    embed.add_field(name=" Rola", value=dane.get("rola", "?"), inline=True); embed.add_field(name="📅 Zatrudniony", value=dane.get("data_zatrudnienia", "?"), inline=True)
    stats_value = f"⭐ Plusy: **{dane.get('plusy', 0)}**\n❌ Minusy: **{dane.get('minusy', 0)}**\n⚠️ Upomnienia: **{dane.get('upomnienia', 0)}**"; embed.add_field(name="📊 Punkty", value=stats_value, inline=False)
    hist_aw = dane.get("historia_awansow", []); hist_txt = "";
    if hist_aw:
        for wpis in reversed(hist_aw[-ITEMS_PER_PAGE:]): t=wpis.get('typ','z');e="⬆️" if t=="awans" else "⬇️" if t=="degradacja" else "🔄";p=f"\n *Powód: {wpis['powod']}*" if t=="degradacja" and wpis.get('powod') else ""; hist_txt+=f"{e} `{wpis.get('data','?')}`: **{wpis.get('rola','?')}** (*{wpis.get('awansujacy','?')}*){p}\n"
        if len(hist_aw) > ITEMS_PER_PAGE: hist_txt += f"*... ({len(hist_aw)} wpisów)*"
    embed.add_field(name=f"📈 Stanowiska (max {ITEMS_PER_PAGE})", value=hist_txt or "Brak", inline=False)
    ostrz = dane.get("ostrzezenia", []); ostrz_txt = ""
    if ostrz:
        for wpis in reversed(ostrz[-ITEMS_PER_PAGE:]): ostrz_txt += f"❗ `{wpis.get('data', '?')}`: **{wpis.get('powod', '?')}** (*{wpis.get('od', '?')}*)\n"
        if len(ostrz) > ITEMS_PER_PAGE: ostrz_txt += f"*... ({len(ostrz)} ostrzeżeń)*"
    embed.add_field(name=f"🚨 Ostrzeżenia (max {ITEMS_PER_PAGE})", value=ostrz_txt or "Brak", inline=False)
    await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="warn", description="Nadaje ostrzeżenie pracownikowi")
@app_commands.describe(member="Pracownik", powod="Powód ostrzeżenia")
@is_manager()
async def slash_warn(interaction: discord.Interaction, member: discord.Member, powod: str):
    if not interaction.guild_id: await interaction.response.send_message("Błąd: Brak ID serwera.", ephemeral=True); return
    await interaction.response.defer();
    guild_id = interaction.guild_id
    guild_data = get_guild_data(guild_id)
    member_id_str = str(member.id)

    if member_id_str not in guild_data: await interaction.followup.send(f"❌ {member.mention} brak w bazie.", ephemeral=True); return
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S"); ostrzezenie_data = {"data": now, "powod": powod, "od": str(interaction.user)}
    # Używamy setdefault, aby upewnić się, że lista istnieje przed dodaniem
    guild_data[member_id_str].setdefault("ostrzezenia", []).append(ostrzezenie_data)
    if not await zapisz_pracownikow(): await interaction.followup.send("⚠️ Błąd zapisu ostrzeżenia!", ephemeral=True)
    embed = discord.Embed(title="🚨 Ostrzeżenie", description=f"{member.mention} otrzymał ostrzeżenie.", color=discord.Color.orange()); embed.add_field(name="Powód", value=powod, inline=False); embed.add_field(name="Nadane przez", value=interaction.user.mention, inline=False); embed.add_field(name="Data", value=now, inline=False)
    await interaction.followup.send(embed=embed) # Publicznie
    await log_to_channel(bot, Kanaly.LOGI_HR, embed=embed.copy().add_field(name="Użytkownik", value=f"{member.mention} (`{member.id}`)", inline=False))

@bot.tree.command(name="zwolnij", description="Zwalnia pracownika (usuwa role i wpis z bazy)")
@app_commands.describe(member="Pracownik", powod="Powód zwolnienia")
@is_manager()
async def slash_zwolnij(interaction: discord.Interaction, member: discord.Member, powod: str):
    if not interaction.guild_id: await interaction.response.send_message("Błąd: Brak ID serwera.", ephemeral=True); return
    await interaction.response.defer();
    guild_id = interaction.guild_id
    guild_data = get_guild_data(guild_id)
    member_id_str = str(member.id)
    is_in_db = member_id_str in guild_data
    zwolniony_pracownik_data = guild_data.get(member_id_str, {})
    data_zwolnienia = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[Zwolnij] Start {member.name} (Guild: {guild_id}). W bazie: {is_in_db}")

    roles_removed_names = []; bot_top_role_pos = interaction.guild.me.top_role.position; roles_to_attempt_remove = []
    if isinstance(member, discord.Member):
        for role in member.roles:
            if role.id in ROLE_WSZYSTKIE_DO_USUNIECIA: # Usuwamy też role punktowe
                if role.position < bot_top_role_pos: roles_to_attempt_remove.append(role)
                else: print(f"[WARN Zwolnij] Hierarchia blokuje usunięcie '{role.name}'.")
        if roles_to_attempt_remove:
            try: await member.remove_roles(*roles_to_attempt_remove, reason=f"Zwolnienie przez {interaction.user}"); roles_removed_names = [r.name for r in roles_to_attempt_remove]; print(f"[Zwolnij] Usunięto role: {', '.join(roles_removed_names)}")
            except discord.Forbidden: await interaction.followup.send(f"❌ Bot nie ma uprawnień do usunięcia ról!", ephemeral=True) # Kontynuuj
            except Exception as e: await interaction.followup.send(f"❌ Błąd usuwania ról: {e}", ephemeral=True); traceback.print_exc() # Kontynuuj
    else: print(f"[WARN Zwolnij] Nie można usunąć ról - 'member' nie jest discord.Member.")

    final_message = ""
    if is_in_db:
        del guild_data[member_id_str] # Usuwamy z danych TEGO serwera
        if not await zapisz_pracownikow(): await interaction.followup.send("⚠️ KRYTYCZNY błąd usuwania z bazy!", ephemeral=True); return
        embed = discord.Embed(title="🚫 Zwolnienie pracownika", description=f"{member.mention} zwolniony z systemu.", color=discord.Color.red()); embed.add_field(name="Ostatnia rola (baza)", value=zwolniony_pracownik_data.get("rola", "?"), inline=False); embed.add_field(name="Zatrudniony (baza)", value=zwolniony_pracownik_data.get("data_zatrudnienia", "?"), inline=True); embed.add_field(name="Zwolniony", value=data_zwolnienia, inline=True); embed.add_field(name="Powód", value=powod, inline=False); embed.add_field(name="Przez", value=interaction.user.mention, inline=False);
        if roles_removed_names: embed.add_field(name="Usunięte role", value=", ".join(roles_removed_names), inline=False)
        embed.set_footer(text=f"ID: {member_id_str}"); await interaction.followup.send(embed=embed); final_message = embed.description
    else:
        if roles_removed_names: final_message = f"ℹ️ {member.mention} nie był w bazie, usunięto role: {', '.join(roles_removed_names)}."
        else: final_message = f"❌ {member.mention} nie jest zatrudniony."; await interaction.followup.send(final_message, ephemeral=True); return
        await interaction.followup.send(final_message)
    await log_to_channel(bot, Kanaly.LOGI_HR, message=f"🚪 {interaction.user.mention} zwolnił: {final_message.replace(f'{member.mention}', f'**{member.display_name}** (`{member.id}`)')} | Powód: {powod}")

@bot.tree.command(name="lista_pracownikow", description="Wyświetla listę pracowników na tym serwerze (stronnicowana)")
@is_manager()
async def slash_lista_pracownikow(interaction: discord.Interaction):
    if not interaction.guild_id: await interaction.response.send_message("Błąd: Brak ID serwera.", ephemeral=True); return
    await interaction.response.defer(ephemeral=True)
    guild_id = interaction.guild_id
    guild_data = get_guild_data(guild_id)

    if not guild_data: await interaction.followup.send("📋 Lista pracowników dla tego serwera jest pusta.", ephemeral=True); return
    try: sorted_pracownicy = sorted(guild_data.items(), key=lambda item: item[1].get('nazwa', 'ZZZ'))
    except Exception as e: print(f"[ERROR] Błąd sortowania listy: {e}"); await interaction.followup.send("❌ Błąd sortowania listy.", ephemeral=True); return

    embeds = []; current_page_items = 0; current_description = ""
    for pracownik_id, dane in sorted_pracownicy:
        nazwa=dane.get('nazwa',f"ID:{pracownik_id}");rola=dane.get('rola','?');p,m,u=dane.get('plusy',0),dane.get('minusy',0),dane.get('upomnienia',0);data_zatr=dane.get('data_zatrudnienia','?')
        entry = f"**• {nazwa}** (`{pracownik_id}`)\n Rola:{rola} | 📊 P:{p} M:{m} U:{u} | 📅 Zatrudniony:{data_zatr}\n"
        if len(current_description)+len(entry)>4000 or current_page_items>=ITEMS_PER_PAGE*2:
            if current_description: embed=discord.Embed(title=f"📋 Lista pracowników ({interaction.guild.name})",description=current_description,color=discord.Color.blue()); embeds.append(embed)
            current_description = ""; current_page_items = 0
        current_description += entry; current_page_items += 1
    if current_description: embed=discord.Embed(title=f"📋 Lista pracowników ({interaction.guild.name})",description=current_description,color=discord.Color.blue()); embeds.append(embed)
    if not embeds: await interaction.followup.send("Nie wygenerowano listy.", ephemeral=True); return
    total_pages = len(embeds)
    for i, embed in enumerate(embeds): embed.set_footer(text=f"Strona {i+1}/{total_pages} | Łącznie: {len(guild_data)} pracowników")
    await interaction.followup.send(embed=embeds[0], ephemeral=True)
    for embed in embeds[1:]: await interaction.followup.send(embed=embed, ephemeral=True)


@bot.tree.command(name="test_uprawnienia", description="Testuje uprawnienia zarządzające użytkownika")
@app_commands.describe(member="Użytkownik do sprawdzenia (domyślnie ty)")
async def slash_test_uprawnienia(interaction: discord.Interaction, member: Optional[discord.Member] = None):
    target_member = member or interaction.user; await interaction.response.defer(ephemeral=True)
    if not isinstance(target_member, discord.Member): await interaction.followup.send("Błąd: Nie można sprawdzić.", ephemeral=True); return
    has_permission = _ma_wymagane_uprawnienia(target_member)
    user_roles_str = "\n".join([f"- {role.name} (`{role.id}`)" for role in target_member.roles]) or "Brak ról"
    managing_roles_str = "\n".join([f"- ... (`{role_id}`)" for role_id in ROLE_ZARZADZAJACE]) # Uproszczone
    response = (f"📊 Raport uprawnień dla {target_member.mention} (`{target_member.id}`)\n\n"
                f"🔑 Upr. zarządzające? {'✅ Tak' if has_permission else '❌ Nie'}\n"
                f"👑 Admin serwera? {'✅ Tak' if target_member.guild_permissions.administrator else '❌ Nie'}\n\n"
                f"👤 Role:\n{user_roles_str}\n\n"
                f"📜 Wymagane role zarządzające (ID):\n{managing_roles_str}")
    if len(response) > 1950: response = response[:1950] + "..."
    await interaction.followup.send(response, ephemeral=True)

@bot.tree.command(name="sprawdz_role", description="Wyświetla ID wszystkich ról na serwerze")
@is_manager()
async def slash_sprawdz_role(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True); sorted_roles = sorted(interaction.guild.roles, key=lambda r: r.position, reverse=True)
    response = "📋 Lista ról na serwerze (od najwyższej):\n\n"; response += "\n".join([f"• {role.name}: `{role.id}` (Poz: {role.position})" for role in sorted_roles])
    if len(response) > 1900:
        parts = [response[i:i+1900] for i in range(0, len(response), 1900)];
        for part in parts: await interaction.followup.send(part, ephemeral=True)
    else: await interaction.followup.send(response, ephemeral=True)

# Komenda tylko dla właściciela do debugowania synchronizacji
@bot.tree.command(name="force_sync", description="[Właściciel] Czyści i synchronizuje komendy dla TEGO serwera.")
# Usunięto @app_commands.guilds - komenda będzie globalna, ale zadziała tylko na skonfigurowanych serwerach po sprawdzeniu ID wewnątrz
async def force_sync(interaction: discord.Interaction):
    # !!! WAŻNE: Wstaw tutaj SWOJE ID użytkownika Discord !!!
    owner_id = 377376144879648768 # <-- ZASTĄP TĄ LICZBĘ SWOIM ID!

    if interaction.user.id != owner_id:
        await interaction.response.send_message("❌ Tylko właściciel bota może tego użyć.", ephemeral=True)
        return

    # Sprawdź czy komenda jest wywołana na jednym ze skonfigurowanych serwerów
    if interaction.guild_id not in GUILD_IDS_LIST:
         await interaction.response.send_message("❌ Tej komendy synchronizacji można użyć tylko na skonfigurowanym serwerze.", ephemeral=True)
         return

    await interaction.response.defer(ephemeral=True, thinking=True)
    try:
        guild_id = interaction.guild_id
        guild_obj = discord.Object(id=guild_id)

        print(f"[SYNC MANUAL] Rozpoczynam czyszczenie komend dla serwera {guild_id}...")
        bot.tree.clear_commands(guild=guild_obj)
        await bot.tree.sync(guild=guild_obj)
        print(f"[SYNC MANUAL] Wyczyszczono komendy dla serwera {guild_id}.")

        print(f"[SYNC MANUAL] Rozpoczynam ponowną synchronizację dla serwera {guild_id}...")
        await bot.tree.sync(guild=guild_obj)
        print(f"[SYNC MANUAL] Zsynchronizowano komendy dla serwera {guild_id}.")

        await interaction.followup.send("✅ Komendy na tym serwerze zostały wyczyszczone i ponownie zsynchronizowane!", ephemeral=True)
    except Exception as e:
        print(f"[ERROR SYNC MANUAL] Błąd podczas ręcznej synchronizacji: {e}")
        traceback.print_exc()
        await interaction.followup.send(f"❌ Wystąpił błąd podczas synchronizacji: {e}", ephemeral=True)

# --- Uruchomienie Bota ---
if __name__ == "__main__":
    discord_token = os.getenv('DISCORD_TOKEN')
    if not discord_token: print("BŁĄD KRYTYCZNY: Brak DISCORD_TOKEN w .env!")
    else:
        try: bot.run(discord_token)
        except discord.errors.LoginFailure: print("BŁĄD KRYTYCZNY: Nieprawidłowy token.")
        except Exception as e: print(f"BŁĄD KRYTYCZNY startu: {e}"); traceback.print_exc()
