import discord
import asyncio
import config # Kendi dosyamızdan token çekiyoruz

# Ek Görev için Car Sınıfı
class Car:
    def __init__(self, marka, renk):
        self.marka = marka
        self.renk = renk
    
    def ozellikleri_soyle(self):
        return f"🚗 Arabanız hazır! Marka: {self.marka}, Renk: {self.renk}"

class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def setup_hook(self) -> None:
        # Arka plan görevini başlatır
        self.bg_task = self.loop.create_task(self.my_background_task())

    async def on_ready(self):
        print(f'Giriş yapıldı: {self.user} (ID: {self.user.id})')

    async def my_background_task(self):
        await self.wait_until_ready()
        counter = 0
        # BURAYA KENDİ KANAL ID'Nİ YAZMALISIN (Örn: 123456789)
        channel = self.get_channel(123456789) 

        if channel and isinstance(channel, discord.abc.Messageable):
            while not self.is_closed():
                counter += 1
                # Sayacı kanala gönderir (Her 60 saniyede bir)
                # await channel.send(f"Sayaç: {counter}") 
                await asyncio.sleep(60)

    # Mesaj işleyicisi (on_message)
    async def on_message(self, message):
        # Botun kendi mesajlarına cevap vermesini engeller
        if message.author == self.user:
            return

        # Merhaba komutu
        if message.content.lower().startswith('merhaba'):
            await message.channel.send('LAHMACUN İSTİYOM')

        # Ek Görev: /araba marka renk
        if message.content.startswith('/araba'):
            try:
                # Mesajı boşluklardan ayırıyoruz: ['/araba', 'BMW', 'Mavi']
                parcalar = message.content.split()
                marka = parcalar[1]
                renk = parcalar[2]
                
                # Sınıf örneği oluşturma
                yeni_araba = Car(marka, renk)
                await message.channel.send(yeni_araba.ozellikleri_soyle())
            except IndexError:
                await message.channel.send('Lütfen şu formatta yazın: `/araba Marka Renk`')

# Yetkileri ayarla
intents = discord.Intents.default()
intents.message_content = True

# Botu başlat
client = MyClient(intents=intents)
client.run(config.token)