import tkinter as tk
from src.youtube_app import YouTubeApp


def main():
    root = tk.Tk()
    app = YouTubeApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
