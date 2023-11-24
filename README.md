# bot_rt
Contient le code source du bot Carbo 3000 de l'intégration discord "bot_rt". Destiné au département R&T de l'IUT de Béthune.

Le programme Python est directement commenté.

Les données (str) nécessaires à son execution sont :

- BOT_TOKEN : Le token de votre bot* Discord qui sera utilisé. (cf. https://www.ionos.fr/digitalguide/serveur/know-how/creer-un-bot-discord).
- GUILD_ID_BETHUNE : L'ID du serveur R&T disponible directement dans Discord. (ou celui de votre propre serveur)

Ces données sont à indiquer dans un fichier 'data.json' comprenant les mêmes clés précedentes, et se trouvant dans le même dossier que le programme python.

*Le numéro des permissions du bot utilisé doit être 1084479765568, à indiquer dans l'url generator. (cf. https://discord.com/developers)
