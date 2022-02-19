import json
import random
import os.path

import requests
from dotenv import load_dotenv


def get_random_comic_number():
    last_page_url = "https://xkcd.com/info.0.json"

    response = requests.get(last_page_url)
    response.raise_for_status()

    last_comic_num = response.json()["num"]
    all_comics_nums = [comic_num for comic_num in range(1, last_comic_num)]

    comic_number_to_publish = random.choice(all_comics_nums)

    return comic_number_to_publish


def fetch_comic_pic_title(comic_number_to_publish, precessed_file_name):
    processed_comic = f'https://xkcd.com/{comic_number_to_publish}/info.0.json'

    response = requests.get(processed_comic)
    response.raise_for_status()

    comic_img_title = response.json()
    processed_comic_link = comic_img_title["img"]
    title = comic_img_title["alt"]

    response = requests.get(processed_comic_link)
    response.raise_for_status()

    with open(precessed_file_name, 'wb') as file:
        file.write(response.content)

    return title


def upload_file_to_vk(payload, url_for_upload, pic_to_upload):
    with open(pic_to_upload, 'rb') as file:
        url = url_for_upload
        files = {
            'photo': file,
        }

        response = requests.post(url, params=payload, files=files)
        response.raise_for_status()

        return response.json()


def sending_requests_to_vk(method, payload):
    target_url = f'https://api.vk.com/method/{method}'

    response = requests.post(target_url, params=payload)
    response.raise_for_status()

    return response.json()


if __name__ == '__main__':
    load_dotenv()

    published_comics = "published_comics.json"

    processed_file_name = 'precessed_comic_pic.png'

    vk_access_token = os.getenv('VK_ACCESS_TOKEN')
    group_id = os.getenv('VK_GROUP_ID')

    fetch_vk_upload_url_method = 'photos.getWallUploadServer'
    save_photo_to_album_method = 'photos.saveWallPhoto'
    post_vk_wall_method = 'wall.post'

    try:
        comic_random_number = get_random_comic_number()
        comic_title = fetch_comic_pic_title(comic_random_number, processed_file_name)

        payload_for_fetch_upload_url = {
            'access_token': vk_access_token,
            'v': '5.131',
            'group_id': group_id
            }

        upload_url = sending_requests_to_vk(
            method=fetch_vk_upload_url_method,
            payload=payload_for_fetch_upload_url
        )["response"]["upload_url"]

        payload_for_upload_photo = {
            "group_id": group_id
        }

        saved_photo_info = upload_file_to_vk(
            payload=payload_for_upload_photo,
            url_for_upload=upload_url,
            pic_to_upload=processed_file_name
        )

        payload_for_save_photo_to_album = {
            'access_token': vk_access_token,
            'v': '5.131',
            'group_id': group_id,
            'photo': saved_photo_info["photo"],
            'server': int(saved_photo_info["server"]),
            'hash': saved_photo_info["hash"]
        }

        photo = sending_requests_to_vk(
            method=save_photo_to_album_method,
            payload=payload_for_save_photo_to_album
        )["response"][0]

        payload_for_post_vk_wall = {
            'access_token': vk_access_token,
            'v': '5.131',
            'owner_id': f'-{group_id}',
            'from_group': 1,
            'message': comic_title,
            'attachments': f'photo{photo["owner_id"]}_{photo["id"]}'
        }

        sending_requests_to_vk(
            method=post_vk_wall_method,
            payload=payload_for_post_vk_wall
        )
    finally:
        os.remove(processed_file_name)
