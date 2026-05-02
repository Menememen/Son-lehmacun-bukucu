import discord
import asyncio
import aiohttp
import random
import config

# --- 1. Ana Pokémon Sınıfı ---
class Pokemon:
    def __init__(self, pokemon_number, pokemon_trainer):
        self.pokemon_number = pokemon_number
        self.pokemon_trainer = pokemon_trainer
        self.name = "Bilinmiyor"
        self.img = ""
        self.hp = random.randint(70, 100) 
        self.power = random.randint(10, 20)
        self.abilities = []

    async def fetch_data(self):
        url = f'https://pokeapi.co/api/v2/pokemon/{self.pokemon_number}'
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    self.name = data['name'].capitalize()
                    self.img = data['sprites']['front_default']
                    self.abilities = [a['ability']['name'] for a in data['abilities']]
                    return True
                return False

    def get_info(self):
        return (f"👾 **İsim:** {self.name}\n"
                f"❤️ **Sağlık (HP):** {self.hp}\n"
                f"⚔️ **Güç:** {self.power}")

    async def attack(self, enemy):
        # Sihirbaz Kalkan Kontrolü
        if isinstance(enemy, Wizard):
            if random.randint(1, 5) == 1:
                return f"🛡️ **{enemy.name}** bir sihirli kalkan kullandı! Saldırı engellendi!"

        if enemy.hp > self.power:
            enemy.hp -= self.power
            return (f"💥 **@{self.pokemon_trainer}**, **@{enemy.pokemon_trainer}**'na saldırdı!\n"
                    f"💢 **{enemy.name}** kalan sağlık: {enemy.hp}")
        else:
            enemy.hp = 0
            self.hp += 10 # Kazanan bonusu
            return (f"🏆 **@{self.pokemon_trainer}**, **@{enemy.pokemon_trainer}**'nı yendi!\n"
                    f"🎁 Bonus: {self.name} 10 HP yeniledi!")

# --- 2. Çocuk Sınıflar ---

class Wizard(Pokemon):
    def __init__(self, pokemon_number, pokemon_trainer):
        super().__init__(pokemon_number, pokemon_trainer)
        self.hp += random.randint(20, 40)

    def get_info(self):
        return "🧙‍♂️ **Sihirbaz Pokémonunuz var!**\n" + super().get_info()

class Fighter(Pokemon):
    def __init__(self, pokemon_number, pokemon_trainer):
        super().__init__(pokemon_number, pokemon_trainer)
        self.power += random.randint(10, 15)

    def get_info(self):
        return "🥊 **Dövüşçü Pokémonunuz var!**\n" + super().get_info()

    async def attack(self, enemy):
        super_guc = random.randint(5, 15)
        self.power += super_guc
        sonuc = await super().attack(enemy)
        self.power -= super_guc
        return sonuc + f"\n⚡ **Dövüşçü süper saldırı kullandı! (+{super_guc} Güç)**"

# --- 3. Bot Sınıfı ---
class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.oyuncular = {}
        # SİLMEDEN EKLEDİĞİMİZ KISIM: Aktif savaşları takip etmek için sözlük
        self.aktif_savaslar = {}

    async def on_ready(self):
        print(f'✅ Bot {self.user} olarak giriş yaptı!')

    async def on_message(self, message):
        if message.author == self.user:
            return

        msg = message.content.lower()

        # Pokémon Yakala
        if msg == '!go':
            pokemon_id = random.randint(1, 151)
            sinif = random.choice([Wizard, Fighter])
            yeni_pokemon = sinif(pokemon_id, message.author.display_name)
            
            if await yeni_pokemon.fetch_data():
                self.oyuncular[message.author.id] = yeni_pokemon
                await message.channel.send(yeni_pokemon.get_info())
                await message.channel.send(yeni_pokemon.img)

        # Bot ile Antrenman Yap (DÜZENLENEN KISIM: Sadece savaşı başlatır)
        if msg == '!antrenman':
            if message.author.id in self.oyuncular:
                p1 = self.oyuncular[message.author.id]
                
                # Vahşi rakip oluştur
                vahsi_id = random.randint(1, 151)
                vahsi_sinif = random.choice([Wizard, Fighter])
                bot_rakip = vahsi_sinif(vahsi_id, "Vahşi Bot")
                
                if await bot_rakip.fetch_data():
                    # Savaşı hafızaya alıyoruz
                    self.aktif_savaslar[message.author.id] = bot_rakip
                    
                    await message.channel.send(f"🌲 Çalılıkların arasından vahşi bir **{bot_rakip.name}** çıktı!")
                    await message.channel.send(bot_rakip.img)
                    await message.channel.send(bot_rakip.get_info())
                    await message.channel.send("\n⚔️ **Senin hamlen bekleniyor!** Bota vurmak için **`!saldır`** yaz!")
                else:
                    await message.channel.send("⚠️ Vahşi Pokémon bulunamadı.")
            else:
                await message.channel.send("⚠️ Önce bir Pokémon almalısın! `!go` yaz!")

        # YENİ EKLEDİĞİMİZ KOMUT: Bizzat senin vurmanı sağlar
        if msg == '!saldır':
            if message.author.id in self.aktif_savaslar:
                p1 = self.oyuncular[message.author.id]
                bot_rakip = self.aktif_savaslar[message.author.id]

                # 1. Sen saldırıyorsun
                await message.channel.send(f"⚔️ **{p1.pokemon_trainer}** saldırıyor!")
                await message.channel.send(await p1.attack(bot_rakip))

                # Eğer bot öldüyse savaşı bitir
                if bot_rakip.hp <= 0:
                    await message.channel.send(f"🎉 **{bot_rakip.name}** yenildi! Antrenman bitti.")
                    del self.aktif_savaslar[message.author.id]
                else:
                    # 2. Bot yaşıyorsa o saldırıyor
                    await asyncio.sleep(1)
                    await message.channel.send(f"⚠️ **{bot_rakip.name}** karşı atağa geçiyor!")
                    await message.channel.send(await bot_rakip.attack(p1))

                    # Eğer sen öldüysen savaşı bitir
                    if p1.hp <= 0:
                        await message.channel.send("💀 Pokémonun bayıldı! `!heal` yazarak iyileşmelisin.")
                        del self.aktif_savaslar[message.author.id]
            else:
                await message.channel.send("❌ Şu an aktif bir antrenman yok. `!antrenman` yazarak başlatabilirsin.")

        # İyileşme
        if msg == '!heal':
            if message.author.id in self.oyuncular:
                p = self.oyuncular[message.author.id]
                # Canı tam doldurmak için güncelledim
                p.hp = 100 
                await message.channel.send(f"🧪 {p.name} tamamen iyileşti! Mevcut HP: {p.hp}")

# Başlatma
intents = discord.Intents.default()
intents.message_content = True
client = MyClient(intents=intents)
client.run(config.token)
