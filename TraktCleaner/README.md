and instead provide plain text formatting. Here's the updated README content:

---

# TraktCleaner

TraktCleaner is a Python-based utility designed to streamline the management of your Trakt collection. It identifies and removes orphaned movies and TV shows from your Trakt library while synchronizing missing content from your local Radarr and Sonarr libraries.

---

## Features
- 🗑️ Remove Orphaned Content: Automatically detect and remove movies and shows in Trakt that are no longer present in your Radarr or Sonarr libraries.
- 🔄 Sync Missing Content: Add missing movies and episodes from Radarr and Sonarr to your Trakt collection.
- ⚙️ Graceful Handling: Handles missing IMDb/TVDB IDs without breaking the workflow.
- 🚀 Optimized Performance: Parallelized fetching for faster synchronization.
- 🧪 Dry-Run Mode: Preview changes without making any modifications to your Trakt collection.

---

## Requirements
- Python: Version 3.10 or higher.
- Dependencies: Listed in requirements.txt.
- Environment Variables: A .env file containing your API credentials (see Setup).

---

## Setup

1. Clone the Repository:
   git clone https://github.com/yourusername/traktcleaner.git
   cd traktcleaner

2. Install Dependencies:
   pip install -r requirements.txt

3. Configure Environment Variables:
   - Copy the example .env file:
     cp .env.example .env
   - Open the .env file and fill in the required credentials:
     - TRAKT_CLIENT_ID
     - TRAKT_ACCESS_TOKEN
     - TRAKT_USERNAME
     - RADARR_API_KEY
     - SONARR_API_KEY

4. Verify Connectivity:
   - Ensure your Radarr and Sonarr servers are accessible on your network.

---

## Usage

Dry-Run Mode (Default):
   python sync_trakt_library.py

Live Mode:
   python sync_trakt_library.py --live

---

## Notes
- API Rate Limits: The Trakt API enforces rate limits. This script uses batching and parallelism to minimize API calls.
- Network Accessibility: Ensure Radarr and Sonarr servers are reachable on your local network.
- Error Handling: The script gracefully handles missing or invalid IDs and provides detailed logs for debugging.

---

## License
This project is licensed under the MIT License. See the LICENSE file for more details.

---

## Contributing
Contributions are welcome! If you encounter issues or have feature requests, feel free to open an issue or submit a pull request.

## Verify Python Version
Ensure you are using Python 3.10 or higher by running:
python --version