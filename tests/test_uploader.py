import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import uploader


class _UploadRequest:
    def next_chunk(self):
        return None, {"id": "video-id"}


class _VideosResource:
    def __init__(self):
        self.insert_kwargs = None

    def insert(self, **kwargs):
        self.insert_kwargs = kwargs
        return _UploadRequest()


class _YouTubeClient:
    def __init__(self):
        self.videos_resource = _VideosResource()

    def videos(self):
        return self.videos_resource


class UploadToYouTubeTests(unittest.TestCase):
    def setUp(self):
        self.meta = {
            "title": "Test Short #Shorts",
            "description": "Test description",
            "tags": ["Shorts"],
            "categoryId": "24",
            "privacyStatus": "public",
        }

    def _upload(self, meta):
        youtube = _YouTubeClient()
        with tempfile.NamedTemporaryFile(suffix=".mp4") as video:
            with patch.object(uploader, "MediaFileUpload", return_value=object()):
                response = uploader.upload_to_youtube(youtube, Path(video.name), meta)
        return response, youtube.videos_resource.insert_kwargs

    def test_status_defaults_both_audience_settings_to_false(self):
        response, request = self._upload(self.meta)

        self.assertEqual(response, {"id": "video-id"})
        self.assertEqual(request["part"], "snippet,status")
        self.assertEqual(
            request["body"]["status"],
            {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False,
                "containsSyntheticMedia": False,
            },
        )

    def test_scheduled_upload_preserves_publish_time_and_boolean_overrides(self):
        publish_at = "2026-10-10T09:00:00-04:00"
        meta = {
            **self.meta,
            "privacyStatus": "unlisted",
            "publishAt": publish_at,
            "selfDeclaredMadeForKids": True,
            "containsSyntheticMedia": True,
        }

        _, request = self._upload(meta)

        self.assertEqual(
            request["body"]["status"],
            {
                "privacyStatus": "private",
                "selfDeclaredMadeForKids": True,
                "containsSyntheticMedia": True,
                "publishAt": publish_at,
            },
        )

    def test_boolean_overrides_reject_strings(self):
        for key in ("selfDeclaredMadeForKids", "containsSyntheticMedia"):
            with self.subTest(key=key):
                with self.assertRaisesRegex(TypeError, rf"^{key} must be a bool"):
                    self._upload({**self.meta, key: "false"})


if __name__ == "__main__":
    unittest.main()
