# https://oauth.vk.com/authorize?client_id=8225570&display=page&redirect_uri=https%3A%2F%2Foauth.vk.com%2Fblank.html&scope=photos&response_type=token&v=5.52

from typing import Optional, Any
import requests
import json
import os


VK_token = 'vk1.a.8u6FMMTwFhzrWLCXrp8kpklH0mjF_EdsDvNgBIRHN_bemnFZdF3iac8SxO1cQ0tXQVlTf3AYZsuy8qR7RygTKT_YLjAOD4FE8SaDBrG7i7jOk5Nb_VKl9DqFbubF8D5ouZvv6L7d8HogMmzMrT1mOzdPj9V39i6s2QZtq-c4gLVwLHUOKPem2TPBMXHbXC1X'
VK_userid = '137239236'


class VKPhotoDownload:
    """
        main class
    """

    def __init__(self, token: str, userid: str):
        self._token = token
        self._userid = userid
        self._api = "https://api.vk.com/method/"

    def get_photo_data(self, offset: int = 0, count: int = 200) -> json:
        """
            get photo data
        :param offset: offset
        :param count: count # 200 - max not sure if it's working
        :return: json
        """
        params = {
            'owner_id': self._userid,
            'access_token': self._token,
            'offset': offset,
            'count': count,
            'v': 5.81
        }

        print('Get photo data')
        rqst = requests.get(self.method('photos.getAll'), params)

        return json.loads(rqst.text)

    @staticmethod
    def download_photo(url: str, album_name: str) -> None:
        """
            download photo
        :param album_name: album name
        :param url: url
        :return: none
        """
        rqst = requests.get(url)
        file_name = url.split("/")[-1].split('?')[0]
        print(f'Download file: {file_name}')

        with open(f"images/{album_name}/{file_name}", "wb") as f:
            f.write(rqst.content)

    def method(self, method_name: str) -> str:
        """
            call method of api
        :param method_name:
        :return: url
        """
        return f"{self._api}/{method_name}"

    @staticmethod
    def album_add(album_name: str) -> None:
        """
            make all folders for downloading
        :param album_name: album name
        :return:
        """

        if not os.path.isdir('images'):
            os.mkdir('images')
        if not os.path.isdir(f'images/{album_name}'):
            print(f'Creating folder for album {album_name}')
            os.mkdir(f'images/{album_name}')

    def get_album_name(self, album_id: int) -> str:
        """
            get album name via api + check folder created
        :param album_id: album id
        :return: album name
        """
        album_name = None

        if album_id == -7:
            album_name = 'Wall photos'
        elif album_id == -6:
            album_name = 'My photos'

        if album_name:
            self.album_add(album_name)
            return album_name

        params = {
            "access_token": self._token,
            "owner_id": self._userid,
            "album_ids": [album_id],
            "offset": 0,
            "count": 1,
            "need_system": 0,
            "need_covers": 0,
            "photo_sizes": 0,
            "v": 5.81
        }

        rqst = requests.get(self.method('photos.getAlbums'), params)
        album = json.loads(rqst.content).get('response').get('items')[0]
        album_name = album.get('title')
        new_album_id = album.get('id')
        assert album_id == new_album_id, 'Wrong ID from API!'

        self.album_add(album_name)

        return album_name

    @staticmethod
    def save_progress(iterator: int, count: int) -> None:
        """
            save progress to file
        :param iterator: iterator
        :param count: count
        :return:
        """
        settings = {
            'count': count,
            'iterator': iterator
        }
        with open('settings.json', 'w') as sf:
            json.dump(settings, sf)

    @staticmethod
    def load_progress() -> Optional[Any]:
        """
            load progress from file
        :return:
        """
        try:
            with open('settings.json', 'r') as sf:
                return json.load(sf)
        except FileNotFoundError:
            return None

    @staticmethod
    def handle_buged_photo(photo_id: int) -> None:
        """
            handle with photos with empty 'sizes'
        :param photo_id: photo id
        :return: None
        """

        print(f'Photo with no sizes was found! ID: {photo_id}')
        if not os.path.isfile('bug_photos.json'):
            template = {
                'bug_photos': [photo_id]
            }
            with open('bug_photos.json', 'w') as bp:
                json.dump(template, bp)
        else:
            with open('bug_photos.json', 'r+') as bp:
                bug_photos_list = json.load(bp).get('bug_photos_list')
                if photo_id not in bug_photos_list:
                    bug_photos_list.append(photo_id)
                    print('Photo ID saved!')
                    bp.truncate(0)
                    json.dump({"bug_photos_list": bug_photos_list}, bp)
                else:
                    print('Photo ID is in list already!')

    def download_everything(self) -> None:
        """
            main func
        :return: none
        """
        settings = self.load_progress()
        if settings:
            offset = settings.get('iterator')
        else:
            offset = 0
        iterator = offset + 1
        while True:
            print(f'Renew photos with offset {offset}')
            data = self.get_photo_data(offset).get('response')
            count = data.get('count')
            offset += len(data.get('items'))
            if len(data.get('items')) == 0:
                break
            for item in data.get('items'):
                album_id = item.get('album_id')
                photo_id = item.get('id')
                album_name = self.get_album_name(album_id)
                print(f'Album name: {album_name}')
                print(f'Photo ID: {photo_id}')
                item.get('sizes').sort(key=lambda x: x.get('height'))
                if len(item.get('sizes')) == 0:
                    self.handle_buged_photo(photo_id)
                    iterator += 1
                    continue
                photo_url = item.get('sizes')[-1].get('url')
                print(f'{iterator}/{count} ==== {round(iterator/count, 4)*100}%')
                self.save_progress(iterator, count)
                iterator += 1
                self.download_photo(photo_url, album_name)


if __name__ == '__main__':
    VKPhotoDownload(VK_token, VK_userid).download_everything()
