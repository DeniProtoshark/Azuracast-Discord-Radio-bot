# Discord Radio Bot for AzuraCast
# Streams FLAC or MP3 from AzuraCast to a voice channel
# Supports volume control and channel selection


import discord
from discord import app_commands
import asyncio
import ffmpeg
import io


TOKEN = "Bla Bla Bla Token Bla Bla Bla"


STREAM_URL_FLAC = "Bla Bla Bla.flac"
STREAM_URL_MP3 = "Bla Bal Bla.mp3"


FFMPEG_SAMPLE_RATE = 48000  
FFMPEG_CHANNELS = 2         
FFMPEG_SAMPLE_FMT = 's16le' 

intents = discord.Intents.default()
intents.guilds = True
intents.voice_states = True

class RadioBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.current_volume = 0.5
        self.voice_client = None
        self.is_streaming = False

    async def on_ready(self):
        print(f"✅ Logged in as {self.user} (ID: {self.user.id})")
        try:
            await self.tree.sync()  
            print("✅ Slash-команды синхронизированы глобально.")
        except Exception as e:
            print(f"⚠️ Ошибка при синхронизации команд: {e}")

    async def on_guild_join(self, guild):
        try:
            await self.tree.sync(guild=guild)
            print(f"✅ Команды синхронизированы для нового сервера: {guild.name}")
        except Exception as e:
            print(f"⚠️ Ошибка при синхронизации на новом сервере: {e}")

bot = RadioBot()

@bot.tree.command(name="radio", description="Зайти в голосовой канал и стримить радио")
@app_commands.describe(channel="Имя голосового канала (или оставить пустым для текущего)")
async def radio(interaction: discord.Interaction, channel: str = None):
    guild = interaction.guild
    ch = None
    allowed_channel_id = 1422341130703339621
    allowed_channels = [c for c in guild.channels if isinstance(c, discord.VoiceChannel) or c.id == allowed_channel_id]

    if channel:
        for c in allowed_channels:
            if c.name.lower() == channel.lower() or str(c.id) == channel:
                ch = c
                break
    else:
        if interaction.user.voice and interaction.user.voice.channel in allowed_channels:
            ch = interaction.user.voice.channel

    if not ch:
        await interaction.response.send_message("❌ Можно выбрать только голосовой канал или трибуну.", ephemeral=True)
        return

    if bot.voice_client and bot.voice_client.is_connected():
        await bot.voice_client.disconnect()

    try:
        bot.voice_client = await ch.connect()

        if isinstance(ch, discord.StageChannel):
            me = guild.me or await guild.fetch_member(bot.user.id)
            try:
                await me.edit(suppress=False)
            except Exception as e:
                await interaction.response.send_message(f"⚠️ Не удалось стать спикером: {e}", ephemeral=True)
        await interaction.response.send_message(f"🎶 Подключился к {ch.name}. Начинаю стрим!")
        await start_stream(interaction, STREAM_URL_FLAC)
    except Exception as e:
        await interaction.response.send_message(f"❌ Ошибка подключения: {e}", ephemeral=True)

async def start_stream(interaction, stream_url):
    if not bot.voice_client:
        await interaction.followup.send("❌ Бот не в голосовом канале.")
        return

    ffmpeg_options = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': f'-vn -filter:a "volume={bot.current_volume}"'
    }
    audio_source = discord.FFmpegPCMAudio(stream_url, **ffmpeg_options)
    bot.voice_client.play(audio_source)
    bot.is_streaming = True

async def set_volume(interaction: discord.Interaction, percent: int):
    if percent < 0 or percent > 100:
        await interaction.response.send_message("❌ Громкость должна быть от 0 до 100%.", ephemeral=True)
        return

    bot.current_volume = percent / 100.0
    msg = f"🔊 Громкость установлена на {percent}%."

    if bot.voice_client and bot.voice_client.is_connected() and bot.is_streaming:
        bot.voice_client.stop()
        await start_stream(interaction, STREAM_URL_FLAC)
        msg += " Изменения применены сразу."
    else:
        msg += " Будет использована при следующем стриме."

    await interaction.response.send_message(msg)

@bot.tree.command(name="volume", description="Установить громкость (0–100%)")
@app_commands.describe(percent="Громкость от 0 до 100")
async def volume(interaction: discord.Interaction, percent: int):
    await set_volume(interaction, percent)

@bot.tree.command(name="vol", description="Синоним volume")
@app_commands.describe(percent="Громкость от 0 до 100")
async def vol(interaction: discord.Interaction, percent: int):
    await set_volume(interaction, percent)

@bot.tree.command(name="stop", description="Остановить стрим и выйти из голосового чата")
async def stop(interaction: discord.Interaction):
    if bot.voice_client:
        await bot.voice_client.disconnect()
        bot.is_streaming = False
        await interaction.response.send_message("🛑 Отключился от голосового канала.")
    else:
        await interaction.response.send_message("❌ Бот не был подключен к голосовому каналу.")

bot.run(TOKEN)


