# Discord-Spotify-Bot
This is a simple Discord bot written in Python that can play music from YouTube using the Discord voice chat feature. The bot uses the discord, spotipy, youtube_dl, and ffmpeg libraries for interacting with Discord, Spotify, YouTube, and audio processing.

## Features
- Plays music from Spotify playlists or individual tracks.
- Searches YouTube for the requested song and plays the first result.
- Supports basic playback controls such as play, pause, resume, skip, and stop.
- Allows users to add songs to a queue and plays them in the desired order.
- Clears the song queue and stops the playback.
- Displays a countdown message and plays a GIF when triggered.
- Can play a pre-defined audio file when a specific command is invoked.

## Supported Commands
- **!spotify <query>** or **!spotify <playlist_id>**: Searches for a Spotify playlist or track based on the provided query or playlist ID and adds the songs to the queue.
- **!play <youtube_url>**: Adds a YouTube video to the queue using the provided video URL.
- **!clear**: Clears the song queue and stops the playback.
- **!skip**: Skips the current song and plays the next song in the queue.
- **!stop**: Stops the playback and disconnects the bot from the voice channel.
- **!pause**: Pauses the current playback.
- **!resume**: Resumes the paused playback.
Note: Make sure you have a valid Spotify API key and a valid Discord bot token for the bot to function properly.

Feel free to customize and modify the code to suit your specific needs and preferences.
