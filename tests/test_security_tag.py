import unittest
import importlib

class SecurityTagTests(unittest.TestCase):
    def test_apply_security_tag_marks_core(self):
        sec = importlib.import_module('src.security')
        sec.apply_security_tag('src')
        yt_app = importlib.import_module('src.youtube_app')
        mp_mod = importlib.import_module('src.pages.main.main_page')
        self.assertTrue(sec.is_secure(yt_app))
        self.assertTrue(hasattr(yt_app.YouTubeApp, '__secure_tag__'))
        self.assertTrue(sec.is_secure(yt_app.YouTubeApp))
        self.assertTrue(sec.is_secure(mp_mod))

    def test_tag_functions_and_classes(self):
        sec = importlib.import_module('src.security')
        sec.apply_security_tag('src')
        pl_mod = importlib.import_module('src.playlist')
        self.assertTrue(sec.is_secure(pl_mod))
        self.assertTrue(sec.is_secure(pl_mod.Playlist))
        self.assertTrue(hasattr(pl_mod.Playlist.search_playlists, '__secure_tag__'))

if __name__ == '__main__':
    unittest.main()
