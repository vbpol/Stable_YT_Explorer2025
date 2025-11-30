# Testing Model Classes in YouTube Downloader

This document outlines the steps and methods used to test the model classes (`Playlist` and `Video`) in the YouTube downloader application. The tests are implemented using the `unittest` framework and are designed to verify the functionality of the models.

---

## Overview of Tests

### 1. Test Setup
- **In-Memory Database**: The tests use an in-memory SQLite database to ensure that each test runs in isolation without affecting the actual database.
- **Session Management**: A new session is created for each test, and it is closed after the test completes.

### 2. Test Cases

#### a. Playlist Model Tests
- **`test_create_playlist`**: Tests the creation of a new playlist and verifies its attributes.
- **`test_get_number_of_videos`**: Tests the method to get the number of videos in a playlist.
- **`test_get_videos`**: Tests the method to retrieve videos from a playlist.

#### b. Video Model Tests
- **`test_create_video`**: Tests the creation of a new video and verifies its attributes.
- **`test_video_download_status`**: Tests the method to check if a video is downloaded.
- **`test_to_dataframe`**: Tests the conversion of video information to a Pandas DataFrame.

---

## Test Implementation

### Test Class Structure
The tests are organized within a class called `TestModelClasses`, which inherits from `unittest.TestCase`. The class includes the following methods:

```python
class TestModelClasses(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up the test database and create tables."""
        cls.engine = create_engine('sqlite:///:memory:')  # Use in-memory database for testing
        Base.metadata.create_all(cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)

    def setUp(self):
        """Create a new session for each test."""
        self.session = self.Session()

    def tearDown(self):
        """Close the session after each test."""
        self.session.close()
```

### Example Test Method
Here's an example of a test method for creating a playlist:

```python
def test_create_playlist(self):
    """Test creating a new playlist."""
    playlist = Playlist(title='Test Playlist', description='A playlist for testing.')
    self.session.add(playlist)
    self.session.commit()

    # Verify that the playlist was created
    retrieved_playlist = self.session.query(Playlist).filter_by(title='Test Playlist').one()
    self.assertEqual(retrieved_playlist.title, 'Test Playlist')
    self.assertEqual(retrieved_playlist.description, 'A playlist for testing.')
```

---

## Running the Tests
To run the tests, execute the following command in the terminal:

```bash
python -m unittest discover -s Test
```

This command will discover and run all test cases defined in the `Test` directory.

---

## Conclusion
By following this document, you can understand how to test the model classes in the YouTube downloader application effectively. The tests ensure that the models function as expected and help maintain the integrity of the application as it evolves.

For further details, refer to the individual test methods and the model class implementations. 