import discord
import yt_dlp
from discord.ext import commands
import asyncio

intents = discord.Intents.default() # Configura as intenções (Intents) necessárias para o bot funcionar
intents.message_content = True  # Permite ler o conteúdo das mensagens (se necessário)

bot = commands.Bot(command_prefix='.', intents=intents) # Inicializa o bot

@bot.event
async def on_ready():
    print(f"Bot {bot.user} está online e pronto!")

ytdl_format_options = { #Opções de formatação do ytdl
    'format': 'bestaudio/best',
    'noplaylist': True,
    'default_search': 'ytsearch1',
    'ignoreerrors': True,
    'cookiefile': 'cookies.txt',
    'js_runtimes': {
          'node': {}
    },
     'extractor_args': {
         'youtube': {
             'player_client': ['android', 'web']
        }
    },
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn', # -vn significa "video no" (ignorar vídeo, apenas áudio)
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

Fila = []

@bot.event
async def on_ready():
    print(f"Bot {bot.user} está online e pronto!")

# Função auxiliar para tocar a próxima música da fila de forma segura
def play_next(ctx):
    if len(Fila) > 0:
        next_data = Fila.pop(0)
        coro = play_song_from_queue(ctx, next_data)
        asyncio.run_coroutine_threadsafe(coro, bot.loop)

async def play_song_from_queue(ctx, data):
    if not ctx.voice_client:
        return
    
    stream_url = data['url']
    title = data.get('title', 'Música sem título')
    
    source = discord.FFmpegPCMAudio(stream_url, **ffmpeg_options)
    
    def after_play(error):
        if error:
            print(f"Erro no player: {error}")
        play_next(ctx)

    ctx.voice_client.play(source, after=after_play)
    await ctx.send(f'▶ Tocando agora: **{title}**')

@bot.command()
async def play(ctx, *, search: str):
    if not ctx.author.voice:
        return await ctx.send("❌ Você precisa entrar em um canal de voz primeiro!")

    channel = ctx.author.voice.channel

    if ctx.voice_client is None:
        await channel.connect()
        await ctx.send("Conectado com sucesso!")
    elif ctx.voice_client.channel != channel:
        await ctx.voice_client.move_to(channel)

    async with ctx.typing():
        loop = ctx.bot.loop
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(search, download=False))
        
        if data is None:
            return await ctx.send("❌ Não foi possível encontrar ou extrair esta música.")
            
        if 'entries' in data:
            data = data['entries'][0]

    # Se já houver uma música tocando, adiciona à fila e encerra aqui
    if ctx.voice_client.is_playing():
        Fila.append(data)
        return await ctx.send(f"🎵 Música adicionada à fila: **{data.get('title')}**")

    # Se não estiver tocando nada, toca imediatamente
    stream_url = data['url']
    title = data.get('title', 'Música sem título')
    
    source = discord.FFmpegPCMAudio(stream_url, **ffmpeg_options)
    
    def after_play(error):
        if error:
            print(f"Erro no player: {error}")
        play_next(ctx)

    ctx.voice_client.play(source, after=after_play)
    await ctx.send(f'▶ Tocando agora: **{title}**')

@bot.command()
async def stop(ctx):
    global Fila
    if ctx.voice_client:
        Fila.clear()
        ctx.voice_client.stop()
        await ctx.voice_client.disconnect()
        await ctx.send("⏹️ Bot desconectado e fila limpa.")
    else:
        await ctx.send("❌ Eu não estou conectado a nenhum canal de voz.")

@bot.command()
async def skip(ctx):
    global Fila
    if ctx.voice_client and ctx.voice_client.is_playing():
        # Parar a música atual dispara automaticamente o 'after_play', que chama a próxima da fila
        ctx.voice_client.stop()
        await ctx.send("⏭️ Música pulada com sucesso!")
    else:
        await ctx.send("❌ Não há nenhuma música tocando para pular.")

@bot.command()
async def disconnect(ctx):
    global Fila
    if ctx.voice_client:
        Fila.clear()
        await ctx.voice_client.disconnect()
        await ctx.send("Desconectado com sucesso!")
    else:
        await ctx.send("Eu não estou conectado a nenhum canal de voz neste servidor.")
   

TOKEN = "YOUR TOKEN HERE"
bot.run(TOKEN)
                   