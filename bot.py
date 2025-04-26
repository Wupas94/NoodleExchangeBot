import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import asyncio
import traceback
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

# --- Stałe i Konfiguracja ---
load_dotenv()
JSON_FILE = "pracownicy.json"
ITEMS_PER_PAGE = 10
GUILD_ID = 1021373051272704130  # ID serwera na którym jest bot
GUILD_IDS = [GUILD_ID]  # Lista ID serwerów, na których bot ma działać

# --- Role IDs ---
class Role:
    # Role bazowe
    REKRUT = 1119626832262738000
    PRACOWNIK = 1021384419740753970
    OCHRONA = 1022826867960582204
    
    # Role zarządzające
    NADZOR_PRACY = 1031216295905079336
    WLASCICIEL_FIRMY = 1021376435530760233
    ZASTEPCA_SZEFA = 1094378926333243434
    MENADZER = 1021687974104141864
    KIEROWNIK = 1322094531302395935
    ASYSTENT_KIEROWNIKA = 1359944124932948111
    TECHNIK = 1364712468680806532  # TODO: Wstaw ID
    NADZOR_OCHRONY = 1283101978129469515
    SZEF_OCHRONY = 1022827507302543450
    ZASTEPCA_SZEFA_OCHRONY = 1107424252824653834
    ASYSTENT_SZEFA_OCHRONY = 1343271396737945600
    EGZAMINATOR_OCHRONY = 1343272656602005524
    SZKOLENIOWIEC_OCHRONY = 1343272696233857106
    
    # Role punktowe
    PLUS1 = 1125425345433194506
    PLUS2 = 1125425435535212544
    PLUS3 = 1125425499980709909
    MINUS1 = 1021686482236354590
    MINUS2 = 1021687044793188372
    MINUS3 = 1021687258815922230
    UPOMNIENIE1 = 1292900587868000287
    UPOMNIENIE2 = 1292900582192840856
    UPOMNIENIE3 = 1292900560093188096
    
    # Role ścieżki ochrony
    MLODSZY_OCHRONIARZ = 1118302455013322923
    OCHRONIARZ = 1118303102618046505
    OCHRONIARZ_LICENCJONOWANY = 1259930187232051283
    DOSWIADCZONY_OCHRONIARZ = 1283104620658556948
    STARSZY_OCHRONIARZ = 1283104625037279296
    PIES_OCHRONY = 1270883261458939975
    
    # Role ścieżki gastronomii
    KELNER = 1119627033589338183
    ASYSTENT_KUCHARZA = 1119627348074045512
    KUCHARZ = 1119627473634734220
    SZEF_KUCHNI = 1166755931015622737
    OBSLUGA_BARU = 1335274785541722143

# --- Ścieżki awansu i mapowanie ---
SCIEZKA_OCHRONY = [Role.REKRUT, Role.MLODSZY_OCHRONIARZ, Role.OCHRONIARZ, Role.OCHRONIARZ_LICENCJONOWANY, Role.DOSWIADCZONY_OCHRONIARZ, Role.STARSZY_OCHRONIARZ]
SCIEZKA_GASTRONOMII = [Role.REKRUT, Role.KELNER, Role.ASYSTENT_KUCHARZA, Role.KUCHARZ, Role.SZEF_KUCHNI, Role.OBSLUGA_BARU]
SCIEZKA_ZARZADU = [Role.REKRUT, Role.PRACOWNIK, Role.ASYSTENT_KIEROWNIKA, Role.KIEROWNIK, Role.MENADZER, Role.ZASTEPCA_SZEFA]
SCIEZKA_ZARZADU_OCHRONY = [Role.OCHRONA, Role.SZKOLENIOWIEC_OCHRONY, Role.EGZAMINATOR_OCHRONY, Role.ASYSTENT_SZEFA_OCHRONY, Role.ZASTEPCA_SZEFA_OCHRONY, Role.SZEF_OCHRONY]
SCIEZKI_MAP = {"ochrona": SCIEZKA_OCHRONY, "gastronomia": SCIEZKA_GASTRONOMII, "zarząd": SCIEZKA_ZARZADU, "zarzad_ochrony": SCIEZKA_ZARZADU_OCHRONY}
SCIEZKI_WYBORY = [app_commands.Choice(name=n.replace('_',' ').title(), value=n) for n in SCIEZKI_MAP.keys()] # Dynamiczne generowanie choices

# --- Role Groups ---
ROLE_ZARZADZAJACE = [Role.NADZOR_PRACY, Role.WLASCICIEL_FIRMY, Role.ZASTEPCA_SZEFA, Role.MENADZER, Role.KIEROWNIK, Role.ASYSTENT_KIEROWNIKA, Role.TECHNIK, Role.NADZOR_OCHRONY, Role.SZEF_OCHRONY, Role.ZASTEPCA_SZEFA_OCHRONY, Role.ASYSTENT_SZEFA_OCHRONY, Role.EGZAMINATOR_OCHRONY, Role.SZKOLENIOWIEC_OCHRONY]
ROLE_PRACOWNICZE_WSZYSTKIE = list(set([role_id for role_id in (ROLE_ZARZADZAJACE + [Role.REKRUT, Role.PRACOWNIK, Role.OCHRONA] + SCIEZKA_OCHRONY + SCIEZKA_GASTRONOMII + SCIEZKA_ZARZADU + SCIEZKA_ZARZADU_OCHRONY) if role_id is not None]))
ROLE_PUNKTOWE = [Role.PLUS1, Role.PLUS2, Role.PLUS3, Role.MINUS1, Role.MINUS2, Role.MINUS3, Role.UPOMNIENIE1, Role.UPOMNIENIE2, Role.UPOMNIENIE3]
ROLE_WSZYSTKIE_DO_USUNIECIA = set(ROLE_PRACOWNICZE_WSZYSTKIE + ROLE_PUNKTOWE)

# --- Mapowanie Punktów na Role Poziomowe ---
POINT_ROLE_LEVELS_MAP = {
    "plusy": {1: Role.PLUS1, 2: Role.PLUS2, 3: Role.PLUS3},
    "minusy": {1: Role.MINUS1, 2: Role.MINUS2, 3: Role.MINUS3},
    "upomnienia": {1: Role.UPOMNIENIE1, 2: Role.UPOMNIENIE2, 3: Role.UPOMNIENIE3}
}

# --- Kanały Logowania ---
class Kanaly:
    # TODO: Wstaw prawdziwe ID kanałów
    LOGI_HR = 1234567890
    LOGI_PUNKTY = 1234567890
    LOGI_AWANSE = 1234567890

# --- Słownik pracowników i Lock ---
pracownicy = {}
json_lock = asyncio.Lock() 

# --- Funkcje Pomocnicze (JSON, Uprawnienia, Logowanie) ---
async def zapisz_pracownikow():
    async with json_lock:
        try:
            with open(JSON_FILE, 'w', encoding='utf-8') as f: json.dump(pracownicy, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e: print(f"[ERROR] Błąd zapisywania {JSON_FILE}: {str(e)}"); traceback.print_exc(); return False

async def wczytaj_pracownikow():
    global pracownicy
    async with json_lock:
        try:
            if os.path.exists(JSON_FILE):
                with open(JSON_FILE, 'r', encoding='utf-8') as f: pracownicy = json.load(f)
                print(f"[INFO] Wczytano dane {len(pracownicy)} pracowników z {JSON_FILE}")
            else: print(f"[INFO] Plik {JSON_FILE} nie istnieje, inicjuję pustą bazę."); pracownicy = {}
            return True
        except json.JSONDecodeError as e:
            print(f"[ERROR] Błąd dekodowania JSON {JSON_FILE}: {str(e)}"); print(f"[WARN] Tworzę backup i inicjuję pustą bazę.")
            try: os.rename(JSON_FILE, f"{JSON_FILE}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            except OSError as os_err: print(f"[ERROR] Nie udało się utworzyć backupu: {os_err}")
            pracownicy = {}; return False
        except Exception as e: print(f"[ERROR] Inny błąd wczytywania {JSON_FILE}: {str(e)}"); traceback.print_exc(); pracownicy = {}; return False

def _ma_wymagane_uprawnienia(member: discord.Member) -> bool:
    if not member or not isinstance(member, discord.Member): return False
    if member.guild_permissions.administrator: return True
    user_role_ids = {role.id for role in member.roles}
    return any(role_id in user_role_ids for role_id in ROLE_ZARZADZAJACE)

def is_manager():
    async def predicate(interaction: discord.Interaction) -> bool:
        allowed = _ma_wymagane_uprawnienia(interaction.user)
        if not allowed: await interaction.response.send_message("❌ Nie masz uprawnień do użycia tej komendy!", ephemeral=True)
        return allowed
    return app_commands.check(predicate)

def czy_jest_zatrudniony(member: discord.Member) -> bool:
    if not member or not isinstance(member, discord.Member): return False
    if str(member.id) in pracownicy: return True
    user_role_ids = {role.id for role in member.roles}
    return any(role_id in user_role_ids for role_id in ROLE_PRACOWNICZE_WSZYSTKIE)

async def log_to_channel(bot_instance: commands.Bot, channel_id: int, message: str = None, embed: discord.Embed = None):
    if not channel_id or channel_id == 1234567890: return
    channel = bot_instance.get_channel(channel_id)
    if not isinstance(channel, discord.TextChannel): print(f"[ERROR LOG] Kanał {channel_id} nie jest tekstowy."); return
    try: await channel.send(content=message, embed=embed)
    except discord.Forbidden: print(f"[ERROR LOG] Brak uprawnień do pisania na kanale {channel_id}.")
    except Exception as e: print(f"[ERROR LOG] Błąd wysyłania logu na {channel_id}: {e}"); traceback.print_exc() 

# --- Funkcja Punktów (Wersja z Rolami Poziomowymi v2) ---
async def dodaj_punkt_z_rolami_v2(interaction: discord.Interaction, member: discord.Member, typ: str, powod: Optional[str] = None) -> bool:
    """Zarządza punktami i rolami poziomowymi 1/3, 2/3, 3/3."""
    try:
        member_id_str = str(member.id)
        log_prefix = f"[DEBUG RolePointsV2][{typ}][{member.name}]"
        print(f"{log_prefix} Rozpoczęto.")

        if not interaction.response.is_done(): await interaction.response.defer(ephemeral=False)

        if member_id_str not in pracownicy:
            await interaction.followup.send(f"❌ {member.mention} nie jest zarejestrowany (/job).", ephemeral=True); return False

        level_role_ids = POINT_ROLE_LEVELS_MAP.get(typ)
        if not level_role_ids:
            print(f"{log_prefix} BŁĄD: Nieznany typ punktu: {typ}"); await interaction.followup.send(f"❌ Błąd wewnętrzny.", ephemeral=True); return False

        roles, missing_roles_info, hierarchy_ok = {}, [], True
        bot_member = interaction.guild.me; bot_top_role_pos = bot_member.top_role.position
        print(f"{log_prefix} Pozycja bota ({bot_member.top_role.name}): {bot_top_role_pos}")

        for level, role_id in level_role_ids.items():
            role = interaction.guild.get_role(role_id); roles[level] = role
            if role is None: print(f"{log_prefix} BŁĄD: Rola Poziom {level} (ID: {role_id}) NIE ZNALEZIONA!"); missing_roles_info.append(f"Poziom {level} (ID: {role_id})")
            else:
                print(f"{log_prefix} Rola Poziom {level}: '{role.name}' (Poz: {role.position})")
                if role.position >= bot_top_role_pos: print(f"{log_prefix} BŁĄD HIERARCHII: Rola '{role.name}' >= bot!"); hierarchy_ok = False

        if missing_roles_info: await interaction.followup.send(f"❌ Błąd Konfiguracji: Brakujące role dla '{typ}': {', '.join(missing_roles_info)}!", ephemeral=True); return False
        if not hierarchy_ok: await interaction.followup.send(f"❌ Błąd Hierarchii: Rola bota ({bot_member.top_role.name}) jest zbyt nisko!", ephemeral=True); return False
        if not bot_member.guild_permissions.manage_roles: await interaction.followup.send("❌ Bot nie ma uprawnień 'Zarządzanie Rolami'!", ephemeral=True); return False
        print(f"{log_prefix} Walidacja ról i hierarchii OK.")

        current_level, current_role_obj = 0, None
        user_roles_set = {r.id for r in member.roles}
        for level in [3, 2, 1]:
            role_obj = roles.get(level)
            if role_obj and role_obj.id in user_roles_set: current_level, current_role_obj = level, role_obj; break
        print(f"{log_prefix} Aktualny poziom: {current_level}")

        new_level = current_level + 1
        osiagnieto_limit = new_level > 3
        role_to_remove, role_to_add = current_role_obj, roles.get(new_level) if not osiagnieto_limit else None
        final_level_in_db = 0 if osiagnieto_limit else new_level
        print(f"{log_prefix} Nowy poziom: {new_level}, Limit?: {osiagnieto_limit}, Usuń: {role_to_remove}, Dodaj: {role_to_add}")

        role_action_success = True
        reason = f"Punkt {typ} ({new_level if not osiagnieto_limit else 'LIMIT'}) przez {interaction.user}"
        try:
            current_user_roles_set = {r.id for r in member.roles} # Odśwież role użytkownika
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
            pracownicy[member_id_str][typ] = final_level_in_db
            print(f"{log_prefix} Zapisuję poziom {final_level_in_db} do bazy.")
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
        log_msg = f"{emoji} `{datetime.now().strftime('%H:%M')}` {interaction.user.mention} -> {member.mention} ({typ} {new_level if not osiagnieto_limit else 'LIMIT/RESET'}). Powód: {powod or '-'}. {role_change_info}"
        await log_to_channel(bot, Kanaly.LOGI_PUNKTY, message=log_msg)
        return osiagnieto_limit

    except Exception as e:
        print(f"[ERROR KRYTYCZNY] {log_prefix} Nieoczekiwany błąd w głównej funkcji:"); traceback.print_exc()
        try:
            if interaction.response.is_done(): await interaction.followup.send(f"Wystąpił krytyczny błąd: {e}", ephemeral=True)
        except Exception as e2: print(f"[ERROR Handler] Nie można wysłać wiad. o błędzie krytycznym: {e2}")
        return False

# --- Funkcje pomocnicze ---
def load_json():
    try:
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        print(f"BŁĄD: Nieprawidłowy format pliku {JSON_FILE}")
        return {}

def save_json(data):
    try:
        with open(JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"BŁĄD zapisu do {JSON_FILE}: {e}")

def get_user_data(user_id: str) -> dict:
    data = load_json()
    if user_id not in data:
        data[user_id] = {
            "points": 0,
            "history": [],
            "current_role": None,
            "warnings": []
        }
        save_json(data)
    return data[user_id]

def update_user_data(user_id: str, updates: dict):
    data = load_json()
    if user_id not in data:
        data[user_id] = {
            "points": 0,
            "history": [],
            "current_role": None,
            "warnings": []
        }
    data[user_id].update(updates)
    save_json(data)

def can_manage_points(interaction: discord.Interaction) -> bool:
    required_roles = [
        Role.NADZOR_PRACY,
        Role.WLASCICIEL_FIRMY,
        Role.ZASTEPCA_SZEFA,
        Role.MENADZER,
        Role.KIEROWNIK,
        Role.ASYSTENT_KIEROWNIKA,
        Role.TECHNIK,
        Role.NADZOR_OCHRONY,
        Role.SZEF_OCHRONY,
        Role.ZASTEPCA_SZEFA_OCHRONY,
        Role.ASYSTENT_SZEFA_OCHRONY,
        Role.EGZAMINATOR_OCHRONY,
        Role.SZKOLENIOWIEC_OCHRONY
    ]
    return any(role and role in [r.id for r in interaction.user.roles] for role in required_roles)

def can_manage_roles(interaction: discord.Interaction) -> bool:
    required_roles = [
        Role.NADZOR_PRACY,
        Role.WLASCICIEL_FIRMY,
        Role.ZASTEPCA_SZEFA,
        Role.MENADZER,
        Role.KIEROWNIK,
        Role.ASYSTENT_KIEROWNIKA,
        Role.TECHNIK,
        Role.NADZOR_OCHRONY,
        Role.SZEF_OCHRONY,
        Role.ZASTEPCA_SZEFA_OCHRONY,
        Role.ASYSTENT_SZEFA_OCHRONY,
        Role.EGZAMINATOR_OCHRONY,
        Role.SZKOLENIOWIEC_OCHRONY
    ]
    return any(role and role in [r.id for r in interaction.user.roles] for role in required_roles)

def log_action(interaction: discord.Interaction, action: str, target: discord.Member, details: str = ""):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_data = get_user_data(str(target.id))
    user_data["history"].append({
        "timestamp": timestamp,
        "action": action,
        "by": str(interaction.user),
        "details": details
    })
    update_user_data(str(target.id), user_data)

# --- Konfiguracja Bota ---
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

class NoodleExchangeBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        
    async def setup_hook(self):
        await self.tree.sync(guild=discord.Object(id=GUILD_ID))
        
    async def on_ready(self):
        print(f"Zalogowano jako {self.user}")
        print("Bot jest gotowy!")

bot = NoodleExchangeBot()

# --- Komendy Slash ---

@bot.tree.command(name="test", description="Testowa komenda")
async def test(interaction: discord.Interaction):
    await interaction.response.send_message("Bot działa!", ephemeral=True)

@bot.tree.command(name="job", description="Przypisz pracę pracownikowi")
@app_commands.checks.has_permissions(manage_roles=True)
async def job(interaction: discord.Interaction, user: discord.Member, job: str):
    if not can_manage_roles(interaction):
        await interaction.response.send_message("❌ Brak uprawnień do przypisywania pracy.", ephemeral=True)
        return

    job = job.lower()
    if job not in ["ochrona", "gastronomia", "zarząd"]:
        await interaction.response.send_message("❌ Nieprawidłowa ścieżka kariery. Wybierz: ochrona, gastronomia lub zarząd.", ephemeral=True)
        return

    user_data = get_user_data(str(user.id))
    current_role = user_data.get("current_role")
    
    if current_role:
        await interaction.response.send_message(f"❌ {user.mention} ma już przypisaną ścieżkę kariery.", ephemeral=True)
        return

    new_role = None
    if job == "ochrona":
        new_role = Role.REKRUT
    elif job == "gastronomia":
        new_role = Role.REKRUT
    elif job == "zarząd":
        new_role = Role.REKRUT

    if new_role:
        role = interaction.guild.get_role(new_role)
        if role:
            await user.add_roles(role)
            update_user_data(str(user.id), {"current_role": new_role})
            log_action(interaction, "Przypisano pracę", user, f"Ścieżka: {job}")
            await interaction.response.send_message(f"✅ Przypisano {user.mention} do ścieżki {job}.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Nie znaleziono roli.", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Wystąpił błąd podczas przypisywania roli.", ephemeral=True)

@bot.tree.command(name="plus", description="Dodaj punkty pracownikowi")
async def plus(interaction: discord.Interaction, user: discord.Member, amount: int, reason: str):
    if not can_manage_points(interaction):
        await interaction.response.send_message("❌ Brak uprawnień do dodawania punktów.", ephemeral=True)
        return

    if amount <= 0:
        await interaction.response.send_message("❌ Liczba punktów musi być większa od 0.", ephemeral=True)
        return

    user_data = get_user_data(str(user.id))
    current_points = user_data.get("points", 0)
    new_points = current_points + amount

    update_user_data(str(user.id), {"points": new_points})
    log_action(interaction, "Dodano punkty", user, f"Liczba: +{amount}, Powód: {reason}")

    await interaction.response.send_message(f"✅ Dodano {amount} punktów dla {user.mention}. Nowa suma: {new_points}", ephemeral=True)

@bot.tree.command(name="minus", description="Odejmij punkty pracownikowi")
async def minus(interaction: discord.Interaction, user: discord.Member, amount: int, reason: str):
    if not can_manage_points(interaction):
        await interaction.response.send_message("❌ Brak uprawnień do odejmowania punktów.", ephemeral=True)
        return

    if amount <= 0:
        await interaction.response.send_message("❌ Liczba punktów musi być większa od 0.", ephemeral=True)
        return

    user_data = get_user_data(str(user.id))
    current_points = user_data.get("points", 0)
    new_points = max(0, current_points - amount)

    update_user_data(str(user.id), {"points": new_points})
    log_action(interaction, "Odejmowano punkty", user, f"Liczba: -{amount}, Powód: {reason}")

    await interaction.response.send_message(f"✅ Odejmowano {amount} punktów od {user.mention}. Nowa suma: {new_points}", ephemeral=True)

@bot.tree.command(name="upomnienie", description="Dodaj upomnienie pracownikowi")
async def upomnienie(interaction: discord.Interaction, user: discord.Member, reason: str):
    if not can_manage_points(interaction):
        await interaction.response.send_message("❌ Brak uprawnień do dodawania upomnień.", ephemeral=True)
        return

    user_data = get_user_data(str(user.id))
    warnings = user_data.get("warnings", [])
    warnings.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "reason": reason,
        "by": str(interaction.user)
    })

    update_user_data(str(user.id), {"warnings": warnings})
    log_action(interaction, "Dodano upomnienie", user, f"Powód: {reason}")

    await interaction.response.send_message(f"✅ Dodano upomnienie dla {user.mention}. Powód: {reason}", ephemeral=True)

@bot.tree.command(name="awansuj", description="Awansuj pracownika na wyższe stanowisko")
async def awansuj(interaction: discord.Interaction, user: discord.Member, sciezka: str, poziom: int, powod: Optional[str] = None):
    if not can_manage_roles(interaction):
        await interaction.response.send_message("❌ Brak uprawnień do awansowania.", ephemeral=True)
        return

    sciezka = sciezka.lower()
    if sciezka not in ["ochrona", "gastronomia", "zarząd"]:
        await interaction.response.send_message("❌ Nieprawidłowa ścieżka kariery.", ephemeral=True)
        return

    sciezki_map = {
        "ochrona": SCIEZKA_OCHRONY,
        "gastronomia": SCIEZKA_GASTRONOMII,
        "zarząd": SCIEZKA_ZARZADU
    }

    sciezka_awansu = sciezki_map[sciezka]
    if poziom < 1 or poziom > len(sciezka_awansu):
        await interaction.response.send_message(f"❌ Nieprawidłowy poziom. Dostępne poziomy: 1-{len(sciezka_awansu)}", ephemeral=True)
        return

    user_data = get_user_data(str(user.id))
    current_role = user_data.get("current_role")
    if not current_role:
        await interaction.response.send_message("❌ Pracownik nie ma przypisanej ścieżki kariery.", ephemeral=True)
        return

    new_role_id = sciezka_awansu[poziom - 1]
    new_role = interaction.guild.get_role(new_role_id)
    if not new_role:
        await interaction.response.send_message("❌ Nie znaleziono roli dla wybranego poziomu.", ephemeral=True)
        return

    try:
        await user.add_roles(new_role)
        update_user_data(str(user.id), {"current_role": new_role_id})
        log_action(interaction, "Awans", user, f"Ścieżka: {sciezka}, Poziom: {poziom}, Powód: {powod}")
        await interaction.response.send_message(f"✅ Pomyślnie awansowano {user.mention} na {new_role.name}!", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("❌ Bot nie ma uprawnień do nadawania ról.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Wystąpił błąd podczas awansowania: {str(e)}", ephemeral=True)

@bot.tree.command(name="degrad", description="Degraduje pracownika na niższe stanowisko")
async def degrad(interaction: discord.Interaction, user: discord.Member, sciezka: str, poziom: int, powod: str):
    if not can_manage_roles(interaction):
        await interaction.response.send_message("❌ Brak uprawnień do degradowania.", ephemeral=True)
        return

    sciezka = sciezka.lower()
    if sciezka not in ["ochrona", "gastronomia", "zarząd"]:
        await interaction.response.send_message("❌ Nieprawidłowa ścieżka kariery.", ephemeral=True)
        return

    sciezki_map = {
        "ochrona": SCIEZKA_OCHRONY,
        "gastronomia": SCIEZKA_GASTRONOMII,
        "zarząd": SCIEZKA_ZARZADU
    }

    sciezka_awansu = sciezki_map[sciezka]
    if poziom < 1 or poziom > len(sciezka_awansu):
        await interaction.response.send_message(f"❌ Nieprawidłowy poziom. Dostępne poziomy: 1-{len(sciezka_awansu)}", ephemeral=True)
        return

    user_data = get_user_data(str(user.id))
    current_role = user_data.get("current_role")
    if not current_role:
        await interaction.response.send_message("❌ Pracownik nie ma przypisanej ścieżki kariery.", ephemeral=True)
        return

    new_role_id = sciezka_awansu[poziom - 1]
    new_role = interaction.guild.get_role(new_role_id)
    if not new_role:
        await interaction.response.send_message("❌ Nie znaleziono roli dla wybranego poziomu.", ephemeral=True)
        return

    try:
        await user.add_roles(new_role)
        update_user_data(str(user.id), {"current_role": new_role_id})
        log_action(interaction, "Degradacja", user, f"Ścieżka: {sciezka}, Poziom: {poziom}, Powód: {powod}")
        await interaction.response.send_message(f"✅ Pomyślnie zdegradowano {user.mention} na {new_role.name}!", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("❌ Bot nie ma uprawnień do nadawania ról.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Wystąpił błąd podczas degradowania: {str(e)}", ephemeral=True)

@bot.tree.command(name="historia", description="Wyświetla historię pracownika")
async def historia(interaction: discord.Interaction, user: discord.Member):
    user_data = get_user_data(str(user.id))
    if not user_data:
        await interaction.response.send_message("❌ Nie znaleziono danych dla tego pracownika.", ephemeral=True)
        return

    history = user_data.get("history", [])
    if not history:
        await interaction.response.send_message(f"ℹ️ Brak historii dla {user.mention}", ephemeral=True)
        return

    response = f"📜 Historia {user.mention}:\n\n"
    for entry in history[-10:]:  # Show last 10 entries
        response += f"• {entry['timestamp']} - {entry['action']}"
        if entry.get('details'):
            response += f": {entry['details']}"
        response += "\n"

    if len(response) > 2000:
        parts = [response[i:i+1900] for i in range(0, len(response), 1900)]
        await interaction.response.send_message(parts[0], ephemeral=True)
        for part in parts[1:]:
            await interaction.followup.send(part, ephemeral=True)
    else:
        await interaction.response.send_message(response, ephemeral=True)

@bot.tree.command(name="warn", description="Dodaje ostrzeżenie pracownikowi")
async def warn(interaction: discord.Interaction, user: discord.Member, powod: str):
    if not can_manage_points(interaction):
        await interaction.response.send_message("❌ Brak uprawnień do dodawania ostrzeżeń.", ephemeral=True)
        return

    user_data = get_user_data(str(user.id))
    warnings = user_data.get("warnings", [])
    warnings.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "reason": powod,
        "by": str(interaction.user)
    })

    update_user_data(str(user.id), {"warnings": warnings})
    log_action(interaction, "Dodano ostrzeżenie", user, f"Powód: {powod}")

    await interaction.response.send_message(f"⚠️ Dodano ostrzeżenie dla {user.mention}. Powód: {powod}", ephemeral=True)

@bot.tree.command(name="zwolnij", description="Zwolnij pracownika")
async def zwolnij(interaction: discord.Interaction, user: discord.Member, powod: str):
    if not can_manage_roles(interaction):
        await interaction.response.send_message("❌ Brak uprawnień do zwalniania pracowników.", ephemeral=True)
        return

    user_data = get_user_data(str(user.id))
    if not user_data:
        await interaction.response.send_message("❌ Nie znaleziono danych dla tego pracownika.", ephemeral=True)
        return

    try:
        # Remove all roles
        await user.remove_roles(*user.roles)
        log_action(interaction, "Zwolnienie", user, f"Powód: {powod}")
        await interaction.response.send_message(f"✅ Pomyślnie zwolniono {user.mention}. Powód: {powod}", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("❌ Bot nie ma uprawnień do usuwania ról.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Wystąpił błąd podczas zwalniania: {str(e)}", ephemeral=True)

@bot.tree.command(name="lista_pracownikow", description="Wyświetla listę pracowników")
async def lista_pracownikow(interaction: discord.Interaction):
    data = load_json()
    if not data:
        await interaction.response.send_message("ℹ️ Brak pracowników w systemie.", ephemeral=True)
        return

    response = "📋 Lista pracowników:\n\n"
    for user_id, user_data in data.items():
        user = interaction.guild.get_member(int(user_id))
        if user:
            response += f"• {user.mention} - Punkty: {user_data.get('points', 0)}\n"

    if len(response) > 2000:
        parts = [response[i:i+1900] for i in range(0, len(response), 1900)]
        await interaction.response.send_message(parts[0], ephemeral=True)
        for part in parts[1:]:
            await interaction.followup.send(part, ephemeral=True)
    else:
        await interaction.response.send_message(response, ephemeral=True)

@bot.tree.command(name="test_uprawnienia", description="Testuje uprawnienia użytkownika")
async def test_uprawnienia(interaction: discord.Interaction):
    can_points = can_manage_points(interaction)
    can_roles = can_manage_roles(interaction)
    
    response = f"🔑 Uprawnienia {interaction.user.mention}:\n"
    response += f"• Zarządzanie punktami: {'✅' if can_points else '❌'}\n"
    response += f"• Zarządzanie rolami: {'✅' if can_roles else '❌'}"
    
    await interaction.response.send_message(response, ephemeral=True)

@bot.tree.command(name="sprawdz_role", description="Sprawdza role użytkownika")
async def sprawdz_role(interaction: discord.Interaction, user: discord.Member):
    roles = [role.name for role in user.roles if role.name != "@everyone"]
    response = f"👤 Role {user.mention}:\n\n"
    response += "\n".join([f"• {role}" for role in roles])
    
    await interaction.response.send_message(response, ephemeral=True)

# --- Uruchomienie Bota ---
if __name__ == "__main__":
    try:
        bot.run(os.getenv('DISCORD_TOKEN'))
    except discord.LoginFailure:
        print("❌ Błąd logowania: Nieprawidłowy token.")
    except Exception as e:
        print(f"❌ Wystąpił błąd: {str(e)}") 
