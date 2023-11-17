import json
import os
import subprocess
import random, string, hashlib
import time
import urllib.request
import requests
import ffmpeg
from datetime import datetime, timedelta
from .helper_functions import delete_video, write_to_json, read_json_file
import logging

logger = logging.getLogger(__name__)

class BaseTiktokDownloader:
    SEARCH_URL = "https://tiktok-video-no-watermark2.p.rapidapi.com/feed/search"
    USERNAME_URL = "https://tiktok-video-no-watermark2.p.rapidapi.com/user/posts"
    API_KEYS = 'api_keys.json'
    SEARCH_BY_FILE = 'search.json'


    def __init__(self, channel, channel_path):
        self.channel = channel
        self.channel_path = channel_path
        self.api_key = ''
        self.search_by = ''
        self.search = ''
        self.api_keys = self.load_api_keys()

        self.load_search_file()

    def load_api_keys(self):
        '''Read the list of tiktok api keys to fetch'''
        file_path = os.path.join(os.getcwd(), self.API_KEYS)
        secrets = read_json_file(file_path)
        for secret in secrets:
            yield secret

    def load_search_file(self):
        try:
            file_path = os.path.join(self.channel_path, self.SEARCH_BY_FILE)
            data = read_json_file(file_path)
            search_by = data.get('search_by', False)
            self.search_by = 'keywords' if search_by == 'keywords' else 'username'

            if self.search_by == 'keywords':
                self.search = data.get('keywords', False)
            else:
                self.search = data.get('username', False)

        except json.JSONDecodeError as e:
            logger.error(f"Error {self.channel.upper()} : {e}")
            return False

        except Exception as e:
            logger.error(f"Error {self.channel.upper()} : {e}")
            return False

    def read_json_file(self, filename):
        with open(filename, "r") as file:
            return json.load(file)

    def generate_random_uuid(self):
        # Define characters to be used (digits and uppercase letters)
        chars = string.digits + string.ascii_uppercase
        # Generate random characters for each section of the UUID
        sections = [
            ''.join(random.choice(chars) for _ in range(length))
            for length in [8, 4, 4, 4, 12]
        ]
        # Join the sections with dashes to form the UUID
        random_uuid = '-'.join(sections)

        return random_uuid

class TikTokDownloader(BaseTiktokDownloader):
    VIDEO_DB = 'videos_db.json'

    def __init__(self, channel, channel_path):
        super().__init__(channel, channel_path)
        self.pre_fetched_videos = None

    def fetch_video(self):
        '''
            - Saves Video response in self.prefetched videos
            - Iterate videos and Yield downloaded Video
        '''
        self.pre_fetched_videos = self.check_prefetched_videos()
        if not self.pre_fetched_videos:
            self.pre_fetched_videos = self.request_videos()
            self.overwrite_db()

        for video_data in self.pre_fetched_videos:
                title = video_data.get("title", None)
                url = video_data.get("play", None)
                video_id = video_data.get("video_id", None)

                if title is None or url is None or video_id is None:
                    raise Exception(f'Title {title} or Video_id {video_id} or URL {url} is none, ')

                if self.is_video_in_db(video_id):
                    logger.info(f"Skipping {self.channel.upper()} : Video '{video_id}' already exists in TikTok")
                    continue
                try:
                    generated_filename = self.generate_random_uuid()
                    video_name = f"video_{random.randint(1, 10)}"
                    downloaded_video = os.path.join(self.channel_path, f"first_{video_name}.mp4")
                    if not self.download_video(url, downloaded_video):
                        continue

                    edited_video = os.path.join(self.channel_path, f"{generated_filename}.MOV")
                    if not self.convert_video(downloaded_video, edited_video):
                        continue
                    self.add_metadata(edited_video)
                    delete_video(downloaded_video)
                    #Add Edited Video Path to video metadata
                    video_data['video_path'] = edited_video
                    yield video_data

                except Exception as e:
                    logger.info(f"{self.channel.upper()} : {e}")
                    continue


    def request_videos(self, cursor="0"):
        '''
         :sort_type: { 0: Relevance, 1: Like Count, 2: Date Posted }
         :publish_time : { 0 - ALL, 1 - Past 24 hours, 7 - This week, 30 - This month, 90 - Last 3 months, 180 - Last 6 months }
         :region : 'string'
        :return: response['data']['videos']
        '''
        retry = 0
        api = next(self.api_keys)
        if self.search_by == 'keywords':
            querystring = {"keywords": self.search, "count": "20", "cursor": cursor, 'sort_type': 0}
            url = self.SEARCH_URL
        else:
            querystring = {"unique_id": self.search, "count": "20", "cursor": cursor}
            url = self.USERNAME_URL
        headers = {
            "X-RapidAPI-Key": api,
            "X-RapidAPI-Host": "tiktok-video-no-watermark2.p.rapidapi.com"
        }
        try:
            retry += 1
            response = requests.get(url, headers=headers, params=querystring)
            response.raise_for_status()
            if response.status_code != 200:
                raise requests.HTTPError(f'ERROR {response.status_code} : {response.content}')
            data = response.json().get('data', {})
            videos = data.get('videos', [])
            return videos

        except (requests.exceptions.HTTPError, requests.exceptions.RequestException) as e:
            logger.info(f'RETRY {retry} with another key .. : {e}')
            return self.request_videos()

        except (json.JSONDecodeError, requests.HTTPError) as e:
            logger.error(f"Error {self.channel.upper()} : {e}")
            return []

    def download_video(self, url, filename):
        try:
            # Download the video and save it to a file
            urllib.request.urlretrieve(url, filename)
            return True
            logger.info(f"{self.channel.upper()} Video {video_id} downloaded!")

        except Exception as e:
            logger.error(f"Error {self.channel.upper()} : {e}")
            return False

    def is_video_in_db(self, video_id):
        video_db_path = os.path.join(self.channel_path, self.VIDEO_DB)
        videos_db = read_json_file(video_db_path)
        if video_id in videos_db:
            return True
        return False



    def map_metadata(self):
        time = str((datetime.now() - timedelta(minutes=5)).strftime("%Y:%m:%d %H:%M:%S")) + '-6:00'
        add_keys = {
            # "File Name" : filename,
            # "Vendor ID": '',
            # "Color Primaries" : '',
            # "Transfer Characteristics": "",
            # "Matrix Coefficients": "",
            # "Pixel Aspect Ratio": "",
            # "Create Date": time,
            # "Modify Date": time,
            "TrackCreateDate": time,
             "TrackModifyDate": time,
            # "Clean Aperture Dimensions": "1080x1920", #checl
            # "Production Aperture Dimensions": "1080x1920", #checl
            # "Encoded Pixels Dimensions": "1080x1920", #checl
            # "HandlerVendorID": "Apple",
            "MediaCreateDate": time,
            "MediaModifyDate": time,
            # "Media Language Code": "und",
            # "Handler Type": "Metadata Tags",
            # "Handler Description": "Core Media Data Handler",
            "SoftwareVersion": "",
            "User Data des": "",
            "XMPToolkit" : "",
            "Comment": "",
            "AllDates" : time,
            # "Layout Flags": "",
            "Software": str({
                "publicMode": "1",
                "TEEditor": "2",
                "isFastImport": "0",
                "transType": "2",
                "te_is_reencode": "1",
                "source": ""
            }),
            "Artwork": str({
                "source_type": "vicut",
                "data": {
                    "ad_ai_avatar_params": {},
                    "adsTemplateId": "",
                    "appVersion": "9.4.0",
                    "businessComponentId": "",
                    "businessTemplateId": "",
                    "capabilityName": "",
                    "ccTtVid": "",
                    "commercial_params": {
                        "commercial_audio_music_cnt": 0,
                        "commercial_sticker_cnt": 0,
                        "commercial_text_font_cnt": 0,
                        "commercial_text_template_cnt": 0,
                        "commercial_tone_cnt": 0,
                        "tone_cnt": 0
                    },
                    "draftInfo": {
                        "adjust": 0,
                        "aiMatting": 0,
                        "audioToText": 0,
                        "chroma": 0,
                        "coverTemplateId": "",
                        "curveSpeed": random.choice([0, 1]),
                        "faceEffectId": "",
                        "filterId": "",
                        "gameplayAlgorithm": "",
                        "graphs": random.choice([0, 1]),
                        "keyframe": random.choice([0, 1]),
                        "mask": random.choice([0, 1]),
                        "mixMode": random.choice([0, 1]),
                        "motion_blur_cnt": random.choice([0, 1]),
                        "normalSpeed": random.choice([0, 1]),
                        "pip": 0,
                        "reverse": 0,
                        "slowMotion": 0,
                        "soundId": "",
                        "stickerId": "",
                        "textAnimationId": "",
                        "textEffectId": "",
                        "textShapeId": "",
                        "textTemplateId": "",
                        "textToAudio": random.choice([0, 1]),
                        "transitionId": "",
                        "videoAnimationId": "",
                        "videoEffectId": "",
                        "videoMaterialId": "",
                        "videoTracking": random.choice([0, 1])
                    },
                    "editSource": "multi_record",
                    "editType": "camera",
                    "enterFrom": "camera",
                    "exportType": "export",
                    "extendTemplateId": "",
                    "extendTemplateType": random.choice([0, 1]),
                    "filterId": "",
                    "greenscreenLayoutType": "",
                    "infoStickerId": "",
                    "is_keyframe": random.choice([0, 1]),
                    "is_use_smart_motion": "0",
                    "is_velocity_edited": 0,
                    "motion_blur_cnt": 0,
                    "movie3dTextTemplateId": "",
                    "musicId": "",
                    "os": "ios",
                    "product": "vicut",
                    "provider": "ad_site",
                    "region": "US",
                    "resourceTypeApplied": "",
                    "slowMotion": "none",
                    "stickerId": "",
                    "templateAddTextCnt": 0,
                    "templateId": "",
                    "textSpecialEffect": "",
                    "transferMethod": "",
                    "transitions": "",
                    "useSpecialEffectKeyFrame": 0,
                    "videoAnimation": "",
                    "videoEffectId": "",
                    "videoId": self.generate_random_uuid() + '.MOV',
                }
            }),
            "Copyright": str(self.hash_string()),
        }
        metadata = ''
        for key, value in add_keys.items():
        #     # metadata += f':{key}={value}'
            metadata += f' -{key}="{value}"'
            # metadata.append(f' {key}="{value}"')
        return metadata
    def hash_string(self):
        # Generate a random string
        random_string = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(4))

        # Convert the hashed bytes to a hexadecimal representation
        hash_hex = hashlib.sha256(random_string.encode()).hexdigest()
        return hash_hex
    def convert_video(self, input_file, output_file):
        # Use exiftool to clean metadata from the input file and save the result to the output file
        # subprocess.run(['exiftool', '-all=', '-o', output_file, input_file], check=True)
        # metadata_to_add = self.map_metadata()
        metadata = {
            'c:v': 'copy',  # Copy video stream
            'c:a': 'copy',  # Copy audio stream
            'f' : 'mov',
            # 'vcodec' : 'libx265',
            # 'metadata' : self.map_metadata()ffmpe
        }
        try:
            ffmpeg.input(input_file).output(output_file, **metadata).run(overwrite_output=True)
            return True
        except ffmpeg.Error as e:
            return False
            logger.error(e)

    def add_metadata(self, file_path):
        #Add a sleep until video i generated
        time.sleep(2)
        new_metadata = self.map_metadata()
        self.modify_metadata(file_path, new_metadata)

    def modify_metadata(self, file_path, metadata_changes):
            try:
                # Construct the ExifTool command to modify metadata
                command = "exiftool" + metadata_changes

                # Add metadata modifications to the command
                # for key, value in metadata_changes.items():
                #     command += f' -{key}="{value}"'

                # Add the file path to the command
                command += f' "{file_path}"'

                # Execute the command
                subprocess.run(command, shell=True)
                logger.info(f"{self.channel.upper} Metadata modified successfully.")
            except Exception as e:
                logger.error(f"Error {self.channel.upper()}:", str(e))


    def overwrite_db(self):
        '''
        Overwrite with newest VIDEO LIST
        {
        'search' : '___',
        'datetime': '',
        'items' : []
        }
        '''
        if self.pre_fetched_videos:
            file_path = os.path.join(self.channel_path, 'prefetched_videos.json')
            data = {
                "search": str(self.search),
                'datetime' : str(datetime.now()),
                'items' : self.pre_fetched_videos
            }
            if data:
                write_to_json(file_path, data)


    def check_prefetched_videos(self):
        file_path = os.path.join(self.channel_path, 'prefetched_videos.json')
        try:
            videos = read_json_file(file_path)
            old_datetime = datetime.strptime(videos.get('datetime', '2022-10-18 12:11:27.554310'),
                                             '%Y-%m-%d %H:%M:%S.%f')
            curr_time = datetime.now()
            if curr_time - old_datetime < timedelta(hours=12) and videos.get('items',
                                                                             False) and self.search == videos.get(
                    'search', False):
                return videos['items']
            return False

        except FileNotFoundError as e:
            return False




