import discord
import asyncio
import aiohttp
import random
import config
from random import randint
from datetime import datetime, timedelta

# --- 1. Ana Pokémon Sınıfı ---
class Pokemon:
    pokemons = {}  

    def __init__(self, pokemon_trainer):
        self.pokemon_trainer = pokemon_trainer
        self.pokemon_number = random.randint(1, 1000)
        self.name = None
        self.img = None
        self.power = random.randint(30, 60)
        self.hp = random.randint(200, 400)
        
        # GÖREV: Son beslenme zamanını tutan nitelik
        self.last_feed_time = datetime.now()
        
        # Pokémon'u eğitmene zimmetle (Eskisi varsa üzerine yazar)
        Pokemon.pokemons[pokemon_trainer] = self

    async def get_name(self):
        url = f'https://pokeapi.co/api/v2/pokemon/{self.pokemon_number}'
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['forms'][0]['name'].capitalize()
                return "Pikachu"

    async def info(self):
        if not self.name:
            self.name = await self.get_name()
        return f"👾 **Pokémon ismi:** {self.name}\n⚔️ **Gücü:** {self.power}\n❤️ **Sağlığı:** {self.hp}"

    async def show_img(self):
        url = f'https://pokeapi.co/api/v2/pokemon/{self.pokemon_number}'
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['sprites']['front_default']
                return None

    # GÖREV: Besleme metodu
    async def feed(self, feed_interval=60, recovery=20):
        now = datetime.now()
        next_feed_time = self.last_feed_time + timedelta(seconds=feed_interval)
        
        if now >= next_feed_time:
            self.hp += recovery
            self.last_feed_time = now
            return f"🍎 **{self.name}** beslendi! Sağlık +{recovery} arttı. Mevcut HP: {self.hp}"
        else:
            wait_time = (next_feed_time - now).seconds
            return f"⏳ Pokémonun tok! Tekrar beslemek için **{wait_time}** saniye beklemen gerek."

    async def attack(self, enemy):
        if isinstance(enemy, Wizard):
            if randint(1, 5) == 1:
                return f"🛡️ **{enemy.name}** bir kalkan kullandı! Saldırı engellendi!"

        if enemy.hp > self.power:
            enemy.hp -= self.power
            return f"💥 **@{self.pokemon_trainer}**, **@{enemy.pokemon_trainer}**'na saldırdı!\n💢 **{enemy.name}** kalan sağlık: {enemy.hp}"
        else:
            enemy.hp = 0
            return f"🏆 **@{self.pokemon_trainer}**, **@{enemy.pokemon_trainer}**'nı yendi!"

# --- 2. Çocuk Sınıflar ---

class Wizard(Pokemon):
    async def info(self):
        return "🧙‍♂️ **Sihirbaz Pokémonunuzun durumu:**\n" + await super().info()
    
    async def feed(self):
        # Çok biçimlilik: Sihirbaz 30 saniyede bir yiyebilir
        return await super().feed(feed_interval=30)

class Fighter(Pokemon):
    async def attack(self, enemy):
        super_power = randint(5, 15)
        self.power += super_power
        result = await super().attack(enemy)
        self.power -= super_power
        return result + f"\n⚡ **Dövüşçü süper saldırı kullandı! (+{super_power} Güç)**"
    
    async def feed(self):
        # Çok biçimlilik: Dövüşçü 50 HP kazanır
        return await super().feed(recovery=50)

# --- 3. Bot Sınıfı ---
class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.aktif_savaslar = {} 

    async def on_ready(self):
        print(f'✅ Bot {self.user} olarak giriş yaptı!')

    async def on_message(self, message):
        if message.author == self.user:
            return

        msg = message.content.lower()
        trainer_name = message.author.name 

        # --- Pokémon Yakala ---
        if msg == '!go':
            sinif = random.choice([Wizard, Fighter])
            yeni_pokemon = sinif(trainer_name)
            
            await message.channel.send(await yeni_pokemon.info())
            img_url = await yeni_pokemon.show_img()
            if img_url: 
                await message.channel.send(img_url)
            return # ÖNEMLİ: İşlem bitti, aşağıya devam etme!

        # --- Pokémon Bilgisi ---
        if msg == '!info':
            if trainer_name in Pokemon.pokemons:
                pok = Pokemon.pokemons[trainer_name]
                await message.channel.send(await pok.info())
                img_url = await pok.show_img()
                if img_url: await message.channel.send(img_url)
            else:
                await message.channel.send("⚠️ Önce `!go` yazmalısın.")
            return

        # --- Pokémon Besleme ---
        if msg == '!feed':
            if trainer_name in Pokemon.pokemons:
                pok = Pokemon.pokemons[trainer_name]
                await message.channel.send(await pok.feed())
            else:
                await message.channel.send("⚠️ Besleyecek bir Pokémonun yok!")
            return

        # --- Antrenman ---
        if msg == '!antrenman':
            if trainer_name in Pokemon.pokemons:
                vahsi_sinif = random.choice([Wizard, Fighter])
                bot_rakip = vahsi_sinif("Vahşi Bot")
                self.aktif_savaslar[trainer_name] = bot_rakip
                await message.channel.send(f"🌲 Vahşi bir Pokémon belirdi!")
                await message.channel.send(await bot_rakip.info())
                img_url = await bot_rakip.show_img()
                if img_url: await message.channel.send(img_url)
                await message.channel.send("\n⚔️ Vurmak için **`!saldır`** yaz!")
            else:
                await message.channel.send("⚠️ Önce bir Pokémon almalısın!")
            return

        # --- Saldırı ---
        if msg == '!saldır':
            if trainer_name in self.aktif_savaslar:
                p1 = Pokemon.pokemons[trainer_name]
                bot_rakip = self.aktif_savaslar[trainer_name]
                await message.channel.send(await p1.attack(bot_rakip))

                if bot_rakip.hp <= 0:
                    await message.channel.send("🎉 Kazandın!")
                    del self.aktif_savaslar[trainer_name]
                else:
                    await asyncio.sleep(1)
                    await message.channel.send(f"⚠️ **{bot_rakip.name}** saldırıyor!")
                    await message.channel.send(await bot_rakip.attack(p1))
                    if p1.hp <= 0:
                        await message.channel.send("💀 Bayıldın! `!feed` kullan.")
                        del self.aktif_savaslar[trainer_name]
            return

        if msg == '!heal':
            if trainer_name in Pokemon.pokemons:
                Pokemon.pokemons[trainer_name].hp = 400 
                await message.channel.send("🧪 Pokémonun tamamen iyileşti!")
            return

# Başlatma
intents = discord.Intents.default()
intents.message_content = True
client = MyClient(intents=intents)
client.run(config.token)
