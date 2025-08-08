import sqlite3
import os

DB_FILE = "alphaburn_library.db"

def init_db():
    """Initializes the database and creates/updates the music table."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS music (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filepath TEXT NOT NULL UNIQUE,
            title TEXT,
            artist TEXT,
            album TEXT,
            year TEXT,
            genre TEXT,
            rating INTEGER DEFAULT 0
        )
    """)
    
    # Add rating column if it doesn't exist (for backward compatibility)
    try:
        cursor.execute("SELECT rating FROM music LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE music ADD COLUMN rating INTEGER DEFAULT 0")

    conn.commit()
    conn.close()

def add_song(filepath, metadata):
    """Adds a new song to the database. Ignores duplicates based on filepath."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO music (filepath, title, artist, album, year, genre, rating)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            filepath,
            metadata.get('title', 'Unknown Title'),
            metadata.get('artist', 'Unknown Artist'),
            metadata.get('album', 'Unknown Album'),
            metadata.get('year', '0000'),
            metadata.get('genre', 'Unknown'),
            0 # Default rating
        ))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    finally:
        conn.close()

def update_song_metadata(filepath, new_metadata):
    """Updates the metadata for a specific song."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE music
        SET title = ?, artist = ?, album = ?, year = ?, genre = ?
        WHERE filepath = ?
    """, (
        new_metadata['title'],
        new_metadata['artist'],
        new_metadata['album'],
        new_metadata['year'],
        new_metadata['genre'],
        filepath
    ))
    conn.commit()
    conn.close()

def update_song_rating(filepath, rating):
    """Updates the rating for a specific song."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE music SET rating = ? WHERE filepath = ?", (rating, filepath))
    conn.commit()
    conn.close()

def get_all_songs():
    """Retrieves all songs from the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT title, artist, album, year, genre, rating, filepath FROM music ORDER BY artist, album, title")
    songs = cursor.fetchall()
    conn.close()
    return songs

def get_song_by_filepath(filepath):
    """Retrieves a single song's data by its filepath."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT title, artist, album, year, genre, rating FROM music WHERE filepath = ?", (filepath,))
    song = cursor.fetchone()
    conn.close()
    return song

