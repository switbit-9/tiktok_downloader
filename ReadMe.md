# TikTok Downloader Python Package

A Python package for downloading TikTok videos without watermarks.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
  - [Basic Usage](#basic-usage)
  - [Advanced Configuration](#advanced-configuration)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)
- [Support](#support)

## Installation



## Usage

### Configuration 

You can configure the TikTokDownloader by providing a configuration file in the specified channel folder. The configuration file (search.json) should contain the following fields:

```
{
  "keywords": "your_search_keywords",
  "username": "tiktok_username",
  "location": "tiktok_location"
}
```


```
from tiktok_downloader import TikTokDownloader

# Create an instance of TikTokDownloader
downloader = TikTokDownloader(channel="your_channel_name")

# Fetch and download TikTok videos
for video_data in downloader.fetch_video(fetch_type="search"):
    # Process downloaded video data
    print(video_data)
```

Costumize the folders where you put Configurations

```
downloader.SEARCH_URL = "https://tiktok-video-no-watermark2.p.rapidapi.com/feed/search"
downloader.USERNAME_URL = "https://tiktok-video-no-watermark2.p.rapidapi.com/user/posts"
downloader.CHANNELS_FOLDER = 'channels'
downloader.API_KEYS = 'api_keys.json'
downloader.SEARCH_BY_FILE = 'search.json'
```


