import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from enum import Enum
import asyncio
from dotenv import load_dotenv
from datetime import datetime
from typing import Literal

# Load environment variables
load_dotenv()

# Konfiguracja intencji bota
intents = discord.Intents.default()
intents.message_content = True  # Pozwala na czytanie treści wiadomości
intents.members = True         # Pozwala na dostęp do informacji o członkach serwera
intents.guilds = True         # Pozwala na dostęp do informacji o serwerze
intents.guild_messages = True  # Pozwala na czytanie wiadomości na serwerze
intents.messages = True

# Tworzenie instancji bota
class CustomBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='!', intents=intents)
        
    async def setup_hook(self):
        print("Rozpoczynam setup hook...")
        # Lista ID serwerów
        GUILD_IDS = [
            1021373051272704130,  # Pierwszy serwer
            1364669344180863088   # Drugi serwer
        ]
        
        # Przygotowanie komend dla wszystkich serwerów
        for guild_id in GUILD_IDS:
            try:
                guild = discord.Object(id=guild_id)
                self.tree.copy_global_to(guild=guild)
                await self.tree.sync(guild=guild)
                print(f"Komendy zsynchronizowane dla serwera {guild_id}")
            except Exception as e:
                print(f"Błąd podczas synchronizacji komend dla serwera {guild_id}: {str(e)}")
            
        print("Setup hook zakończony!")

# Tworzenie instancji bota
bot = CustomBot()

# Role w systemie
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

    # System punktowy - Plusy
    PLUS1 = 1125425345433194506
    PLUS2 = 1125425435535212544
    PLUS3 = 1125425499980709909

    # System punktowy - Minusy
    MINUS1 = 1021686482236354590
    MINUS2 = 1021687044793188372
    MINUS3 = 1021687258815922230

    # System punktowy - Upomnienia
    UPOMNIENIE1 = 1292900587868000287
    UPOMNIENIE2 = 1292900582192840856
    UPOMNIENIE3 = 1292900560093188096

# Ścieżki awansu
SCIEZKA_OCHRONY = [
    Role.REKRUT,
    Role.MLODSZY_OCHRONIARZ,
    Role.OCHRONIARZ,
    Role.OCHRONIARZ_LICENCJONOWANY,
    Role.DOSWIADCZONY_OCHRONIARZ,
    Role.STARSZY_OCHRONIARZ
]

SCIEZKA_GASTRONOMII = [
    Role.REKRUT,
    Role.KELNER,
    Role.ASYSTENT_KUCHARZA,
    Role.KUCHARZ,
    Role.SZEF_KUCHNI,
    Role.OBSLUGA_BARU
]

SCIEZKA_ZARZADU = [
    Role.REKRUT,
    Role.PRACOWNIK,
    Role.ASYSTENT_KIEROWNIKA,
    Role.KIEROWNIK,
    Role.MENADZER,
    Role.ZASTEPCA_SZEFA
]

SCIEZKA_ZARZADU_OCHRONY = [
    Role.OCHRONA,
    Role.SZKOLENIOWIEC_OCHRONY,
    Role.EGZAMINATOR_OCHRONY,
    Role.ASYSTENT_SZEFA_OCHRONY,
    Role.ZASTEPCA_SZEFA_OCHRONY,
    Role.SZEF_OCHRONY
]

# Role zarządzające (używane w funkcji czy_ma_uprawnienia_do_zarzadzania)
ROLE_ZARZADZAJACE = [
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

# Słownik do przechowywania pracowników (w pamięci)
pracownicy = {}

# Dictionary to store message information
messages_to_delete = {}

# Funkcja do zapisywania danych pracowników do pliku
def zapisz_pracownikow():
    try:
        with open('pracownicy.json', 'w', encoding='utf-8') as f:
            json.dump(pracownicy, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"Błąd podczas zapisywania danych pracowników: {str(e)}")
        return False

# Funkcja do wczytywania danych pracowników z pliku
def wczytaj_pracownikow():
    global pracownicy
    try:
        if os.path.exists('pracownicy.json'):
            with open('pracownicy.json', 'r', encoding='utf-8') as f:
                pracownicy = json.load(f)
            return True
    except Exception as e:
        print(f"Błąd podczas wczytywania danych pracowników: {str(e)}")
        pracownicy = {}
    return False

# Funkcja pomocnicza do sprawdzania uprawnień
def czy_ma_uprawnienia_do_zarzadzania(member: discord.Member) -> bool:
    """
    Sprawdza czy użytkownik ma uprawnienia do zarządzania (role zarządzające lub administrator).
    """
    # Sprawdź czy użytkownik ma którąkolwiek z ról zarządzających
    user_role_ids = [role.id for role in member.roles]
    user_role_names = [role.name for role in member.roles]
    
    # Wyświetl szczegółowe debug info
    print(f"\n=== Sprawdzanie uprawnień dla {member.name} ===")
    print(f"ID użytkownika: {member.id}")
    print("\nRole użytkownika:")
    for role in member.roles:
        print(f"- {role.name} (ID: {role.id})")
    
    print("\nWymagane role zarządzające:")
    for role_id in ROLE_ZARZADZAJACE:
        role_name = "Nieznana"
        for attr_name in dir(Role):
            if not attr_name.startswith('_'):  # pomijamy atrybuty prywatne
                if getattr(Role, attr_name) == role_id:
                    role_name = attr_name
                    break
        print(f"- {role_name} (ID: {role_id})")
    
    # Sprawdź czy użytkownik ma rolę zarządzającą lub jest administratorem
    has_managing_role = any(role_id in user_role_ids for role_id in ROLE_ZARZADZAJACE)
    is_admin = member.guild_permissions.administrator
    
    print(f"\nWyniki sprawdzenia:")
    print(f"Czy ma rolę zarządzającą: {has_managing_role}")
    if has_managing_role:
        matching_roles = [role.name for role in member.roles if role.id in ROLE_ZARZADZAJACE]
        print(f"Pasujące role zarządzające: {', '.join(matching_roles)}")
    print(f"Czy jest administratorem: {is_admin}")
    print("=" * 50)
    
    return has_managing_role or is_admin

# Event wywoływany gdy bot jest gotowy
@bot.event
async def on_ready():
    print(f'Bot jest zalogowany jako {bot.user.name}')
    print(f'ID bota: {bot.user.id}')
    print('-------------------')
    print('Wczytywanie danych pracowników...')
    wczytaj_pracownikow()
    print('Dane pracowników wczytane.')
    print('-------------------')
    
    # Wyświetl informacje o komendach
    print('Dostępne komendy:')
    for command in bot.tree.get_commands():
        print(f'- /{command.name}')
        # Wyświetl szczegóły komendy
        print(f'  Opis: {command.description}')
        print(f'  Parametry: {[param.name for param in command.parameters]}')
    
    # Wyświetl informacje o serwerach
    print('\nSerwery, na których jest bot:')
    for guild in bot.guilds:
        print(f'- {guild.name} (ID: {guild.id})')
        # Sprawdź uprawnienia bota na serwerze
        bot_member = guild.get_member(bot.user.id)
        if bot_member:
            print(f"  Pozycja bota w hierarchii: {bot_member.top_role.position}")
            print(f"  Uprawnienia administratora: {bot_member.guild_permissions.administrator}")
            print(f"  Uprawnienia do zarządzania rolami: {bot_member.guild_permissions.manage_roles}")
            print(f"  Uprawnienia do wysyłania wiadomości: {bot_member.guild_permissions.send_messages}")
            print(f"  Uprawnienia do zarządzania wiadomościami: {bot_member.guild_permissions.manage_messages}")
    
    print('-------------------')
    print('Bot jest gotowy do użycia!')

@bot.event
async def on_message(message):
    # Sprawdź, czy wiadomość została wysłana przez bota
    if message.author == bot.user:
        # Zapisz ID wiadomości i czas utworzenia
        messages_to_delete[message.id] = {
            "channel_id": message.channel.id,
            "timestamp": message.created_at
        }

        # Usuń wiadomość po 12 godzinach
        await asyncio.sleep(12 * 60 * 60)  # 12 godzin w sekundach
        try:
            channel = bot.get_channel(message.channel.id)
            await channel.delete_messages([discord.Object(id=message.id)])
            print(f"Usunięto wiadomość o ID: {message.id}")
        except discord.errors.NotFound:
            print(f"Wiadomość o ID: {message.id} nie istnieje lub została już usunięta.")
        except Exception as e:
            print(f"Wystąpił błąd podczas usuwania wiadomości: {e}")

    # Przetwarzaj inne wiadomości
    await bot.process_commands(message)

# Event do logowania błędów
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.MissingPermissions):
        await ctx.send("❌ Nie masz wymaganych uprawnień do użycia tej komendy!")
    elif isinstance(error, commands.errors.MemberNotFound):
        await ctx.send("❌ Nie znaleziono takiego użytkownika!")
    else:
        print(f"Wystąpił błąd: {str(error)}")
        await ctx.send(f"❌ Wystąpił błąd: {str(error)}")

# Prosta komenda testowa
@bot.tree.command(name="test", description="Sprawdza czy bot działa")
async def slash_test(interaction: discord.Interaction):
    await interaction.response.send_message("Bot działa prawidłowo!", ephemeral=True)

# Funkcja pomocnicza do sprawdzania czy użytkownik jest zatrudniony
def czy_jest_zatrudniony(member: discord.Member) -> bool:
    """
    Sprawdza czy użytkownik jest zatrudniony i automatycznie dodaje do bazy jeśli ma role
    """
    print(f"\n=== SZCZEGÓŁOWE SPRAWDZANIE ZATRUDNIENIA ===")
    print(f"Sprawdzam użytkownika: {member.name} (ID: {member.id})")
    
    # Lista wszystkich ról związanych z pracą
    ROLE_PRACOWNICZE = [
        # Role zarządzające
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
        Role.SZKOLENIOWIEC_OCHRONY,
        # Role podstawowe
        Role.REKRUT,
        Role.PRACOWNIK,
        Role.OCHRONA,
        # Ścieżka Ochrony
        Role.MLODSZY_OCHRONIARZ,
        Role.OCHRONIARZ,
        Role.OCHRONIARZ_LICENCJONOWANY,
        Role.DOSWIADCZONY_OCHRONIARZ,
        Role.STARSZY_OCHRONIARZ,
        # Ścieżka Gastronomii
        Role.KELNER,
        Role.ASYSTENT_KUCHARZA,
        Role.KUCHARZ,
        Role.SZEF_KUCHNI,
        Role.OBSLUGA_BARU
    ]
    
    print("\nROLE PRACOWNICZE W SYSTEMIE:")
    for role_id in ROLE_PRACOWNICZE:
        print(f"- ID: {role_id}")
    
    print("\nROLE UŻYTKOWNIKA:")
    user_role_ids = [role.id for role in member.roles]
    for role in member.roles:
        print(f"- {role.name} (ID: {role.id})")
        if role.id in ROLE_PRACOWNICZE:
            print(f"  ✓ Ta rola jest na liście ról pracowniczych!")
        else:
            # Sprawdź czy nazwa roli wskazuje na rolę pracowniczą
            role_name_lower = role.name.lower()
            if any(keyword in role_name_lower for keyword in ["ochrona", "pracownik", "rekrut", "technik", "menadzer", "kierownik"]):
                print(f"  ✓ Ta rola ma nazwę wskazującą na rolę pracowniczą!")
            else:
                print(f"  ✗ Ta rola nie jest na liście ról pracowniczych")
    
    # Sprawdź czy użytkownik ma którąkolwiek z ról pracowniczych (po ID lub nazwie)
    znalezione_role = []
    for role in member.roles:
        # Sprawdź ID roli
        if int(role.id) in [int(r) for r in ROLE_PRACOWNICZE]:
            znalezione_role.append(role)
            print(f"\nZnaleziono rolę pracowniczą (po ID):")
            print(f"- Nazwa: {role.name}")
            print(f"- ID: {role.id}")
            continue
            
        # Sprawdź nazwę roli
        role_name_lower = role.name.lower()
        if any(keyword in role_name_lower for keyword in ["ochrona", "pracownik", "rekrut", "technik", "menadzer", "kierownik"]):
            znalezione_role.append(role)
            print(f"\nZnaleziono rolę pracowniczą (po nazwie):")
            print(f"- Nazwa: {role.name}")
            print(f"- ID: {role.id}")
    
    ma_role_pracownicza = len(znalezione_role) > 0
    print(f"\nCzy ma rolę pracowniczą: {ma_role_pracownicza}")
    
    # Jeśli użytkownik ma role pracownicze, ale nie ma go w bazie, dodaj go
    if ma_role_pracownicza:
        print("\nSprawdzanie czy użytkownik jest w bazie...")
        if str(member.id) not in pracownicy:
            print("Użytkownik nie jest w bazie, dodaję...")
            # Znajdź najwyższą rolę użytkownika z listy ról pracowniczych
            najwyzsza_rola = znalezione_role[0]  # Bierzemy pierwszą znalezioną rolę
            for role in reversed(znalezione_role):  # Sprawdzamy od końca (wyższe role są później)
                najwyzsza_rola = role
                break
            
            pracownicy[str(member.id)] = {
                "nazwa": str(member),
                "data_zatrudnienia": str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                "rola": najwyzsza_rola.name,
                "plusy": 0,
                "minusy": 0,
                "upomnienia": 0,
                "ostrzezenia": [],
                "historia_awansow": []
            }
            zapisz_pracownikow()
            print(f"✓ Dodano użytkownika {member.name} do bazy z rolą {najwyzsza_rola.name}")
        else:
            print("Użytkownik jest już w bazie")
    
    # Sprawdź czy jest w bazie danych
    jest_w_bazie = str(member.id) in pracownicy
    print(f"\nCzy jest w bazie danych: {jest_w_bazie}")
    if jest_w_bazie:
        print(f"Dane z bazy: {pracownicy[str(member.id)]}")
    
    print("\n=== PODSUMOWANIE ===")
    if ma_role_pracownicza:
        print("Znalezione role pracownicze:")
        for role in znalezione_role:
            print(f"- {role.name} (ID: {role.id})")
    else:
        print("Nie znaleziono żadnej roli pracowniczej")
    print(f"Jest w bazie danych: {jest_w_bazie}")
    print(f"OSTATECZNY WYNIK: {'ZATRUDNIONY' if ma_role_pracownicza or jest_w_bazie else 'NIEZATRUDNIONY'}")
    print("=" * 50)
    
    return ma_role_pracownicza or jest_w_bazie

# Komenda do zatrudniania pracowników
@bot.tree.command(name="job", description="Zatrudnia nowego pracownika")
@app_commands.describe(member="Użytkownik, którego chcesz zatrudnić")
async def slash_job(interaction: discord.Interaction, member: discord.Member):
    try:
        if member.bot:
            await interaction.response.send_message("❌ Nie można zatrudnić bota!", ephemeral=True)
            return

        if not czy_ma_uprawnienia_do_zarzadzania(interaction.user):
            await interaction.response.send_message("❌ Nie masz uprawnień do zatrudniania pracowników!", ephemeral=True)
            return

        await interaction.response.defer()

        # Sprawdź czy role istnieją
        rekrut_role = interaction.guild.get_role(Role.REKRUT)
        pracownik_role = interaction.guild.get_role(Role.PRACOWNIK)

        if not rekrut_role or not pracownik_role:
            await interaction.followup.send(
                f"❌ Nie mogę znaleźć wymaganych ról!\n"
                f"Rola Rekrut ID: {Role.REKRUT}\n"
                f"Rola Pracownik ID: {Role.PRACOWNIK}",
                ephemeral=True
            )
            return

        if str(member.id) in pracownicy:
            # Sprawdź czy użytkownik ma już role
            missing_roles = []
            if rekrut_role not in member.roles:
                missing_roles.append(rekrut_role)
            if pracownik_role not in member.roles:
                missing_roles.append(pracownik_role)

            if not missing_roles:
                await interaction.followup.send(
                    f"ℹ️ {member.mention} jest już zatrudniony i ma wszystkie wymagane role.",
                    ephemeral=True
                )
                return

            # Dodaj brakujące role
            try:
                await member.add_roles(*missing_roles)
                role_names = ", ".join([role.name for role in missing_roles])
                await interaction.followup.send(
                    f"🔄 {member.mention} był już w systemie, nadano brakujące role: {role_names}"
                )
            except discord.Forbidden:
                await interaction.followup.send(
                    "❌ Bot nie ma uprawnień do nadawania ról!",
                    ephemeral=True
                )
            except Exception as e:
                await interaction.followup.send(
                    f"❌ Wystąpił nieoczekiwany błąd: {str(e)}",
                    ephemeral=True
                )
            return

        try:
            # Nadaj obie role
            await member.add_roles(rekrut_role, pracownik_role)
            
            # Dodaj pracownika do systemu
            pracownicy[str(member.id)] = {
                "nazwa": str(member),
                "data_zatrudnienia": str(interaction.created_at.strftime("%Y-%m-%d %H:%M:%S")),
                "rola": "Rekrut, Pracownik",
                "plusy": 0,
                "minusy": 0,
                "upomnienia": 0,
                "ostrzezenia": [],
                "historia_awansow": [
                    {
                        "data": str(interaction.created_at.strftime("%Y-%m-%d %H:%M:%S")),
                        "rola": "Rekrut, Pracownik",
                        "awansujacy": str(interaction.user)
                    }
                ]
            }
            
            if not zapisz_pracownikow():
                await interaction.followup.send(
                    "⚠️ Udało się nadać role, ale wystąpił błąd podczas zapisywania danych pracownika!",
                    ephemeral=True
                )
                return
                
            await interaction.followup.send(
                f"✅ Pomyślnie zatrudniono {member.mention}!\n"
                f"Nadane role: {rekrut_role.name}, {pracownik_role.name}"
            )
            
        except discord.Forbidden:
            await interaction.followup.send(
                "❌ Bot nie ma uprawnień do nadawania ról!\n"
                "Upewnij się, że rola bota jest wyżej w hierarchii niż role, które próbuje nadawać.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(
                f"❌ Wystąpił błąd podczas zarządzania rolami: {str(e)}",
                ephemeral=True
            )
            
    except Exception as e:
        error_msg = f"❌ Wystąpił błąd: {str(e)}"
        if not interaction.response.is_done():
            await interaction.response.send_message(error_msg, ephemeral=True)
        else:
            await interaction.followup.send(error_msg, ephemeral=True)
        print(f"Błąd podczas wykonywania komendy job: {str(e)}")

# Kanały do logowania (uzupełnij właściwe ID)
class Kanaly:
    LOGI_HR = 1234567890  # ID kanału do logowania zmian HR (zatrudnienia, zwolnienia, etc.)
    LOGI_PUNKTY = 1234567890  # ID kanału do logowania punktów
    LOGI_AWANSE = 1234567890  # ID kanału do logowania awansów

async def dodaj_punkt(interaction: discord.Interaction, member: discord.Member, typ: str, powod: str = None) -> bool:
    """
    Dodaje punkt (plus/minus/upomnienie) pracownikowi i zarządza rolami.
    Sprawdza czy użytkownik jest zatrudniony (ma rolę Pracownik LUB Rekrut, lub jest w bazie danych).
    
    Args:
        interaction: Interakcja Discorda
        member: Członek serwera, któremu dodajemy punkt
        typ: Typ punktu ('plusy', 'minusy', 'upomnienia')
        powod: Powód dodania punktu
        
    Returns:
        bool: True jeśli osiągnięto limit 3 punktów, False w przeciwnym razie
    """
    try:
        # Sprawdź czy pracownik jest zatrudniony
        if not czy_jest_zatrudniony(member):
            await interaction.response.send_message(f"❌ {member.mention} nie jest zatrudniony!", ephemeral=True)
            return False

        # Inicjalizuj dane pracownika jeśli nie istnieją
        if str(member.id) not in pracownicy:
            pracownicy[str(member.id)] = {
                "nazwa": str(member),
                "data_zatrudnienia": str(interaction.created_at.strftime("%Y-%m-%d %H:%M:%S")),
                "rola": "Pracownik",
                "plusy": 0,
                "minusy": 0,
                "upomnienia": 0,
                "ostrzezenia": [],
                "historia_awansow": []
            }
            zapisz_pracownikow()

        # Określ role na podstawie typu punktów
        if typ == "plusy":
            role_levels = {
                1: discord.utils.get(interaction.guild.roles, name="1/3 ⭐"),
                2: discord.utils.get(interaction.guild.roles, name="2/3 ⭐"),
                3: discord.utils.get(interaction.guild.roles, name="3/3 ⭐")
            }
        elif typ == "minusy":
            role_levels = {
                1: discord.utils.get(interaction.guild.roles, name="1/3 ❌"),
                2: discord.utils.get(interaction.guild.roles, name="2/3 ❌"),
                3: discord.utils.get(interaction.guild.roles, name="3/3 ❌")
            }
        else:
            role_levels = {
                1: discord.utils.get(interaction.guild.roles, name="1/3 ⚠️"),
                2: discord.utils.get(interaction.guild.roles, name="2/3 ⚠️"),
                3: discord.utils.get(interaction.guild.roles, name="3/3 ⚠️")
            }

        # Sprawdź aktualny poziom na podstawie ról
        current_level = 0
        for level, role in role_levels.items():
            if role in member.roles:
                current_level = level
                break

        # Ustaw liczbę punktów na podstawie aktualnego poziomu
        pracownicy[str(member.id)][typ] = current_level

        # Dodaj nowy punkt
        pracownicy[str(member.id)][typ] += 1
        nowy_poziom = pracownicy[str(member.id)][typ]

        # Usuń stare role
        for role in role_levels.values():
            if role in member.roles:
                await member.remove_roles(role)

        # Dodaj nową rolę jeśli nie przekroczono limitu
        if nowy_poziom <= 3:
            await member.add_roles(role_levels[nowy_poziom])
            
            # Przygotuj odpowiednie emoji i tekst
            emoji_map = {"plusy": "⭐", "minusy": "❌", "upomnienia": "⚠️"}
            emoji = emoji_map.get(typ, "")
            
            # Wyślij powiadomienie
            if powod:
                await interaction.response.send_message(
                    f"{emoji} {member.mention} otrzymał(a) punkt ({nowy_poziom}/3)\nPowód: {powod}"
                )
            else:
                await interaction.response.send_message(
                    f"{emoji} {member.mention} otrzymał(a) punkt ({nowy_poziom}/3)"
                )

        # Jeśli osiągnięto limit 3 punktów
        if nowy_poziom >= 3:
            # Wyzeruj punkty
            pracownicy[str(member.id)][typ] = 0
            zapisz_pracownikow()
            
            # Wyślij odpowiednie powiadomienie
            if typ == "plusy":
                await interaction.followup.send(f"🎉 **Gratulacje!** {member.mention} otrzymał(a) 3 plusy! To świetny wynik!")
            elif typ == "minusy":
                await interaction.followup.send(f"⚠️ **UWAGA!** {member.mention} otrzymał(a) 3 minusy! Rozważ podjęcie odpowiednich działań.")
            else:
                await interaction.followup.send(f"⛔ **UWAGA!** {member.mention} otrzymał(a) 3 upomnienia! Konieczne jest podjęcie działań!")
            
            return True

        zapisz_pracownikow()
        return False

    except Exception as e:
        print(f"Błąd podczas dodawania punktu: {str(e)}")
        if not interaction.response.is_done():
            await interaction.response.send_message(f"Wystąpił błąd podczas dodawania punktu: {str(e)}", ephemeral=True)
        else:
            await interaction.followup.send(f"Wystąpił błąd podczas dodawania punktu: {str(e)}", ephemeral=True)
        return False

# Komenda do dodawania plusów
@bot.tree.command(name="plus", description="Dodaje plus pracownikowi")
@app_commands.describe(
    member="Pracownik, któremu chcesz dodać plus",
    powod="Powód przyznania plusa"
)
async def slash_plus(interaction: discord.Interaction, member: discord.Member, powod: str):
    """
    Dodaje plus pracownikowi i nadaje odpowiednią rangę.
    """
    print(f"\n=== DODAWANIE PLUSA ===")
    print(f"Użytkownik wykonujący: {interaction.user.name} (ID: {interaction.user.id})")
    print(f"Cel: {member.name} (ID: {member.id})")
    print(f"Powód: {powod}")
    
    await dodaj_punkt(interaction, member, "plusy", powod)

# Komenda do dodawania minusów
@bot.tree.command(name="minus", description="Dodaje minus pracownikowi")
@app_commands.describe(
    member="Pracownik, któremu chcesz dodać minus",
    powod="Powód przyznania minusa"
)
async def slash_minus(interaction: discord.Interaction, member: discord.Member, powod: str):
    """
    Dodaje minus pracownikowi i nadaje odpowiednią rangę.
    """
    print(f"\n=== DODAWANIE MINUSA ===")
    print(f"Użytkownik wykonujący: {interaction.user.name} (ID: {interaction.user.id})")
    print(f"Cel: {member.name} (ID: {member.id})")
    print(f"Powód: {powod}")
    
    await dodaj_punkt(interaction, member, "minusy", powod)

# Komenda do dodawania upomnień
@bot.tree.command(name="upomnienie", description="Dodaje upomnienie pracownikowi")
@app_commands.describe(
    member="Pracownik, któremu chcesz dodać upomnienie",
    powod="Powód przyznania upomnienia"
)
async def slash_upomnienie(interaction: discord.Interaction, member: discord.Member, powod: str):
    try:
        # Sprawdź uprawnienia
        if not czy_ma_uprawnienia_do_zarzadzania(interaction.user):
            await interaction.response.send_message("❌ Nie masz uprawnień do zarządzania upomnieniami!", ephemeral=True)
            return

        # Sprawdź czy pracownik jest zatrudniony
        if not czy_jest_zatrudniony(member):
            await interaction.response.send_message(f"❌ {member.mention} nie jest zatrudniony!", ephemeral=True)
            return

        # Dodaj upomnienie
        osiagnieto_limit = await dodaj_punkt(interaction, member, "upomnienia", powod)
        
        # Jeśli osiągnięto limit 3 upomnień, wyślij dodatkowe powiadomienie
        if osiagnieto_limit:
            await interaction.followup.send(f"🚨 **UWAGA!** {member.mention} otrzymał(a) 3 upomnienia! Należy podjąć odpowiednie kroki dyscyplinarne!")
            
    except Exception as e:
        print(f"Błąd podczas wykonywania komendy upomnienie: {str(e)}")
        if not interaction.response.is_done():
            await interaction.response.send_message(f"Wystąpił błąd podczas wykonywania komendy: {str(e)}", ephemeral=True)
        else:
            await interaction.followup.send(f"Wystąpił błąd podczas wykonywania komendy: {str(e)}", ephemeral=True)

# Definicje ścieżek jako stałe
SCIEZKI_WYBORY = [
    app_commands.Choice(name="Ochrona", value="ochrona"),
    app_commands.Choice(name="Gastronomia", value="gastronomia"),
    app_commands.Choice(name="Zarząd", value="zarzad"),
    app_commands.Choice(name="Zarząd Ochrony", value="zarzad_ochrony")
]

@bot.tree.command(name="awansuj", description="Awansuje pracownika na nowe stanowisko")
@app_commands.describe(
    member="Pracownik do awansowania",
    sciezka="Ścieżka awansu",
    poziom="Poziom awansu (1-6, gdzie 1 to najniższy poziom)"
)
@app_commands.choices(sciezka=SCIEZKI_WYBORY)
async def slash_awansuj(
    interaction: discord.Interaction, 
    member: discord.Member, 
    sciezka: Literal["Ochrona", "Gastronomia", "Zarząd", "Zarząd Ochrony"],
    poziom: app_commands.Range[int, 1, 6]
):
    try:
        # Sprawdź uprawnienia
        if not czy_ma_uprawnienia_do_zarzadzania(interaction.user):
            await interaction.response.send_message(
                "❌ Nie masz uprawnień do awansowania pracowników!\n"
                "Wymagana jest jedna z ról zarządzających lub uprawnienia administratora.", 
                ephemeral=True
            )
            return

        await interaction.response.defer()

        # Walidacja parametrów
        sciezka_value = sciezka.lower().replace(" ", "_")
        if sciezka_value not in ["ochrona", "gastronomia", "zarzad", "zarzad_ochrony"]:
            await interaction.followup.send(
                "❌ Nieprawidłowa ścieżka! Wybierz 'Ochrona', 'Gastronomia', 'Zarząd' lub 'Zarząd Ochrony'.",
                ephemeral=True
            )
            return

        if poziom < 1 or poziom > 6:
            await interaction.followup.send(
                "❌ Poziom awansu musi być między 1 a 6!",
                ephemeral=True
            )
            return

        # Sprawdź czy pracownik ma wymaganą rolę bazową
        if sciezka_value == "zarzad_ochrony":
            rola_bazowa = interaction.guild.get_role(Role.OCHRONA)
            if not rola_bazowa or rola_bazowa not in member.roles:
                await interaction.followup.send(
                    f"❌ {member.mention} nie ma roli Ochrona wymaganej do awansu w zarządzie ochrony!",
                    ephemeral=True
                )
                return
        else:
            pracownik_role = interaction.guild.get_role(Role.PRACOWNIK)
            if not pracownik_role or pracownik_role not in member.roles:
                await interaction.followup.send(
                    f"❌ {member.mention} nie ma roli Pracownik!",
                    ephemeral=True
                )
                return

        # Wybierz odpowiednią ścieżkę awansu
        if sciezka_value == "gastronomia":
            sciezka_awansu = SCIEZKA_GASTRONOMII
            nazwa_sciezki = "Gastronomia"
        elif sciezka_value == "zarzad":
            sciezka_awansu = SCIEZKA_ZARZADU
            nazwa_sciezki = "Zarząd"
        elif sciezka_value == "zarzad_ochrony":
            sciezka_awansu = SCIEZKA_ZARZADU_OCHRONY
            nazwa_sciezki = "Zarząd Ochrony"
        else:  # ochrona
            sciezka_awansu = SCIEZKA_OCHRONY
            nazwa_sciezki = "Ochrona"

        # Sprawdź aktualną rolę użytkownika
        aktualna_rola = None
        aktualny_poziom = -1
        
        for i, rola_id in enumerate(sciezka_awansu):
            rola = interaction.guild.get_role(rola_id)
            if rola and rola in member.roles:
                aktualna_rola = rola
                aktualny_poziom = i
                break

        # Sprawdź czy awans jest możliwy
        if aktualny_poziom >= 0:  # Jeśli użytkownik ma jakąś rolę ze ścieżki
            if poziom <= aktualny_poziom:  # Zmienione z aktualny_poziom + 1
                await interaction.followup.send(
                    f"❌ {member.mention} jest już na poziomie {aktualny_poziom + 1}!\n"
                    f"Aktualna rola: {aktualna_rola.name}\n"
                    f"Nie można awansować na niższy lub ten sam poziom.",
                    ephemeral=True
                )
                return
            
            # Sprawdź czy awans nie jest o więcej niż jeden poziom
            if poziom > aktualny_poziom + 2:
                await interaction.followup.send(
                    f"❌ Nie można awansować o więcej niż jeden poziom!\n"
                    f"Aktualny poziom: {aktualny_poziom + 1}\n"
                    f"Próba awansu na poziom: {poziom}",
                    ephemeral=True
                )
                return
        else:  # Jeśli użytkownik nie ma żadnej roli ze ścieżki
            if poziom > 1:  # Można awansować tylko na poziom 1
                await interaction.followup.send(
                    f"❌ {member.mention} nie ma żadnej roli ze ścieżki {nazwa_sciezki}!\n"
                    "Można awansować tylko na poziom 1.",
                    ephemeral=True
                )
                return
            
            # Sprawdź rolę bazową tylko przy pierwszym awansie
            if sciezka_value == "gastronomia":
                rola_bazowa = interaction.guild.get_role(Role.REKRUT)
                if not rola_bazowa or rola_bazowa not in member.roles:
                    await interaction.followup.send(
                        f"❌ {member.mention} nie ma roli Rekrut wymaganej do pierwszego awansu w gastronomii!",
                        ephemeral=True
                    )
                    return
            else:  # ochrona
                rola_bazowa = interaction.guild.get_role(Role.MLODSZY_OCHRONIARZ)
                if not rola_bazowa or rola_bazowa not in member.roles:
                    await interaction.followup.send(
                        f"❌ {member.mention} nie ma roli Młodszy Ochroniarz wymaganej do pierwszego awansu w ochronie!",
                        ephemeral=True
                    )
                    return

        try:
            # Pobierz rolę do nadania
            poziom_index = poziom - 1
            if poziom_index < 0 or poziom_index >= len(sciezka_awansu):
                await interaction.followup.send(
                    f"❌ Nieprawidłowy poziom! Dostępne poziomy: 1-{len(sciezka_awansu)}",
                    ephemeral=True
                )
                return

            nowa_rola_id = sciezka_awansu[poziom_index]
            nowa_rola = interaction.guild.get_role(nowa_rola_id)
            if not nowa_rola:
                await interaction.followup.send(
                    f"❌ Nie mogę znaleźć roli dla poziomu {poziom}!\n"
                    f"ID roli: {nowa_rola_id}",
                    ephemeral=True
                )
                return

            # Usuń stare role ze ścieżki
            for rola_id in sciezka_awansu:
                if rola_id != nowa_rola_id:  # nie usuwaj nowej roli, jeśli już ją ma
                    rola = interaction.guild.get_role(rola_id)
                    if rola and rola in member.roles:
                        await member.remove_roles(rola)
                        print(f"Usunięto rolę {rola.name} dla {member.name}")

            # Nadaj nową rolę
            await member.add_roles(nowa_rola)
            print(f"Nadano rolę {nowa_rola.name} dla {member.name}")
            
            # Aktualizuj dane w systemie
            if str(member.id) not in pracownicy:
                pracownicy[str(member.id)] = {
                    "nazwa": str(member),
                    "data_zatrudnienia": str(interaction.created_at.strftime("%Y-%m-%d %H:%M:%S")),
                    "rola": nowa_rola.name,
                    "plusy": 0,
                    "minusy": 0,
                    "upomnienia": 0,
                    "ostrzezenia": [],
                    "historia_awansow": []
                }
            
            pracownicy[str(member.id)]["rola"] = nowa_rola.name
            pracownicy[str(member.id)]["historia_awansow"].append({
                "data": str(interaction.created_at.strftime("%Y-%m-%d %H:%M:%S")),
                "rola": nowa_rola.name,
                "awansujacy": str(interaction.user)
            })
            
            zapisz_pracownikow()

            # Wyślij potwierdzenie
            await interaction.followup.send(
                f"✅ Pomyślnie awansowano {member.mention}!\n"
                f"Ścieżka: {nazwa_sciezki}\n"
                f"Nowa rola: {nowa_rola.name}\n"
                f"Poziom: {poziom}/{len(sciezka_awansu)}"
            )
                
        except discord.Forbidden:
            await interaction.followup.send(
                "❌ Bot nie ma uprawnień do zarządzania rolami!\n"
                "Upewnij się, że rola bota jest wyżej w hierarchii niż role, które próbuje nadawać.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(
                f"❌ Wystąpił błąd podczas zarządzania rolami: {str(e)}\n"
                f"Szczegóły błędu zostały zapisane w logach.",
                ephemeral=True
            )
            print(f"Błąd podczas zarządzania rolami: {str(e)}")
            
    except Exception as e:
        error_msg = f"❌ Wystąpił błąd: {str(e)}"
        if not interaction.response.is_done():
            await interaction.response.send_message(error_msg, ephemeral=True)
        else:
            await interaction.followup.send(error_msg, ephemeral=True)
        print(f"Błąd podczas wykonywania komendy awansuj: {str(e)}")

# Komenda do wyświetlania historii pracownika
@bot.tree.command(name="historia", description="Wyświetla historię pracownika")
@app_commands.describe(member="Pracownik, którego historię chcesz wyświetlić (opcjonalne)")
async def slash_historia(interaction: discord.Interaction, member: discord.Member = None):
    await interaction.response.defer()

    if member is None:
        member = interaction.user

    if not czy_jest_zatrudniony(member):
        await interaction.followup.send(f"❌ {member.mention} nie jest zatrudniony!")
        return

    # Upewnij się, że pracownik jest w bazie danych
    if str(member.id) not in pracownicy:
        pracownicy[str(member.id)] = {
            "nazwa": str(member),
            "data_zatrudnienia": str(interaction.created_at.strftime("%Y-%m-%d %H:%M:%S")),
            "rola": "Pracownik",
            "plusy": 0,
            "minusy": 0,
            "upomnienia": 0,
            "ostrzezenia": [],
            "historia_awansow": []
        }
        zapisz_pracownikow()

    dane = pracownicy[str(member.id)]
    historia = dane["historia_awansow"]

    embed = discord.Embed(title=f"Historia pracownika {dane['nazwa']}", color=0x00ff00)
    embed.add_field(name="Aktualna rola", value=dane["rola"], inline=False)
    embed.add_field(name="Data zatrudnienia", value=dane["data_zatrudnienia"], inline=False)
    embed.add_field(name="Statystyki", value=f"Plusy: {dane['plusy']}\nMinusy: {dane['minusy']}\nUpomnienia: {dane['upomnienia']}", inline=False)
    
    historia_text = ""
    for wpis in historia:
        historia_text += f"📅 {wpis['data']}: {wpis['rola']} (przez {wpis['awansujacy']})\n"
    
    embed.add_field(name="Historia awansów", value=historia_text if historia_text else "Brak historii awansów", inline=False)
    await interaction.followup.send(embed=embed)

# Komenda do ostrzegania pracowników
@bot.tree.command(name="warn", description="Nadaje ostrzeżenie pracownikowi")
@app_commands.describe(
    member="Pracownik, któremu chcesz dać ostrzeżenie",
    powod="Powód ostrzeżenia"
)
async def slash_warn(interaction: discord.Interaction, member: discord.Member, powod: str):
    if not czy_ma_uprawnienia_do_zarzadzania(interaction.user):
        await interaction.response.send_message("❌ Nie masz uprawnień do nadawania ostrzeżeń!", ephemeral=True)
        return

    await interaction.response.defer()

    if not czy_jest_zatrudniony(member):
        await interaction.followup.send(f"❌ {member.mention} nie jest zatrudniony!")
        return

    # Upewnij się, że pracownik jest w bazie danych
    if str(member.id) not in pracownicy:
        pracownicy[str(member.id)] = {
            "nazwa": str(member),
            "data_zatrudnienia": str(interaction.created_at.strftime("%Y-%m-%d %H:%M:%S")),
            "rola": "Pracownik",
            "plusy": 0,
            "minusy": 0,
            "upomnienia": 0,
            "ostrzezenia": [],
            "historia_awansow": []
        }

    # Dodaj ostrzeżenie do historii pracownika
    if "ostrzezenia" not in pracownicy[str(member.id)]:
        pracownicy[str(member.id)]["ostrzezenia"] = []

    pracownicy[str(member.id)]["ostrzezenia"].append({
        "data": str(interaction.created_at.strftime("%Y-%m-%d %H:%M:%S")),
        "powod": powod,
        "od": str(interaction.user)
    })

    zapisz_pracownikow()

    # Wyślij informację o ostrzeżeniu
    embed = discord.Embed(
        title="⚠️ Ostrzeżenie",
        description=f"Pracownik {member.mention} otrzymał ostrzeżenie",
        color=0xffff00
    )
    embed.add_field(name="Powód", value=powod, inline=False)
    embed.add_field(name="Od", value=interaction.user.mention, inline=False)
    embed.add_field(name="Data", value=interaction.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
    
    await interaction.followup.send(embed=embed)

# Komenda do degradacji pracownika
@bot.tree.command(name="degrad", description="Degraduje pracownika na niższy poziom")
@app_commands.describe(
    member="Pracownik do zdegradowania",
    sciezka="Ścieżka awansu",
    poziom="Poziom na który chcesz zdegradować (1-6, gdzie 1 to najniższy poziom)",
    powod="Powód degradacji"
)
@app_commands.choices(sciezka=SCIEZKI_WYBORY)
async def slash_degrad(
    interaction: discord.Interaction, 
    member: discord.Member,
    sciezka: Literal["Ochrona", "Gastronomia", "Zarząd", "Zarząd Ochrony"],
    poziom: app_commands.Range[int, 1, 6],
    powod: str
):
    try:
        # Sprawdź uprawnienia
        if not czy_ma_uprawnienia_do_zarzadzania(interaction.user):
            await interaction.response.send_message(
                "❌ Nie masz uprawnień do degradowania pracowników!\n"
                "Wymagana jest jedna z ról zarządzających lub uprawnienia administratora.", 
                ephemeral=True
            )
            return

        await interaction.response.defer()

        # Walidacja parametrów
        sciezka_value = sciezka.lower().replace(" ", "_")
        if sciezka_value not in ["ochrona", "gastronomia", "zarzad", "zarzad_ochrony"]:
            await interaction.followup.send(
                "❌ Nieprawidłowa ścieżka! Wybierz 'Ochrona', 'Gastronomia', 'Zarząd' lub 'Zarząd Ochrony'.",
                ephemeral=True
            )
            return

        if poziom < 1 or poziom > 6:
            await interaction.followup.send(
                "❌ Poziom degradacji musi być między 1 a 6!",
                ephemeral=True
            )
            return

        # Sprawdź czy pracownik ma rolę PRACOWNIK
        pracownik_role = interaction.guild.get_role(Role.PRACOWNIK)
        if not pracownik_role or pracownik_role not in member.roles:
            await interaction.followup.send(
                f"❌ {member.mention} nie ma roli Pracownik!",
                ephemeral=True
            )
            return

        # Wybierz odpowiednią ścieżkę
        if sciezka_value == "gastronomia":
            sciezka_awansu = SCIEZKA_GASTRONOMII
            nazwa_sciezki = "Gastronomia"
            rola_bazowa = interaction.guild.get_role(Role.REKRUT)
        elif sciezka_value == "zarzad":
            sciezka_awansu = SCIEZKA_ZARZADU
            nazwa_sciezki = "Zarząd"
            rola_bazowa = interaction.guild.get_role(Role.PRACOWNIK)
        elif sciezka_value == "zarzad_ochrony":
            sciezka_awansu = SCIEZKA_ZARZADU_OCHRONY
            nazwa_sciezki = "Zarząd Ochrony"
            rola_bazowa = interaction.guild.get_role(Role.OCHRONA)
        else:  # ochrona
            sciezka_awansu = SCIEZKA_OCHRONY
            nazwa_sciezki = "Ochrona"
            rola_bazowa = interaction.guild.get_role(Role.MLODSZY_OCHRONIARZ)

        # Sprawdź aktualną rolę użytkownika
        aktualna_rola = None
        aktualny_poziom = -1
        
        for i, rola_id in enumerate(sciezka_awansu):
            rola = interaction.guild.get_role(rola_id)
            if rola and rola in member.roles:
                aktualna_rola = rola
                aktualny_poziom = i
                break

        # Sprawdź czy degradacja jest możliwa
        if aktualny_poziom == -1:
            await interaction.followup.send(
                f"❌ {member.mention} nie ma żadnej roli ze ścieżki {nazwa_sciezki}!",
                ephemeral=True
            )
            return

        if poziom >= aktualny_poziom + 1:
            await interaction.followup.send(
                f"❌ Nie można degradować na wyższy lub ten sam poziom!\n"
                f"Aktualny poziom: {aktualny_poziom + 1}\n"
                f"Próba degradacji na poziom: {poziom}",
                ephemeral=True
            )
            return

        if poziom < aktualny_poziom:
            if poziom < aktualny_poziom - 1:
                await interaction.followup.send(
                    f"❌ Nie można degradować o więcej niż jeden poziom!\n"
                    f"Aktualny poziom: {aktualny_poziom + 1}\n"
                    f"Próba degradacji na poziom: {poziom}",
                    ephemeral=True
                )
                return

        try:
            # Pobierz rolę do nadania
            poziom_index = poziom - 1
            if poziom_index < 0 or poziom_index >= len(sciezka_awansu):
                await interaction.followup.send(
                    f"❌ Nieprawidłowy poziom! Dostępne poziomy: 1-{len(sciezka_awansu)}",
                    ephemeral=True
                )
                return

            nowa_rola_id = sciezka_awansu[poziom_index]
            nowa_rola = interaction.guild.get_role(nowa_rola_id)
            if not nowa_rola:
                await interaction.followup.send(
                    f"❌ Nie mogę znaleźć roli dla poziomu {poziom}!\n"
                    f"ID roli: {nowa_rola_id}",
                    ephemeral=True
                )
                return

            # Usuń tylko aktualną rolę
            if aktualna_rola:
                await member.remove_roles(aktualna_rola)
                print(f"Usunięto rolę {aktualna_rola.name} dla {member.name}")

            # Nadaj nową rolę
            await member.add_roles(nowa_rola)
            print(f"Nadano rolę {nowa_rola.name} dla {member.name}")

            # Upewnij się, że użytkownik ma rolę bazową
            if rola_bazowa and rola_bazowa not in member.roles:
                await member.add_roles(rola_bazowa)
                print(f"Przywrócono rolę bazową {rola_bazowa.name} dla {member.name}")
            
            # Aktualizuj dane w systemie
            if str(member.id) not in pracownicy:
                pracownicy[str(member.id)] = {
                    "nazwa": str(member),
                    "data_zatrudnienia": str(interaction.created_at.strftime("%Y-%m-%d %H:%M:%S")),
                    "rola": nowa_rola.name,
                    "plusy": 0,
                    "minusy": 0,
                    "upomnienia": 0,
                    "ostrzezenia": [],
                    "historia_awansow": []
                }
            
            pracownicy[str(member.id)]["rola"] = nowa_rola.name
            pracownicy[str(member.id)]["historia_awansow"].append({
                "data": str(interaction.created_at.strftime("%Y-%m-%d %H:%M:%S")),
                "rola": nowa_rola.name,
                "awansujacy": str(interaction.user),
                "typ": "degradacja",
                "powod": powod
            })
            
            zapisz_pracownikow()

            # Wyślij potwierdzenie
            await interaction.followup.send(
                f"⬇️ Pomyślnie zdegradowano {member.mention}!\n"
                f"Ścieżka: {nazwa_sciezki}\n"
                f"Nowa rola: {nowa_rola.name}\n"
                f"Poziom: {poziom}/{len(sciezka_awansu)}\n"
                f"Powód: {powod}"
            )
                
        except discord.Forbidden:
            await interaction.followup.send(
                "❌ Bot nie ma uprawnień do zarządzania rolami!\n"
                "Upewnij się, że rola bota jest wyżej w hierarchii niż role, które próbuje nadawać.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(
                f"❌ Wystąpił błąd podczas zarządzania rolami: {str(e)}\n"
                f"Szczegóły błędu zostały zapisane w logach.",
                ephemeral=True
            )
            print(f"Błąd podczas zarządzania rolami: {str(e)}")
            
    except Exception as e:
        error_msg = f"❌ Wystąpił błąd: {str(e)}"
        if not interaction.response.is_done():
            await interaction.response.send_message(error_msg, ephemeral=True)
        else:
            await interaction.followup.send(error_msg, ephemeral=True)
        print(f"Błąd podczas wykonywania komendy degrad: {str(e)}")

# Ulepszona komenda do zwalniania pracowników
@bot.tree.command(name="zwolnij", description="Zwalnia pracownika")
@app_commands.describe(
    member="Pracownik do zwolnienia",
    powod="Powód zwolnienia"
)
async def slash_zwolnij(interaction: discord.Interaction, member: discord.Member, powod: str):
    if not czy_ma_uprawnienia_do_zarzadzania(interaction.user):
        await interaction.response.send_message("❌ Nie masz uprawnień do zwalniania pracowników!", ephemeral=True)
        return
    
    await interaction.response.defer()

    if str(member.id) not in pracownicy:
        await interaction.followup.send(f"❌ {member.mention} nie jest zatrudniony!")
        return
    
    try:
        # Usuń wszystkie role ze ścieżek awansu
        roles_to_remove = []
        
        # Dodaj role z obu ścieżek
        for role_id in SCIEZKA_OCHRONY + SCIEZKA_GASTRONOMII:
            role = interaction.guild.get_role(role_id)
            if role and role in member.roles:
                roles_to_remove.append(role)
        
        # Usuń role
        if roles_to_remove:
            await member.remove_roles(*roles_to_remove)
        
        # Zapisz informację o zwolnieniu
        zwolniony_pracownik = pracownicy[str(member.id)]
        data_zwolnienia = str(interaction.created_at.strftime("%Y-%m-%d %H:%M:%S"))
        
        # Usuń pracownika z listy
        del pracownicy[str(member.id)]
        
        # Zapisz zmiany
        zapisz_pracownikow()
        
        # Przygotuj embed z informacją o zwolnieniu
        embed = discord.Embed(
            title="🚫 Zwolnienie pracownika",
            description=f"Pracownik {member.mention} został zwolniony",
            color=0xff0000
        )
        embed.add_field(name="Ostatnia rola", value=zwolniony_pracownik["rola"], inline=False)
        embed.add_field(name="Data zatrudnienia", value=zwolniony_pracownik["data_zatrudnienia"], inline=False)
        embed.add_field(name="Data zwolnienia", value=data_zwolnienia, inline=False)
        embed.add_field(name="Powód", value=powod, inline=False)
        embed.add_field(name="Zwolniony przez", value=interaction.user.mention, inline=False)
        
        await interaction.followup.send(embed=embed)
        
    except discord.Forbidden:
        await interaction.followup.send("❌ Bot nie ma uprawnień do usuwania ról!")
    except Exception as e:
        await interaction.followup.send(f"❌ Wystąpił błąd: {str(e)}")

# Komenda do wyświetlania listy pracowników
@bot.tree.command(name="lista_pracownikow", description="Wyświetla listę wszystkich pracowników")
async def slash_lista_pracownikow(interaction: discord.Interaction):
    await interaction.response.defer()

    if not pracownicy:
        await interaction.followup.send("📋 Lista pracowników jest pusta!")
        return
    
    # Tworzenie wiadomości z listą pracowników
    message = "📋 Lista pracowników:\n\n"
    for pracownik_id, dane in pracownicy.items():
        message += f"• {dane['nazwa']}\n"
        message += f"  Rola: {dane['rola']}\n"
        message += f"  Plusy: {dane['plusy']} | Minusy: {dane['minusy']} | Upomnienia: {dane['upomnienia']}\n"
        message += f"  Data zatrudnienia: {dane['data_zatrudnienia']}\n\n"
    
    await interaction.followup.send(message)

# Modyfikacja komunikatu błędu w komendach
async def brak_uprawnien_wiadomosc(interaction: discord.Interaction):
    user_roles = [f"{role.name} (ID: {role.id})" for role in interaction.user.roles]
    return await interaction.response.send_message(
        "❌ Nie masz uprawnień do użycia tej komendy!\n\n"
        "Wymagana jest jedna z ról zarządzających lub uprawnienia administratora.\n"
        f"Twoje obecne role:\n{chr(10).join(['- ' + role for role in user_roles])}\n\n"
        "Jeśli uważasz, że powinieneś mieć dostęp, skontaktuj się z administratorem.",
        ephemeral=True
    )

@bot.tree.command(name="test_uprawnienia", description="Testuje uprawnienia użytkownika")
async def slash_test_uprawnienia(interaction: discord.Interaction):
    """Komenda do testowania uprawnień użytkownika"""
    await interaction.response.defer(ephemeral=True)
    
    # Sprawdź uprawnienia
    has_permission = czy_ma_uprawnienia_do_zarzadzania(interaction.user)
    
    # Przygotuj szczegółową odpowiedź
    user_roles = [f"{role.name} (ID: {role.id})" for role in interaction.user.roles]
    managing_roles = []
    for role_id in ROLE_ZARZADZAJACE:
        role_name = "Nieznana"
        for attr_name in dir(Role):
            if not attr_name.startswith('_'):
                if getattr(Role, attr_name) == role_id:
                    role_name = attr_name
                    break
        managing_roles.append(f"{role_name} (ID: {role_id})")
    
    response = f"📊 **Raport uprawnień dla {interaction.user.mention}**\n\n"
    response += f"🔑 Czy ma uprawnienia: {'✅ Tak' if has_permission else '❌ Nie'}\n"
    response += f"👑 Czy jest administratorem: {'✅ Tak' if interaction.user.guild_permissions.administrator else '❌ Nie'}\n\n"
    
    response += "👤 **Twoje role:**\n"
    response += "\n".join([f"- {role}" for role in user_roles])
    
    response += "\n\n📜 **Role zarządzające wymagane do użycia komend:**\n"
    response += "\n".join([f"- {role}" for role in managing_roles])
    
    await interaction.followup.send(response, ephemeral=True)

@bot.tree.command(name="sprawdz_role", description="Sprawdza ID ról na serwerze")
async def slash_sprawdz_role(interaction: discord.Interaction):
    """Sprawdza ID ról na serwerze"""
    await interaction.response.defer(ephemeral=True)
    
    response = "📋 Lista ról na serwerze:\n\n"
    for role in interaction.guild.roles:
        response += f"• {role.name}: {role.id}\n"
    
    # Podziel odpowiedź na mniejsze części jeśli jest za długa
    if len(response) > 1900:  # Discord ma limit 2000 znaków
        parts = [response[i:i+1900] for i in range(0, len(response), 1900)]
        for part in parts:
            await interaction.followup.send(part, ephemeral=True)
    else:
        await interaction.followup.send(response, ephemeral=True)

# Run the bot
bot.run(os.getenv('DISCORD_TOKEN')) 