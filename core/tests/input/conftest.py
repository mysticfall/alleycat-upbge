import logging

from alleycat.test import mock_bge, mock_bpy

logging.basicConfig(level=logging.DEBUG)

mock_bpy.setup()
mock_bge.setup()
