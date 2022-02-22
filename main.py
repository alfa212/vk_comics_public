import random
import os.path

import requests
from dotenv import load_dotenv


def get_random_comic_number():
    last_page_url = "https://xkcd.com/info.0.json"

    response = requests.get(last_page_url)
    response.raise_for_status()

    last_comic_num = response.json()["num"]

    comic_number = random.randrange(1, last_comic_num)

    return comic_number


def fetch_comic_pic_title(comic_number, precessed_file_name):
    processed_comic = f'https://xkcd.com/{comic_number}/info.0.json'

    response = requests.get(processed_comic)
    response.raise_for_status()

    comic_img_title = response.json()
    comics_link = comic_img_title["img"]
    title = comic_img_title["alt"]

    response = requests.get(comics_link)
    response.raise_for_status()

    with open(precessed_file_name, 'wb') as file:
        file.write(response.content)

    return title


class VKError(Exception):
    def __init__(self, num, text):
        self.n = num
        self.txt = text


def find_vk_errors(vk_answer):
    raise VKError(f'VK Error code: {vk_answer["error"]["error_code"]}',
                  f'VK Error message: {vk_answer["error"]["error_msg"]}')


def upload_file_to_vk(vk_group, url_for_upload, pic_to_upload):
    with open(pic_to_upload, 'rb') as file:
        url = url_for_upload
        files = {
            'photo': file,
        }
        payload = {
            "group_id": vk_group
        }

        response = requests.post(url, params=payload, files=files)
        response.raise_for_status()

        vk_answer = response.json()

        if "error" in vk_answer:
            find_vk_errors(vk_answer)

        return vk_answer


def sending_requests_to_vk(api_token, api_version, vk_group, method, payload={}):
    target_url = f'https://api.vk.com/method/{method}'

    payload['access_token'] = api_token,
    payload['v'] = api_version,
    payload['group_id'] = vk_group

    response = requests.post(target_url, params=payload)
    response.raise_for_status()

    vk_answer = response.json()

    if "error" in vk_answer:
        find_vk_errors(vk_answer)

    return vk_answer


if __name__ == '__main__':
    load_dotenv()

    comics_name = 'precessed_comic_pic.png'

    vk_access_token = os.getenv('VK_ACCESS_TOKEN')
    group_id = os.getenv('VK_GROUP_ID')
    vk_api_version = '5.131'

    fetch_vk_upload_url_method = 'photos.getWallUploadServer'
    save_photo_to_album_method = 'photos.saveWallPhoto'
    post_vk_wall_method = 'wall.post'

    try:
        comic_random_number = get_random_comic_number()
        comic_title = fetch_comic_pic_title(comic_random_number, comics_name)

        upload_url = sending_requests_to_vk(
            vk_access_token,
            vk_api_version,
            group_id,
            fetch_vk_upload_url_method
        )["response"]["upload_url"]

        saved_photo_info = upload_file_to_vk(
            group_id,
            url_for_upload=upload_url,
            pic_to_upload=comics_name
        )

        payload_for_save_photo_to_album = {
            'photo': saved_photo_info["photo"],
            'server': int(saved_photo_info["server"]),
            'hash': saved_photo_info["hash"]
        }

        photo = sending_requests_to_vk(
            vk_access_token,
            vk_api_version,
            group_id,
            method=save_photo_to_album_method,
            payload=payload_for_save_photo_to_album
        )["response"][0]

        payload_for_post_vk_wall = {
            'owner_id': f'-{group_id}',
            'from_group': 1,
            'message': comic_title,
            'attachments': f'photo{photo["owner_id"]}_{photo["id"]}'
        }

        sending_requests_to_vk(
            vk_access_token,
            vk_api_version,
            group_id,
            method=post_vk_wall_method,
            payload=payload_for_post_vk_wall
        )
    finally:
        os.remove(comics_name)
