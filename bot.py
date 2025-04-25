import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from enum import Enum

# Konfiguracja intencji bota
intents = discord.Intents.default()
intents.message_content = True  # Pozwala na czytanie treści wiadomości
intents.members = True         # Pozwala na dostęp do informacji o członkach serwera
intents.guilds = True         # Pozwala na dostęp do informacji o serwerze
intents.guild_messages = True  # Pozwala na czytanie wiadomości na serwerze

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
    Sprawdza czy użytkownik jest zatrudniony (ma rolę Pracownik)
    """
    pracownik_role = member.guild.get_role(Role.PRACOWNIK)
    
    # Debugowanie
    print(f"\n=== Sprawdzanie zatrudnienia dla {member.name} ===")
    print(f"ID użytkownika: {member.id}")
    print(f"Role użytkownika: {[role.name for role in member.roles]}")
    print(f"ID roli Pracownik: {Role.PRACOWNIK}")
    print(f"Znaleziona rola Pracownik: {pracownik_role}")
    if pracownik_role:
        print(f"Czy ma rolę Pracownik: {pracownik_role in member.roles}")
    else:
        print("Nie znaleziono roli Pracownik na serwerze!")
    print("=" * 50)
    
    return pracownik_role in member.roles

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

async def dodaj_punkt(interaction: discord.Interaction, member: discord.Member, typ: str, powod: str) -> bool:
    """
    Dodaje punkt określonego typu (plus/minus/upomnienie) pracownikowi.
    Zwraca True jeśli osiągnięto 3 punkty.
    """
    if not czy_ma_uprawnienia_do_zarzadzania(interaction.user):
        await interaction.response.send_message("❌ Nie masz uprawnień do zarządzania punktami!", ephemeral=True)
        return False

    if not czy_jest_zatrudniony(member):
        await interaction.response.send_message(f"❌ {member.mention} nie jest zatrudniony!", ephemeral=True)
        return False

    await interaction.response.defer()

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
    
    pracownik = pracownicy[str(member.id)]
    
    # Dodaj punkt odpowiedniego typu
    pracownik[typ] += 1
    current_points = pracownik[typ]
    
    # Przygotuj odpowiedni emoji i wiadomość
    emoji_map = {"plusy": "✅", "minusy": "❌", "upomnienia": "⚠️"}
    emoji = emoji_map.get(typ, "ℹ️")
    typ_pojedynczy = {"plusy": "plus", "minusy": "minus", "upomnienia": "upomnienie"}.get(typ, typ)

    # Określ role do zarządzania
    if typ == "plusy":
        role_ids = [Role.PLUS1, Role.PLUS2, Role.PLUS3]
    elif typ == "minusy":
        role_ids = [Role.MINUS1, Role.MINUS2, Role.MINUS3]
    else:  # upomnienia
        role_ids = [Role.UPOMNIENIE1, Role.UPOMNIENIE2, Role.UPOMNIENIE3]

    try:
        # Usuń wszystkie role punktowe tego typu
        roles_to_remove = []
        for role_id in role_ids:
            role = interaction.guild.get_role(role_id)
            if role and role in member.roles:
                roles_to_remove.append(role)
        
        if roles_to_remove:
            await member.remove_roles(*roles_to_remove)

        # Dodaj odpowiednią rolę punktową (tylko jeśli nie osiągnięto limitu)
        if current_points > 0 and current_points <= 3 and not (current_points == 3):
            role = interaction.guild.get_role(role_ids[current_points - 1])
            if role:
                await member.add_roles(role)
    except discord.Forbidden:
        await interaction.followup.send("❌ Bot nie ma uprawnień do zarządzania rolami!")
        return False
    except Exception as e:
        await interaction.followup.send(f"❌ Wystąpił błąd podczas zarządzania rolami: {str(e)}")
        return False
    
    # Zapisz zmiany
    zapisz_pracownikow()
    
    # Sprawdź czy osiągnięto 3 punkty
    if current_points >= 3:
        # Wyślij powiadomienie o osiągnięciu 3 punktów
        await interaction.followup.send(
            f"{emoji} **{member.mention} osiągnął(a) 3 {typ}!**\n"
            f"Powód ostatniego punktu: {powod}\n"
            f"Licznik {typ} został wyzerowany."
        )

        # Usuń wszystkie role punktowe tego typu
        roles_to_remove = []
        for role_id in role_ids:
            role = interaction.guild.get_role(role_id)
            if role and role in member.roles:
                roles_to_remove.append(role)
        
        if roles_to_remove:
            try:
                await member.remove_roles(*roles_to_remove)
                print(f"Usunięto role {[role.name for role in roles_to_remove]} dla {member.name}")
            except Exception as e:
                print(f"Błąd podczas usuwania ról: {str(e)}")

        # Wyzeruj licznik
        pracownik[typ] = 0
        zapisz_pracownikow()

        return True
    else:
        # Wyślij normalne powiadomienie
        await interaction.followup.send(
            f"{emoji} Dodano {typ_pojedynczy} dla {member.mention}\n"
            f"Powód: {powod}\n"
            f"Aktualna liczba {typ}: {current_points}"
        )
        return False

# Komenda do dodawania plusów
@bot.tree.command(name="plus", description="Dodaje plus pracownikowi")
@app_commands.describe(
    member="Pracownik, któremu chcesz dodać plus",
    powod="Powód przyznania plusa"
)
async def slash_plus(interaction: discord.Interaction, member: discord.Member, powod: str):
    try:
        # Sprawdź uprawnienia
        if not czy_ma_uprawnienia_do_zarzadzania(interaction.user):
            await interaction.response.send_message("❌ Nie masz uprawnień do zarządzania plusami!", ephemeral=True)
            return

        # Sprawdź czy pracownik istnieje w systemie
        if str(member.id) not in pracownicy:
            await interaction.response.send_message(f"❌ {member.mention} nie jest zatrudniony!", ephemeral=True)
            return

        # Dodaj plus
        osiagnieto_limit = await dodaj_punkt(interaction, member, "plusy", powod)
        
        # Jeśli osiągnięto limit 3 plusów, wyślij dodatkowe powiadomienie
        if osiagnieto_limit:
            await interaction.followup.send(f"🎉 **Gratulacje!** {member.mention} otrzymał(a) 3 plusy! To świetny wynik!")
            
    except Exception as e:
        print(f"Błąd podczas wykonywania komendy plus: {str(e)}")
        if not interaction.response.is_done():
            await interaction.response.send_message(f"Wystąpił błąd podczas wykonywania komendy: {str(e)}", ephemeral=True)
        else:
            await interaction.followup.send(f"Wystąpił błąd podczas wykonywania komendy: {str(e)}", ephemeral=True)

# Komenda do dodawania minusów
@bot.tree.command(name="minus", description="Dodaje minus pracownikowi")
@app_commands.describe(
    member="Pracownik, któremu chcesz dodać minus",
    powod="Powód przyznania minusa"
)
async def slash_minus(interaction: discord.Interaction, member: discord.Member, powod: str):
    try:
        # Sprawdź uprawnienia
        if not czy_ma_uprawnienia_do_zarzadzania(interaction.user):
            await interaction.response.send_message("❌ Nie masz uprawnień do zarządzania minusami!", ephemeral=True)
            return

        # Sprawdź czy pracownik istnieje w systemie
        if str(member.id) not in pracownicy:
            await interaction.response.send_message(f"❌ {member.mention} nie jest zatrudniony!", ephemeral=True)
            return

        # Dodaj minus
        osiagnieto_limit = await dodaj_punkt(interaction, member, "minusy", powod)
        
        # Jeśli osiągnięto limit 3 minusów, wyślij dodatkowe powiadomienie
        if osiagnieto_limit:
            await interaction.followup.send(f"⚠️ **UWAGA!** {member.mention} otrzymał(a) 3 minusy! Rozważ podjęcie odpowiednich działań.")
            
    except Exception as e:
        print(f"Błąd podczas wykonywania komendy minus: {str(e)}")
        if not interaction.response.is_done():
            await interaction.response.send_message(f"Wystąpił błąd podczas wykonywania komendy: {str(e)}", ephemeral=True)
        else:
            await interaction.followup.send(f"Wystąpił błąd podczas wykonywania komendy: {str(e)}", ephemeral=True)

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

# Komenda do awansowania pracowników
@bot.tree.command(name="awansuj", description="Awansuje pracownika na nowe stanowisko")
@app_commands.describe(
    member="Pracownik do awansowania",
    sciezka="Ścieżka awansu",
    poziom="Poziom awansu (1-6, gdzie 1 to najniższy poziom)"
)
@app_commands.choices(sciezka=[
    app_commands.Choice(name="Ochrona", value="ochrona"),
    app_commands.Choice(name="Gastronomia", value="gastronomia")
])
async def slash_awansuj(
    interaction: discord.Interaction, 
    member: discord.Member, 
    sciezka: str,
    poziom: app_commands.Range[int, 1, 6]
):
    try:
        # Sprawdź uprawnienia
        if not czy_ma_uprawnienia_do_zarzadzania(interaction.user):
            await interaction.response.send_message(
                "❌ Nie masz uprawnień do awansowania pracowników!", 
                ephemeral=True
            )
            return

        # Sprawdź czy pracownik jest zatrudniony
        if not czy_jest_zatrudniony(member):
            await interaction.response.send_message(
                f"❌ {member.mention} nie jest zatrudniony! Najpierw użyj komendy /job aby zatrudnić pracownika.",
                ephemeral=True
            )
            return

        await interaction.response.defer()

        # Walidacja parametrów
        sciezka = sciezka.lower()
        if sciezka not in ["ochrona", "gastronomia"]:
            await interaction.followup.send(
                "❌ Nieprawidłowa ścieżka! Wybierz 'ochrona' lub 'gastronomia'.",
                ephemeral=True
            )
            return

        if poziom < 1 or poziom > 6:
            await interaction.followup.send(
                "❌ Poziom awansu musi być między 1 a 6!",
                ephemeral=True
            )
            return

        if str(member.id) not in pracownicy:
            await interaction.followup.send(
                f"❌ {member.mention} nie jest zatrudniony!",
                ephemeral=True
            )
            return

        # Wybierz odpowiednią ścieżkę awansu
        if sciezka == "ochrona":
            sciezka_awansu = SCIEZKA_OCHRONY
            nazwa_sciezki = "Ochrona"
        elif sciezka == "gastronomia":
            sciezka_awansu = SCIEZKA_GASTRONOMII
            nazwa_sciezki = "Gastronomia"

        try:
            # Pobierz rolę do nadania
            nowa_rola_id = sciezka_awansu[poziom]
            nowa_rola = interaction.guild.get_role(nowa_rola_id)
            if not nowa_rola:
                await interaction.followup.send(f"❌ Nie mogę znaleźć roli dla poziomu {poziom}!")
                return

            # Usuń stare role ze ścieżki
            for rola_id in sciezka_awansu:
                if rola_id != nowa_rola_id:  # nie usuwaj nowej roli, jeśli już ją ma
                    rola = interaction.guild.get_role(rola_id)
                    if rola and rola in member.roles:
                        await member.remove_roles(rola)

            # Nadaj nową rolę
            await member.add_roles(nowa_rola)
            
            # Aktualizuj dane w systemie
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
                f"Poziom: {poziom}/6"
            )
                
        except discord.Forbidden:
            await interaction.followup.send(
                "❌ Bot nie ma uprawnień do zarządzania rolami!\n"
                "Upewnij się, że rola bota jest wyżej w hierarchii niż role, które próbuje nadawać."
            )
        except Exception as e:
            await interaction.followup.send(f"❌ Wystąpił błąd podczas zarządzania rolami: {str(e)}")
            print(f"Błąd podczas zarządzania rolami: {str(e)}")
            
    except Exception as e:
        error_msg = f"❌ Wystąpił błąd: {str(e)}"
        if not interaction.response.is_done():
            await interaction.response.send_message(error_msg, ephemeral=True)
        else:
            await interaction.followup.send(error_msg)
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
    powod="Powód degradacji"
)
async def slash_degrad(interaction: discord.Interaction, member: discord.Member, powod: str):
    if not czy_ma_uprawnienia_do_zarzadzania(interaction.user):
        await interaction.response.send_message("❌ Nie masz uprawnień do degradowania pracowników!", ephemeral=True)
        return

    await interaction.response.defer()

    if not czy_jest_zatrudniony(member):
        await interaction.followup.send(f"❌ {member.mention} nie jest zatrudniony!")
        return

    # Znajdź obecną rolę pracownika w ścieżkach awansu
    current_role = None
    current_path = None
    current_index = -1

    # Sprawdź ścieżkę ochrony
    for i, role_id in enumerate(SCIEZKA_OCHRONY):
        role = interaction.guild.get_role(role_id)
        if role and role in member.roles:
            current_role = role
            current_path = SCIEZKA_OCHRONY
            current_index = i
            break

    # Sprawdź ścieżkę gastronomii
    if current_role is None:
        for i, role_id in enumerate(SCIEZKA_GASTRONOMII):
            role = interaction.guild.get_role(role_id)
            if role and role in member.roles:
                current_role = role
                current_path = SCIEZKA_GASTRONOMII
                current_index = i
                break

    if current_role is None or current_index <= 0:
        await interaction.followup.send(f"❌ Nie można zdegradować {member.mention} - nie znaleziono odpowiedniej roli lub jest już na najniższym poziomie!")
        return

    try:
        # Usuń obecną rolę
        await member.remove_roles(current_role)
        
        # Nadaj niższą rolę
        new_role = interaction.guild.get_role(current_path[current_index - 1])
        await member.add_roles(new_role)
        
        # Aktualizuj dane w systemie
        pracownicy[str(member.id)]["rola"] = new_role.name
        pracownicy[str(member.id)]["historia_awansow"].append({
            "data": str(interaction.created_at.strftime("%Y-%m-%d %H:%M:%S")),
            "rola": new_role.name,
            "awansujacy": str(interaction.user),
            "typ": "degradacja",
            "powod": powod
        })
        
        zapisz_pracownikow()

        # Wyślij potwierdzenie
        embed = discord.Embed(
            title="⬇️ Degradacja",
            description=f"Pracownik {member.mention} został zdegradowany",
            color=0xff0000
        )
        embed.add_field(name="Nowa rola", value=new_role.name, inline=False)
        embed.add_field(name="Powód", value=powod, inline=False)
        embed.add_field(name="Od", value=interaction.user.mention, inline=False)
        
        await interaction.followup.send(embed=embed)
        
    except discord.Forbidden:
        await interaction.followup.send("❌ Bot nie ma uprawnień do zarządzania rolami!")
    except Exception as e:
        await interaction.followup.send(f"❌ Wystąpił błąd: {str(e)}")

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

# Wczytaj token ze zmiennej środowiskowej
print("=== Inicjalizacja bota ===")
TOKEN = os.environ.get('DISCORD_TOKEN')

if not TOKEN:
    print("❌ BŁĄD: Nie znaleziono tokenu w zmiennej środowiskowej DISCORD_TOKEN!")
    print("\nDostępne zmienne środowiskowe:")
    for key in os.environ.keys():
        print(f"- {key}")
    exit(1)

print("✅ Token został wczytany pomyślnie!")
print("🚀 Uruchamianie bota...")

# Uruchomienie bota
bot.run(TOKEN) 