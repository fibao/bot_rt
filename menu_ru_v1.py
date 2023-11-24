import json
import discord
from discord.ext import commands
import requests
from bs4 import BeautifulSoup
import datetime as dt
import asyncio
import random

#Importation data
with open("data.json", "r") as f: data = json.load(f)
BOT_TOKEN = data["BOT_TOKEN"]

##### CONFIGIRATION SERVEUR DISCORD #####
#Changer ce nom pour choisir le serveur
SERVER_NAME = "R&T Béthune"

if SERVER_NAME == 'R&T Béthune': 
    GUILD_ID = data["GUILD_ID_BETHUNE"]
    ROLE_ADMIN = "Admin"
    ROLE_A_PING = "Carbo"
    CHANNEL_NAME = '🍝menu-ru'
elif SERVER_NAME == 'La Matrice': 
    GUILD_ID = data["GUILD_ID_MATRICE"]
    ROLE_ADMIN = "Admin"
    ROLE_A_PING = "Amis"
    CHANNEL_NAME = '🍝menu-ru'

##### CONFIGIRATION RESEAU #####
#OLD_HTML_URL = 'https://www.crous-lille.fr/restaurant/r-u-schweitzer-bethune-2/'
HTML_URL = 'https://www.crous-lille.fr/restaurant/r-u-schweitzer-bethune/'
PROXY_ACTIF = False
PROXY = {
    "http": "http://cache-etu.univ-artois.fr:3128",
    "https": "http://cache-etu.univ-artois.fr:3128",
}

##### PREFERENCES  #####
DEBUG_ACTIF = False #Print plus d'information ?
COLOR_TODAY = False #Colorier le menu d'aujourd'hui en vert ? (Marche incorrectement lorsque les carbonara sont aujourd'hui)
HEURE_DE_RECUPERATION = 9 #Heure à laquelle l'update est effectuée chaque lundi (le bot doit être lancé et la commande 'menu' executée)
PURGE_ON_STOP = False #Effacer tous les messages du channel menu-ru avant l'arrêt du bot, lors la commande 'stop' ?

def recuperation() -> list:
    """
    Récupère le menu de la semaine actuelle.
    Renvoie sous forme de liste, contenant les 1,2,3,4 ou 5 jours de la semaine.
    """

    if DEBUG_ACTIF: print("DEBUG INFO : Récupération html...")
    if PROXY_ACTIF: page = requests.get(HTML_URL, proxies=PROXY)
    else: page = requests.get(HTML_URL)
    soup = BeautifulSoup(page.content, 'html.parser')
    uls = soup.find_all('ul', class_='meal_foodies')

    if DEBUG_ACTIF: print("DEBUG INFO : Traitement html...")
    menu = []
    for ul in uls:
        if ul:
            jour = ul.find_all('li')
            jour = [str(jour).replace("<li>", " ").replace("</li>", " ").replace("<ul>", " ").replace("</ul>", " ").replace("  ", " ")[1:-1].lower() for jour in jour if jour != None]
            jour = [plat for plat in jour if len(plat) >= 45] #Garde uniquement les 2 lignes principales du menu et non les petites lignes
            menu.append(jour)
    
    if len(menu) != 5 - dt.datetime.now().weekday(): print(f"!! : Nombre de jour récupéré erroné ({len(menu)}).")
    if DEBUG_ACTIF: print("DEBUG INFO : menu =\n", menu)
    return menu


def carbonara(menu:list) -> list|None:
    """
    Renvoie le ou les jours de carbonara.
    Si n'existe pas, return None.
    """

    jour_carbonara = [menu.index(jour) for jour in menu if 'carbonara' in ' '.join(jour)]

    if len(jour_carbonara) != 0: return jour_carbonara
    else: return None


def prochain_lundi(HEURE_DE_RECUPERATION:int) -> dt.datetime:
    """
    Renvoie un datetime égal au temps restant avant le prochain lundi, à partir de HEURE_DE_RECUPERATION heures.
    """

    maintenant = prochain_lundi = dt.datetime.now()

    if prochain_lundi.weekday() == 0: prochain_lundi += dt.timedelta(days=7)
    else:
        while prochain_lundi.weekday() != 0: prochain_lundi += dt.timedelta(days=1)

    prochain_lundi = prochain_lundi.replace(hour=HEURE_DE_RECUPERATION, minute=0, second=0, microsecond=0)
    temps_restant = prochain_lundi - maintenant

    return temps_restant


def dernier_lundi() -> str:
    """
    Renvoi la date du lundi de la semaine actuelle (le dernier lundi)
    """
    aujourd_hui = dt.datetime.now()

    if aujourd_hui.weekday() == 0: return aujourd_hui.strftime("%d/%m")
    
    else:
        jours_jusqu_au_lundi = (aujourd_hui.weekday() - 0) % 7
        difference = dt.timedelta(days=jours_jusqu_au_lundi)

        return (aujourd_hui - difference).strftime("%d/%m")


def run_discord_bot() -> None:
    """
    Créer et configure le bot (droits, variables, commandes),
    puis enfin le lance
    """

    #Création du bot
    intents = discord.Intents.default()
    intents.typing = True
    intents.presences = False
    intents.message_content = True #Droit obligatoire
    client = commands.Bot(command_prefix="!", intents=intents)
    
    #Variables / Constantes utilisées par le bot
    ACTIVITES = (
            "Cuit les pâtes...",
            "Cherche les lardons...",
            "Fait chauffer l'eau...",
            "Lance un minuteur...",
            "Soupoudre de parmesan...",
            "Sépare le jaune d'oeuf..."
        )
    
    running = True

    @client.event
    #Au lancement du bot...
    async def on_ready():
        await client.wait_until_ready()
        await activite_update()
        print(f"INFO : Bot connecté en tant que {client.user.name}.")

    #Changement de l'état actuel à la connexion
    async def activite_update():
        await client.change_presence(activity=discord.CustomActivity(ACTIVITES[random.randint(0,len(ACTIVITES) - 1)]))

    @client.command()
    async def menu(ctx):
        """
        Permet d'afficher le menu de la semaine au RU. Affiche uniquement le menu d'ajourd'hui à vendredi.
        Ping également le groupe 'Carbo' pour indiquer si des carbonaras sont prévus (max 2 jours).
        A utiliser dans le chanel 'menu-ru' par un Admin ou BDE. Efface tous les messages de ce chanel à l'utilisation si activé.
        Vérifier que le RU ne ferme pas dans les prochains jours en cas de problèmes, ou que le page web est toujours présente.
        """
        await client.wait_until_ready()
        
        if str(ctx.channel) == CHANNEL_NAME and ROLE_ADMIN in [str(role) for role in ctx.message.author.roles]:
            print("INFO : menu !")
            
            role_a_ping = discord.utils.get(ctx.guild.roles, name=ROLE_A_PING)
            role_admin = discord.utils.get(ctx.guild.roles, name=ROLE_ADMIN)
            
            while running:
                semaine = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"][dt.datetime.now().weekday():]

                menu = recuperation()
                if len(menu) != 5 - dt.datetime.now().weekday():
                    await ctx.send(f"{role_admin.mention}, erreur dans la récupération du menu. Le RU est-il ouvert ?")
                    break

                try:
                    await ctx.channel.purge(limit=None)
                except discord.Forbidden:
                    await print("!! : Impossible d'effacer les messages précedent (Forbidden).")

                if DEBUG_ACTIF: print("DEBUG INFO : Affichage résultats...")
                try:
                    await ctx.send(f"Menu du RU de la semaine du {dernier_lundi()} :")
                except discord.Forbidden:
                    await print(f"{role_admin.mention}, impossible d'écrire dans le channel (Forbidden).")

                for jour in semaine:
                    reponse = f"```ansi\n[1;2m[1;32m{jour}[0m[0m\n```"
                    menu_du_jour = '\n'.join(menu[semaine.index(jour)])
                    
                    if COLOR_TODAY:
                        #Réponse couleur aujourd'hui
                        if dt.datetime.now().weekday() == semaine.index(jour) + dt.datetime.now().weekday(): reponse += (f"```ansi\n[0;2m[0;34m[0;34m[0;35m[0;36m{menu_du_jour}[0m[0;36m[0m[0;35m[0m[0;34m[0m[0;34m[0m[0m[4;2m[1;2m[1;2m[4;2m[0;2m[0m[0m[0m[0m[0m\n```").replace("carbonara", "[1;34m[1;37mcarbonara[0m[1;34m[0m[0;34m")
                        #Réponse couleur pas aujourd'hui
                        else: reponse += (f"```ansi\n[0;2m[0;34m{menu_du_jour}[0m[0m[4;2m[1;2m[1;2m[4;2m[0;2m[0m[0m[0m[0m[0m\n```").replace("carbonara", "[1;34m[1;37mcarbonara[0m[1;34m[0m[0;34m")
                    else:
                        reponse += (f"```ansi\n[0;2m[0;34m{menu_du_jour}[0m[0m[4;2m[1;2m[1;2m[4;2m[0;2m[0m[0m[0m[0m[0m\n```").replace("carbonara", "[1;34m[1;37mcarbonara[0m[1;34m[0m[0;34m")

                    await ctx.send(reponse)
                
                jour_carbonara = carbonara(menu)
                if jour_carbonara == None: await ctx.send(f"{role_a_ping.mention}, vous allez passer les pires jours de votre vie. La carbonara n'est plus...")
                elif len(jour_carbonara) == 1: await ctx.send(f"{role_a_ping.mention}, le meilleur jour de cette semaine est **{semaine[jour_carbonara[0]]}** !")
                elif len(jour_carbonara) == 2: await ctx.send(f"{role_a_ping.mention}, les meilleurs jours de cette semaine sont **{semaine[jour_carbonara[0]]}** et **{semaine[jour_carbonara[1]]}** !")
                else:
                    await ctx.send(f"{role_admin.mention}, erreur dans le jour des carbonara :")
                    await ctx.send(f"{len(jour_carbonara)} not in (1, 2)")

                delta_t = prochain_lundi(HEURE_DE_RECUPERATION)
                #delta_t = dt.timedelta(minutes=1)
                print(f"INFO : Mise en veille durant {delta_t}. ({round(delta_t.total_seconds())} secondes)...\n")
                await ctx.send(f"||Update du menu dans {delta_t}. ({round(delta_t.total_seconds())} secondes)...||")
                await asyncio.sleep(round(delta_t.total_seconds()))
    
    #Commande d'arrêt du bot
    @client.command()
    async def stop(ctx):
        """
        Permet d'arrêter le programme du bot 'Carbo 3000'.
        A utiliser dans le chanel 'menu-ru' par un Admin ou BDE. Efface tous les messages de ce chanel à l'utilisation si activé.
        Attention, aucune commande ne permet de relancer le bot après un '!stop'. Il faudra relancer le programme manuellement.
        """

        await client.wait_until_ready()
        if str(ctx.channel) == CHANNEL_NAME and ROLE_ADMIN in [str(role) for role in ctx.message.author.roles]:
            print("WARNING : Arrêt du bot...")

            if PURGE_ON_STOP:
                try:
                    await ctx.channel.purge(limit=None)
                except discord.Forbidden:
                    await print("!! : Impossible d'effacer les messages précedent (Forbidden).")
            
            try:
                role_admin = discord.utils.get(ctx.guild.roles, name=ROLE_ADMIN)
                await ctx.send(f"{role_admin.mention}, arrêt du bot...")
                await client.close()
            except RuntimeError:
                await print("! RuntimeError: Event loop is closed.")

            await print("INFO : Bot arrêté correctement.")

    client.run(BOT_TOKEN)

run_discord_bot()
