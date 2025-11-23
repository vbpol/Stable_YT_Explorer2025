import os
from pytube import YouTube, Playlist

class YouTubeDownloader:
    def __init__(self, download_dir='downloads'):
        self.download_dir = download_dir
        os.makedirs(self.download_dir, exist_ok=True)

    def download_video(self, video_url):
        """Download a single video."""
        try:
            yt = YouTube(video_url)
            video_stream = yt.streams.filter(progressive=True, file_extension='mp4').get_highest_resolution()
            if video_stream:
                print(f"Downloading: {yt.title}")
                video_stream.download(output_path=self.download_dir)
                print(f"Downloaded successfully to {self.download_dir}")
                return True
            else:
                print("No HD stream available for this video.")
                return False
        except Exception as e:
            print(f"An error occurred: {e}")
            return False

    def download_playlist(self, playlist_url):
        """Download all videos from a playlist."""
        try:
            playlist = Playlist(playlist_url)
            print(f"Downloading playlist: {playlist.title}")
            for video_url in playlist.video_urls:
                self.download_video(video_url)
            print(f"All videos from playlist '{playlist.title}' have been processed.")
        except Exception as e:
            print(f"An error occurred while processing the playlist: {e}")
