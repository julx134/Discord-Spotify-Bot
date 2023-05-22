import discord
import json
import random
import spotipy
import time
import youtube_dl
import ffmpeg
import asyncio
from discord.ext import commands
from spotipy.oauth2 import SpotifyClientCredentials
from requests_html import AsyncHTMLSession
from bs4 import BeautifulSoup as bs


youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)




spotify = spotipy.Spotify(auth_manager = SpotifyClientCredentials('${api_key}','${public_key}'))
client = commands.Bot(command_prefix = '!')
session = AsyncHTMLSession()
songs = []
playThread = asyncio.Event()
nextSong = None
player = None


async def populate_queue(songName):	
	query_songName = songName.replace("&","%26").replace(" ", "+")
	url = 'https://www.youtube.com/results?search_query='+query_songName
	response = await session.get(url)
	await response.html.arender(sleep = 10)
	soup = bs(response.html.html, 'html.parser')

	video_data = soup.find('a', id = 'thumbnail')
	#vid_duration = str(soup.find('span', class_ = 'style-scope ytd-thumbnail-overlay-time-status-renderer').text).strip().split(':')
	#vid_inSeconds = int(vid_duration[0])*60 + int(vid_duration[1])
	link = video_data.get('href')
	video_link = 'https://www.youtube.com' + link

	#data = [video_link, vid_inSeconds]
	return video_link

@client.event
async def on_ready():
	print('Bot is ready')

@client.command(aliases=['spotify'])
async def spotify_(ctx, *, user_input):
	if not ctx.message.author.voice:
		await ctx.send('You must be connected to a voice channel')
		return
	else:
		bot_channel = ctx.message.author.voice.channel
	
	try:
		await bot_channel.connect()
	except:
		pass

	await ctx.send("Working....")

	if ':' not in user_input:
		query = user_input.replace(" ", "%20")
		search_results = spotify.search(q = f'\"{query}\"', type = 'playlist')

		if search_results['playlists']['items']:
			playlist_id = search_results['playlist']['items'][0]['id']
			playlistObject = spotify.playlist_tracks(f'{playlist_id}')
			
			for items in playlistObject['items']:
				songs.append( items['track']['artists'][0]['name'] + '-' + items['track']['name'])	
	else:
		playlist_id = user_input.split(':')[2]

		playlistObject = spotify.playlist_tracks(f'{playlist_id}')
		
		for items in playlistObject['items']:
			songs.append( items['track']['artists'][0]['name'] + ' - ' + items['track']['name'])
		
	await play_backend(ctx)

def done_Playing():
	global playThread
	playThread.set()
	print('ping')

async def clear_PlayThread():
	global playThread
	playThread.clear()
	print('pong')

async def play_backend(ctx):
	try:
		voice_client = ctx.message.guild.voice_client
	except:
		pass
	
	global nextSong
	global player
	random.shuffle(songs)
	print(songs)

	for index, song in enumerate(songs):
		print(f"begin: {playThread.is_set()}")
		if not playThread.is_set() and nextSong is None:
			nextSong = song
			url = await populate_queue(song)
			player = await YTDLSource.from_url(url, loop = client.loop)
		if not voice_client.is_playing():
			async with ctx.typing():
				voice_client.play(player, after=lambda e: done_Playing())
				songs.remove(song)
			await ctx.send(f'Now playing: {url}')
		if index+1 < len(songs):
			if song is nextSong:
				nextSong = songs[index+1]
			else:
				nextSong = song
			url = await populate_queue(nextSong)
			player = await YTDLSource.from_url(url, loop = client.loop)
		else:
			nextSong = None
			player = None
			songs.clear()
			await clear_PlayThread()
			print(f"done: {playThread.is_set()}")
			await ctx.send("Playlist done playing!")
		try:
			print("waiting")
			await playThread.wait()
			await clear_PlayThread()
			print("song finished")
		except:
			pass
		
@client.command(aliases=['play'])
async def play_(ctx, *,user_url):
	if not ctx.message.author.voice:
		await ctx.send('You must be connected to a voice channel')
		return
	else:
		bot_channel = ctx.message.author.voice.channel
	
	try:
		await bot_channel.connect()
	except:
		pass

	songs.append(user_url)
	voice_client = ctx.message.guild.voice_client

	if voice_client.is_playing():
		await ctx.send(f'Added {user_url} to queue!')
	else:
		await play_backend(ctx)

@client.command()
async def clear(ctx):
	nextSong = None
	player = None
	songs.clear()
	await clear_PlayThread()
	voice_client = ctx.message.guild.voice_client
	voice_client.stop()

	await ctx.send('Cleared song queue!')

@client.command()
async def skip(ctx):
	if len(songs) > 0:
		voice_client = ctx.message.guild.voice_client
		voice_client.stop()
		await ctx.send("Working...")

		play_backend(ctx)
	else:
		await ctx.send("No more songs in queue")
		return

@client.command()
async def stop(ctx):
	await clear_PlayThread()
	voice_client = ctx.message.guild.voice_client
	voice_client.stop()

@client.command()
async def pause(ctx):
	await clear_PlayThread()
	voice_client = ctx.message.guild.voice_client
	voice_client.pause()

@client.command()
async def resume(ctx):
	clear_PlayThread()
	voice_client = ctx.message.guild.voice_client
	voice_client.resume()

@client.command()
async def ian(ctx):
	await ctx.send("Ready??")
	await asyncio.sleep(1)
	
	for i in reversed(range(6)):
		if i != 0:
			await ctx.send(f"{i}!")
			await asyncio.sleep(1)

	await ctx.send("**Ian's gay**")
	#https://media1.giphy.com/media/gtakVlnStZUbe/giphy.gif
	embed = discord.Embed()
	embed.set_image(url = 'https://media1.giphy.com/media/gtakVlnStZUbe/giphy.gif')
	await ctx.send(embed = embed)


@client.command(aliases=['this'])
async def this_shit_bussin(ctx):
	await asyncio.sleep(1)

	if not ctx.message.author.voice:
		await ctx.send('You must be connected to a voice channel')
		return
	else:
		bot_channel = ctx.message.author.voice.channel
	
	try:
		await bot_channel.connect()
	except:
		pass

	embed = discord.Embed()
	embed.set_image(url = 'https://emoji.gg/assets/emoji/9695-lip-bitting.png')
	await ctx.send(embed = embed)
	vc = ctx.message.guild.voice_client
	vc.play(discord.FFmpegPCMAudio(executable="C:/ffmpeg/bin/ffmpeg.exe", source="F:/DiscordBot/sheesh_choral.webm"), after=lambda e: print('done'))

	while vc.is_playing():
		await asyncio.sleep(1)

	await vc.disconnect()

client.run('NzkyNDg2NzEyOTgyMjQxMzEx.X-eaxA.qyyrRZTNa-80RnO2rfc8zy5sSKM')



