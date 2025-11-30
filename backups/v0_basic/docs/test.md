# Testing Documentation

## Step 3: Video Player and File Operations Implementation

### Prerequisites
```bash
# 1. Install dependencies
pip install python-vlc isodate yt-dlp google-api-python-client

# 2. Verify VLC installation
vlc --version

# 3. Check configuration
cat config.json  # Verify API key and download folder
```

### Test Cases

#### 1. Video Player Core Features
| Test Case | Steps | Expected Result |
|-----------|-------|----------------|
| Basic Playback | 1. Open downloaded video<br>2. Click play button | Video starts playing |
| Pause/Resume | 1. Click pause during playback<br>2. Click play again | Video pauses and resumes |
| Time Seeking | 1. Drag time slider<br>2. Click different positions | Video jumps to selected position |
| Speed Control | Test each speed button:<br>- 0.5x<br>- 1.0x<br>- 1.5x<br>- 2.0x | Playback speed changes accordingly |
| Volume Control | 1. Adjust volume slider<br>2. Test mute | Volume changes properly |
| Fullscreen | 1. Click fullscreen button<br>2. Press Esc | Toggles fullscreen mode |

#### 2. File Operations
| Test Case | Steps | Expected Result |
|-----------|-------|----------------|
| CSV Export | 1. Select playlist<br>2. File > Export Playlist (CSV) | Creates valid CSV with all videos |
| TXT Export | 1. Select playlist<br>2. File > Export Playlist (TXT) | Creates formatted text file |
| Quick Save | Click "Save Playlist" button | Creates basic playlist file |
| UTF-8 Support | Export playlist with non-ASCII titles | Correct character encoding |

#### 3. Pagination System
| Test Case | Steps | Expected Result |
|-----------|-------|----------------|
| Page Size | Test each size option:<br>- 5<br>- 10<br>- 20<br>- 50 | Correct number of videos shown |
| Navigation | 1. Click Next/Previous<br>2. Check page indicator | Proper page navigation |
| Count Accuracy | Compare total videos with pages | Correct page calculation |

### Regression Testing
1. Verify previous features still work:
   - Playlist search
   - Video listing
   - Basic navigation

### Performance Testing
1. Video Player:
   - Load time < 2 seconds
   - Smooth playback
   - Memory usage < 200MB

2. File Operations:
   - Export large playlists (>100 videos)
   - Multiple format exports

### Known Issues
1. Video Player:
   ```
   - Fullscreen mode occasionally glitches
   - Time slider jumps during updates
   - No keyboard shortcuts implemented
   ```

2. Pagination:
   ```
   - Page reset on size change
   - No direct page jump option
   ```

### Next Steps
1. Download Features:
   - Progress tracking
   - Cancel functionality
   - Quality selection
   - Batch operations

2. UI Improvements:
   - Keyboard shortcuts
   - Search within playlist
   - Sorting options
   - Download queue

### Test Environment
- OS: Windows 10/11, Ubuntu 20.04+, macOS 12+
- Python: 3.8+
- VLC: 3.0+
- Screen Resolution: 1920x1080 minimum 