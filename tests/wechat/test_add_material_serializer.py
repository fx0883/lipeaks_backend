import os
import unittest
from io import BytesIO

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django

django.setup()

from django.core.files.uploadedfile import SimpleUploadedFile

from wechat.serializers import WechatAddMaterialRequestSerializer


class WechatAddMaterialRequestSerializerTests(unittest.TestCase):
    def test_type_defaults_to_image_when_omitted(self):
        image_file = SimpleUploadedFile(
            "cover.png",
            b"fake-png",
            content_type="image/png",
        )

        serializer = WechatAddMaterialRequestSerializer(
            data={
                "account_appid": "wx123",
                "media": image_file,
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["type"], "image")


if __name__ == "__main__":
    unittest.main()
