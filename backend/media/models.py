from django.db import models

class Playlist(models.Model):
    playlist_id = models.CharField(primary_key=True, max_length=128)
    title = models.TextField()
    channel_title = models.TextField()
    video_count = models.IntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'playlists'

class Video(models.Model):
    video_id = models.CharField(primary_key=True, max_length=128)
    title = models.TextField()
    channel_title = models.TextField()
    duration = models.TextField(null=True)
    published = models.TextField(null=True)
    views = models.IntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'videos'

class PlaylistVideo(models.Model):
    playlist = models.ForeignKey(Playlist, on_delete=models.DO_NOTHING, db_constraint=False)
    video = models.ForeignKey(Video, on_delete=models.DO_NOTHING, db_constraint=False)
    position = models.IntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'playlist_videos'
        unique_together = (('playlist', 'video'),)

class LastResult(models.Model):
    id = models.AutoField(primary_key=True)
    mode = models.CharField(max_length=32)
    query = models.TextField()
    saved_at = models.DateTimeField(auto_now_add=True)
    next_page_token = models.TextField(null=True)
    prev_page_token = models.TextField(null=True)

    class Meta:
        managed = False
        db_table = 'last_results'

class LastResultVideo(models.Model):
    last = models.ForeignKey(LastResult, on_delete=models.DO_NOTHING, db_constraint=False)
    video = models.ForeignKey(Video, on_delete=models.DO_NOTHING, db_constraint=False)

    class Meta:
        managed = False
        db_table = 'last_result_videos'

class LastResultPlaylist(models.Model):
    last = models.ForeignKey(LastResult, on_delete=models.DO_NOTHING, db_constraint=False)
    playlist = models.ForeignKey(Playlist, on_delete=models.DO_NOTHING, db_constraint=False)

    class Meta:
        managed = False
        db_table = 'last_result_playlists'