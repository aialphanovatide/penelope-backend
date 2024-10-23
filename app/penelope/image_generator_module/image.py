from typing import List, Literal, Optional
from openai import OpenAI
import requests
import logging
import random
import boto3
import re 
import os


class ImageGeneratorAssistant:
    def __init__(self, api_key: Optional[str] = None, verbose: bool = False):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.aws_access_key_id = os.getenv("AWS_ACCESS")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_KEY")
        self.bucket_name = os.getenv("BUCKET_NAME")
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

        self.s3_client = self._create_s3_client()

    def _create_s3_client(self):
        return boto3.client(
            's3',
            region_name='us-east-2',
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key
        )

    def log_debug(self, message: str, *args, **kwargs):
        if self.verbose:
            self.logger.debug(message, *args, **kwargs)

    def generate_image(self, prompt: str, size: str = "1024x1024", n: int = 1, style: Literal['vivid', 'natural'] = 'vivid') -> List[str]:
        self.log_debug(f"Generating image with prompt: {prompt}")
        self.prompt = prompt
        response = self.client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size,
            n=n,
            style=style
        )
        self.log_debug(f"Image generation response: {response}")

        image_urls = [image.url for image in response.data]
        return self.fetch_and_store_images(image_urls)

    def fetch_and_store_images(self, image_urls: List[str]) -> List[str]:
        s3_urls = []
        for image_url in image_urls:
            self.log_debug(f"Downloading image from: {image_url}")
            try:
                response = requests.get(image_url)
                response.raise_for_status()

                image_binary = response.content
                image_filename = self._generate_filename()

                self.log_debug(f"Uploading image to {self.bucket_name} bucket: {image_filename}")
                s3_url = self._upload_to_s3(image_binary, image_filename)
                if s3_url:
                    s3_urls.append(s3_url)
            except requests.RequestException as e:
                self.log_debug(f"Error downloading image from {image_url}: {str(e)}")
            except Exception as e:
                self.log_debug(f"Error processing image: {str(e)}")
        return s3_urls

    def _upload_to_s3(self, image_binary, filename):
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=filename,
                Body=image_binary,
                ContentType='image/jpeg',
                ContentDisposition='attachment',
                # ACL='public-read'
            )
            return f"https://{self.bucket_name}.s3.amazonaws.com/{filename}"
        except Exception as e:
            self.log_debug(f"Error uploading to S3: {str(e)}")
            return None

    def _generate_filename(self):
        base_name = re.sub(r'[^a-zA-Z0-9]', '', self.prompt)[:20] or f'image_{random.randint(1, 100000000)}'
        return f'{base_name}.jpg'
    

image_generator = ImageGeneratorAssistant(verbose=False)