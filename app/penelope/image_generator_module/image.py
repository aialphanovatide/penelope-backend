# # Image Generator Module using D-ALLE 3, OpenAI API

# import os
# import time
# import logging
# from openai import OpenAI
# from typing import List, Dict, Literal, Optional

# class ImageGeneratorAssistant:
#     def __init__(self, api_key: Optional[str] = None, verbose: bool = False):
#         self.api_key = api_key or os.getenv("OPENAI_API_KEY")

#         if not self.api_key:
#             raise ValueError("OpenAI API key not provided and OPENAI_API_KEY environment variable not set")

#         self.client = OpenAI(api_key=self.api_key)
#         self.logger = logging.getLogger(__name__)
#         self.verbose = verbose

#         if self.verbose:
#             logging.basicConfig(level=logging.DEBUG)

#     def log_debug(self, message: str, *args, **kwargs):
#         if self.verbose:
#             self.logger.debug(message, *args, **kwargs)

#     def generate_image(self, prompt: str, size: str = "1024x1024", n: int = 1, style: Literal['vivid', 'natural'] = 'vivid') -> List[str]:
#         """
#         Generate images based on the given prompt.

#         Args:
#             prompt (str): The text prompt for image generation.
#             size (str): The size of the generated image. Defaults to "1024x1024".
#             n (int): The number of images to generate. Defaults to 1.

#         Returns:
#             List[str]: A list of URLs for the generated images.
#         """
#         # Generate the image using DALL-E
#         response = self.client.images.generate(
#             model="dall-e-3",
#             prompt=prompt,
#             size=size,
#             n=n,
#             style=style
#         )

#         return [image.url for image in response.data]


# Image Generator Module using D-ALLE 3, OpenAI API

import os
import time
import logging
from openai import OpenAI
from typing import List, Dict, Literal, Optional
import requests
from PIL import Image
from io import BytesIO
import boto3
import re 
import random

class ImageGeneratorAssistant:
    def __init__(self, api_key: Optional[str] = None, verbose: bool = False):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.aws_access_key_id = api_key or os.getenv("AWS_ACCESS")
        self.aws_secret_access_key = api_key or os.getenv("AWS_SECRET_KEY")
        self.bucket_name = api_key or os.getenv("BUCKET_NAME")
        self.prompt = None

        if not self.api_key:
            raise ValueError("OpenAI API key not provided and OPENAI_API_KEY environment variable not set")

        self.client = OpenAI(api_key=self.api_key)
        self.logger = logging.getLogger(__name__)
        self.verbose = verbose

        if self.verbose:
            logging.basicConfig(level=logging.DEBUG)

        if not all([self.aws_access_key_id, self.aws_secret_access_key, self.bucket_name]):
            raise ValueError("AWS credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, BUCKET_NAME) not provided and environment variables not set")

    def log_debug(self, message: str, *args, **kwargs):
        if self.verbose:
            self.logger.debug(message, *args, **kwargs)

    def generate_image(self, prompt: str, size: str = "1024x1024", n: int = 1, style: Literal['vivid', 'natural'] = 'vivid') -> List[str]:
        """
        Generate images based on the given prompt.

        Args:
            prompt (str): The text prompt for image generation.
            size (str): The size of the generated image. Defaults to "1024x1024".
            n (int): The number of images to generate. Defaults to 1.

        Returns:
            List[str]: A list of URLs for the generated images.
        """
        self.log_debug(f"Generating image with prompt: {prompt}")
        self.prompt = prompt
        # Generate the image using DALL-E
        response = self.client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size,
            n=n,
            style=style
        )
        self.log_debug(f"Image generation response: {response}")

        image_urls = [image.url for image in response.data]
        return self.download_and_upload_images(image_urls)

    def download_and_upload_images(self, image_urls: List[str]) -> List[str]:
        s3_urls = []
        for image_url in image_urls:
            self.log_debug(f"Downloading image from: {image_url}")
            try:
                response = requests.get(image_url)
                if response.status_code != 200:
                    self.log_debug(f"Error downloading image from {image_url}: {response.text}")
                    continue

                image_binary = response.content
                image_filename = re.sub(r'[^a-zA-Z0-9]', '', self.prompt)[:20] if re.sub(r'[^a-zA-Z0-9]', '', self.prompt) else f'image_{random.randint(1, 100000000)}'
                image_filename = f'{image_filename}.jpg'

                # connection to AWS
                s3 = boto3.client(
                    's3',
                    region_name='us-east-2',
                    aws_access_key_id=self.aws_access_key_id,
                    aws_secret_access_key=self.aws_secret_access_key
                )

                self.log_debug(f"\n\nUploading image to {self.bucket_name} bucket: {image_filename}")
                # Uploads the same image to the specified Bucket for the APP
                s3.upload_fileobj(BytesIO(image_binary), self.bucket_name, image_filename, ExtraArgs={'ContentType': 'image/jpeg'})

                s3_url = f"https://{self.bucket_name}.s3.us-east-2.amazonaws.com/{image_filename}"
                s3_urls.append(s3_url)
            except Exception as e:
                self.log_debug(f"Error downloading and uploading image: {str(e)}")
        return s3_urls



image_generator = ImageGeneratorAssistant(verbose=False)
