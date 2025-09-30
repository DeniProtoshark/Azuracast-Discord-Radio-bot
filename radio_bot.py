import discord
from discord import app_commands

TOKEN = "Bla Bla Bla Token Bla Bla Bla" # Bot token
GUILD_ID = bla bal bal  # Server ID
STREAM_URL_FLAC = "Bla Bla Bla" # Any audio streams

# Stream Settings [beta]
FFMPEG_SAMPLE_RATE = 48000  # Sample rate
FFMPEG_CHANNELS = 2         # Channels (1=mono, 2=stereo)
FFMPEG_SAMPLE_FMT = 's16le' # format PCM (s16le=16 bit[stable}, s32le= 32 bit[unstable]) 


intents = discord.Intents.default()
intents.voice_states = True
intents.messages = True

class RadioBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.current_volume = 1.0 # Def volume 0.0 - 1.0
        self.voice_client = None
        self.is_streaming = False

    async def on_ready(self):
        print(f"✅ Logged in as {self.user}")
        try:
            guild = discord.Object(id=GUILD_ID)
            await self.tree.sync(guild=guild)
            print("✅ Команды синхронизированы для тестового сервера")
        except Exception as e:
            print(f"⚠️ Ошибка синхронизации команд: {e}")

bot = RadioBot()

@bot.tree.command(name="radio", description="Стримить радио в голосовой или Stage канал")
@app_commands.describe(channel="Имя канала (необязательно)")
async def radio(interaction: discord.Interaction, channel: str = None):
    ch = None

    if channel:
        for c in interaction.guild.channels:
            if isinstance(c, (discord.VoiceChannel, discord.StageChannel)) and c.name.lower() == channel.lower():
                ch = c
                break
    else:
        if interaction.user.voice and interaction.user.voice.channel:
            ch = interaction.user.voice.channel

    if not ch:
        await interaction.response.send_message(
            "❌ Нужно быть в голосовом или Stage канале, или указать его имя.", ephemeral=True
        )
        return

    if bot.voice_client and bot.voice_client.is_connected():
        await bot.voice_client.disconnect()

    try:
        bot.voice_client = await ch.connect()

        if isinstance(ch, discord.StageChannel):
            try:
                me = await ch.guild.fetch_member(bot.user.id)
                await me.edit(suppress=False)
            except Exception as e:
                await interaction.response.send_message(f"⚠️ Не удалось стать спикером: {e}", ephemeral=True)

        await interaction.response.send_message(f"🎶 Подключился к {ch.name}. Начинаю стрим!")
        await start_stream(interaction, STREAM_URL_FLAC)
    except Exception as e:
        await interaction.response.send_message(f"❌ Ошибка подключения: {e}", ephemeral=True)

async def start_stream(interaction, stream_url):
    if not bot.voice_client:
        await interaction.followup.send("❌ Бот не в голосовом канале.", ephemeral=True)
        return

    ffmpeg_options = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': f'-vn -ar {FFMPEG_SAMPLE_RATE} -ac {FFMPEG_CHANNELS} -f {FFMPEG_SAMPLE_FMT} -filter:a "volume={bot.current_volume}"'
    }
    audio_source = discord.FFmpegPCMAudio(stream_url, **ffmpeg_options)
    bot.voice_client.play(audio_source)
    bot.is_streaming = True

@bot.tree.command(name="stop", description="Остановить стрим и выйти из голосового канала")
async def stop(interaction: discord.Interaction):
    if bot.voice_client:
        await bot.voice_client.disconnect()
        bot.is_streaming = False
        await interaction.response.send_message("🛑 Отключился от голосового канала.")
    else:
        await interaction.response.send_message("❌ Бот не был подключен к голосовому каналу.")

bot.run(TOKEN)
