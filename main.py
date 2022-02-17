import json
import random
import os.path

import requests
from dotenv import load_dotenv


def processing_published_comic(published_comics_file, comic_number_for_append=0, pic_to_delete=''):
    published_comics_nums = []

    if os.path.exists(published_comics_file):
        with open(published_comics_file, 'r', encoding='utf-8') as file:
            published_comics_nums = json.load(file)

    if comic_number_for_append and pic_to_delete:
        published_comics_nums.append(comic_number_for_append)

        with open(published_comics_file, 'w') as file:
            json.dump(published_comics_nums, file)

        os.remove(pic_to_delete)

        return

    return published_comics_nums


def get_random_comic_number(published_comics_nums):
    last_page_url = "https://xkcd.com/info.0.json"

    response = requests.get(last_page_url)
    response.raise_for_status()

    last_comic_num = response.json()["num"]
    all_comics_nums = [comic_num for comic_num in range(1, last_comic_num)]

    unpublished_comics_nums = set(all_comics_nums) - set(published_comics_nums)

    comic_number_to_publish = random.choice(list(unpublished_comics_nums))

    return comic_number_to_publish


def fetch_comic_pic_title_ext(comic_number_to_publish, precessed_file_name):
    page_url_template = "https://xkcd.com/page_number/info.0.json"

    processed_comic = page_url_template.replace("page_number", str(comic_number_to_publish))

    response = requests.get(processed_comic)
    response.raise_for_status()

    processed_comic_link = response.json()["img"]
    title = response.json()["alt"]

    response = requests.get(processed_comic_link)
    response.raise_for_status()

    pic_ext = os.path.splitext(processed_comic_link)[1]

    with open(f'{precessed_file_name}{pic_ext}', 'wb') as file:
        file.write(response.content)

    return title, pic_ext


def fetch_upload_vk(method='', payload={}, url_for_upload='', pic_to_upload=''):
    if url_for_upload and pic_to_upload:
        with open(pic_to_upload, 'rb') as file:
            url = url_for_upload
            files = {
                'photo': file,
            }

            response = requests.post(url, params=payload, files=files)
            response.raise_for_status()

            return response.json()

    target_url = f'https://api.vk.com/method/{method}'

    response = requests.post(target_url, params=payload)
    response.raise_for_status()

    return response.json()


if __name__ == '__main__':
    load_dotenv()

    published_comics = "published_comics.json"

    processed_file_name = 'precessed_comic_pic'

    vk_access_token = os.getenv('VK_ACCESS_TOKEN')
    group_id = os.getenv('VK_GROUP_ID')

    fetch_vk_upload_url_method = 'photos.getWallUploadServer'
    save_photo_to_album_method = 'photos.saveWallPhoto'
    post_vk_wall_method = 'wall.post'

    published_comics_list = processing_published_comic(published_comics)
    comic_random_number = get_random_comic_number(published_comics_list)
    comic_info = fetch_comic_pic_title_ext(comic_random_number, processed_file_name)
    comic_title = comic_info[0]
    comic_pic_ext = comic_info[1]
    processed_file = f'{processed_file_name}{comic_pic_ext}'

    payload_for_fetch_upload_url = {
        'access_token': vk_access_token,
        'v': '5.131',
        'group_id': group_id
        }

    upload_url = fetch_upload_vk(
        method=fetch_vk_upload_url_method,
        payload=payload_for_fetch_upload_url
    )["response"]["upload_url"]

    payload_for_upload_photo = {
        "group_id": group_id
    }

    saved_photo_info = fetch_upload_vk(
        payload=payload_for_upload_photo,
        url_for_upload=upload_url,
        pic_to_upload=processed_file
    )

    payload_for_save_photo_to_album = {
        'access_token': vk_access_token,
        'v': '5.131',
        'group_id': group_id,
        'photo': saved_photo_info["photo"],
        'server': int(saved_photo_info["server"]),
        'hash': saved_photo_info["hash"]
    }

    photo = fetch_upload_vk(
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

    fetch_upload_vk(
        method=post_vk_wall_method,
        payload=payload_for_post_vk_wall
    )

    processing_published_comic(published_comics, comic_random_number, processed_file)
