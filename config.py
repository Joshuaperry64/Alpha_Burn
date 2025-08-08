import configparser
import os

CONFIG_FILE = 'config.ini'

def create_default_config():
    """Creates a default config.ini file if one doesn't exist."""
    if not os.path.exists(CONFIG_FILE):
        config = configparser.ConfigParser()
        config['PATHS'] = {
            'DownloadFolder': 'AlphaBurn_Downloads',
            'ArtworkCache': 'artwork_cache'
        }
        config['API_KEYS'] = {
            'Gemini_API_Key': '',
            'Spotify_Client_ID': '',
            'Spotify_Client_Secret': '',
            'gemini_model': 'gemini-1.5-pro',
            'system_instructions': 'You are the AI assistant inside this CD burner application. You can search for music, download playlists, and assist with burning discs. Respond as a helpful in-app assistant.'
        }
        with open(CONFIG_FILE, 'w') as configfile:
            config.write(configfile)
    else:
        # Ensure system_instructions is present for existing users
        config = configparser.ConfigParser()
        config.read(CONFIG_FILE)
        if not config.has_option('API_KEYS', 'system_instructions'):
            config.set('API_KEYS', 'system_instructions', 'You are the AI assistant inside this CD burner application. You can search for music, download playlists, and assist with burning discs. Respond as a helpful in-app assistant.')
            with open(CONFIG_FILE, 'w') as configfile:
                config.write(configfile)

def get_config():
    """Reads and returns the configuration object."""
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    return config

def get_setting(section, key, default_value=None):
    """Gets a specific setting from the config file."""
    config = get_config()
    return config.get(section, key, fallback=default_value)

def update_setting(section, key, value):
    """Updates a specific setting in the config file."""
    config = get_config()
    if not config.has_section(section):
        config.add_section(section)
    config.set(section, key, value)
    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)

# Create the default config on import
create_default_config()
