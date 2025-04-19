import argparse
import requests
import os
import time
import concurrent.futures
import json
from dotenv import load_dotenv
from tqdm import tqdm
from loguru import logger

# --- CLI Arguments ---
parser = argparse.ArgumentParser(description="Sync Radarr/Sonarr collections to Trakt.tv")
parser.add_argument('--live', action='store_true', help='Actually perform removals and syncs (default is dry-run)')
args = parser.parse_args()
dry_run = not args.live

# --- Load Environment Variables ---
load_dotenv()

client_id = os.getenv('TRAKT_CLIENT_ID')
access_token = os.getenv('TRAKT_ACCESS_TOKEN')
username = os.getenv('TRAKT_USERNAME')
radarr_api_key = os.getenv('RADARR_API_KEY')
sonarr_api_key = os.getenv('SONARR_API_KEY')

# --- Validate Environment ---
missing_vars = [var for var in ['TRAKT_CLIENT_ID', 'TRAKT_ACCESS_TOKEN', 'TRAKT_USERNAME', 'RADARR_API_KEY', 'SONARR_API_KEY'] if not os.getenv(var)]
if missing_vars:
    logger.error(f"❌ Missing environment variables: {', '.join(missing_vars)}. Please check your .env file.")
    exit(1)

# --- API Base URLs ---
trakt_base_url = "https://api.trakt.tv"
radarr_base_url = 'http://192.168.50.59:7878/api/v3'
sonarr_base_url = 'http://192.168.50.59:8989/api/v3'

# --- API Headers ---
trakt_headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {access_token}',
    'trakt-api-version': '2',
    'trakt-api-key': client_id
}
radarr_headers = {'X-Api-Key': radarr_api_key}
sonarr_headers = {'X-Api-Key': sonarr_api_key}

# --- Utility Functions ---
def fetch_with_retry(url, headers, retries=3, delay=2):
    """Fetch data from an API with retry logic."""
    for attempt in range(retries):
        response = requests.get(url, headers=headers)
        if response.ok:
            return response.json()
        logger.warning(f"Attempt {attempt + 1} failed for {url}. Retrying in {delay} seconds...")
        time.sleep(delay)
    response.raise_for_status()

# TODO: Consider adding exponential backoff to the retry logic for better handling of rate limits.

def chunk_payload(payload, chunk_size):
    """Split a payload into smaller chunks."""
    for i in range(0, len(payload), chunk_size):
        yield payload[i:i + chunk_size]

# TODO: Add logic to handle API rate limits when sending large payloads.

# --- Fetch Collections ---
def fetch_trakt_collection(content_type):
    url = f"{trakt_base_url}/users/{username}/collection/{content_type}"
    return fetch_with_retry(url, trakt_headers)

def fetch_radarr_movies():
    url = f"{radarr_base_url}/movie"
    return fetch_with_retry(url, radarr_headers)

def fetch_sonarr_shows():
    url = f"{sonarr_base_url}/series"
    response = requests.get(url, headers=sonarr_headers)
    if response.ok:
        shows = response.json()
        # TODO: Add optional debug logging for Sonarr shows data if needed for troubleshooting.
        return shows
    logger.error(f"❌ Failed to fetch Sonarr shows. Status code: {response.status_code}")
    return []

# --- Find Orphans ---
def find_orphaned_trakt_movies(trakt_movies, radarr_movies):
    radarr_tmdb_ids = {movie['tmdbId'] for movie in radarr_movies if movie.get('tmdbId')}
    return [movie['movie'] for movie in trakt_movies if movie['movie']['ids'].get('tmdb') not in radarr_tmdb_ids]

def find_orphaned_trakt_shows(trakt_shows, sonarr_shows):
    sonarr_tvdb_ids = {show['tvdbId'] for show in sonarr_shows if show.get('tvdbId')}
    return [show['show'] for show in trakt_shows if show['show']['ids'].get('tvdb') not in sonarr_tvdb_ids]

# TODO: Add unit tests for find_orphaned_trakt_movies and find_orphaned_trakt_shows.

# --- Remove from Trakt ---
def remove_from_trakt(orphaned_movies, orphaned_shows, dry_run=True):
    if not orphaned_movies and not orphaned_shows:
        logger.info("✅ No orphaned movies or shows to remove.")
        return

    if orphaned_movies:
        logger.info(f"\n🎬 Orphaned Movies ({len(orphaned_movies)}):")
        for movie in orphaned_movies:
            logger.info(f" - {movie['title']} ({movie.get('year')})")
    
    if orphaned_shows:
        logger.info(f"\n📺 Orphaned Shows ({len(orphaned_shows)}):")
        for show in orphaned_shows:
            logger.info(f" - {show['title']} ({show.get('year')})")

    if dry_run:
        logger.info("\n🧪 Dry-run mode: No removals performed.")
        return

    payload = {
        "movies": [{"ids": {"tmdb": movie['ids']['tmdb']}} for movie in orphaned_movies],
        "shows": [{"ids": {"tvdb": show['ids']['tvdb']}} for show in orphaned_shows]
    }

    url = f"{trakt_base_url}/sync/collection/remove"
    response = requests.post(url, headers=trakt_headers, json=payload)
    if response.ok:
        logger.info("✅ Successfully removed orphans from Trakt collection.")
    else:
        logger.error(f"❌ Failed to remove from Trakt. Status code: {response.status_code}")

# TODO: Add error handling for partial failures when removing items from Trakt.

# --- Find Missing Movies ---
def find_missing_trakt_movies(radarr_movies, trakt_movies):
    trakt_tmdb_ids = {movie['movie']['ids'].get('tmdb') for movie in trakt_movies}
    return [{"ids": {"tmdb": movie['tmdbId']}} for movie in radarr_movies if movie.get('tmdbId') not in trakt_tmdb_ids]

# TODO: Add logging to indicate how many missing movies were found.

# --- Find Missing Episodes (Parallelized) ---
def fetch_show_episodes(show):
    tvdb_id = show.get('tvdbId')
    imdb_id = show.get('imdbId')  # Use .get() to avoid KeyError
    title = show.get('title', 'Unknown Title')  # Default to 'Unknown Title' if title is missing

    if not tvdb_id:
        logger.warning(f"Skipping show '{title}' (missing TVDB ID).")
        return None

    url = f"{sonarr_base_url}/episode?seriesId={show['id']}"
    response = requests.get(url, headers=sonarr_headers)
    if not response.ok:
        logger.warning(f"❌ Failed to fetch episodes for {title}")
        return None

    episodes = response.json()
    return {
        "tvdb_id": tvdb_id,
        "imdb_id": imdb_id,  # May be None if not present
        "title": title,
        "episodes": episodes
    }

# TODO: Add error handling for cases where episodes are missing or malformed.

def find_missing_trakt_episodes_parallel(sonarr_shows, trakt_shows):
    trakt_episodes = {
        (show['show']['ids'].get('tvdb'), ep['season'], ep['number'])
        for show in trakt_shows
        for ep in show.get('episodes', [])
    }

    missing_episodes = []
    skipped_shows = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_show = {executor.submit(fetch_show_episodes, show): show for show in sonarr_shows}
        for future in tqdm(concurrent.futures.as_completed(future_to_show), total=len(sonarr_shows), desc="Fetching episodes"):
            show_data = future.result()
            if not show_data:
                continue

            if not show_data['imdb_id']:
                skipped_shows.append(show_data['title'])
                continue

            for ep in show_data['episodes']:
                if ep['hasFile']:
                    key = (show_data['tvdb_id'], ep['seasonNumber'], ep['episodeNumber'])
                    if key not in trakt_episodes:
                        missing_episodes.append({
                            "imdb_id": show_data['imdb_id'],
                            "season": ep['seasonNumber'],
                            "episode": ep['episodeNumber'],
                            "title": show_data['title']
                        })

    if skipped_shows:
        logger.warning("\n⚠️ Skipped shows (missing IMDb ID):")
        for title in skipped_shows:
            logger.warning(f" - {title}")

    return missing_episodes

# TODO: Add a summary log of how many episodes were skipped and how many were found missing.

# --- Sync to Trakt ---
def sync_to_trakt(missing_movies, missing_episodes, dry_run=True):
    url = f"{trakt_base_url}/sync/collection"
    payload = {
        "movies": missing_movies,
        "episodes": [
            {"ids": {"imdb": ep['imdb_id']}, "season": ep['season'], "number": ep['episode']}
            for ep in missing_episodes
        ]
    }

    logger.info(f"\n📦 Payload prepared ({len(missing_movies)} movies, {len(missing_episodes)} episodes).")

    if dry_run:
        logger.info("🛠 Dry-run mode: Would sync to Trakt (not actually sending).")
        return

    response = requests.post(url, headers=trakt_headers, json=payload)
    if response.status_code == 201:
        logger.info("✅ Successfully synced missing movies and episodes to Trakt.")
    else:
        logger.error(f"❌ Failed to sync. Status code: {response.status_code} Response: {response.text}")

# TODO: Add retry logic for failed sync attempts.

# --- Main Execution ---
if __name__ == "__main__":
    logger.info("\n🔄 Starting Trakt collection sync...")
    with concurrent.futures.ThreadPoolExecutor() as executor:
        trakt_movies_future = executor.submit(fetch_trakt_collection, 'movies')
        trakt_shows_future = executor.submit(fetch_trakt_collection, 'shows')
        radarr_movies_future = executor.submit(fetch_radarr_movies)
        sonarr_shows_future = executor.submit(fetch_sonarr_shows)

        trakt_movies = trakt_movies_future.result()
        trakt_shows = trakt_shows_future.result()
        radarr_movies = radarr_movies_future.result()
        sonarr_shows = sonarr_shows_future.result()

    orphaned_movies = find_orphaned_trakt_movies(trakt_movies, radarr_movies)
    orphaned_shows = find_orphaned_trakt_shows(trakt_shows, sonarr_shows)
    remove_from_trakt(orphaned_movies, orphaned_shows, dry_run=dry_run)

    missing_movies = find_missing_trakt_movies(radarr_movies, trakt_movies)
    missing_episodes = find_missing_trakt_episodes_parallel(sonarr_shows, trakt_shows)
    sync_to_trakt(missing_movies, missing_episodes, dry_run=dry_run)

    logger.info("\n🏁 Done!")
