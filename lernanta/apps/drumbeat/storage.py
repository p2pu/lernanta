import os
from PIL import Image
import logging

from django.core.files.storage import FileSystemStorage

log = logging.getLogger(__name__)


class ImageStorage(FileSystemStorage):

    format_extensions = {
        'PNG': 'png',
        'GIF': 'gif',
        'JPEG': 'jpg',
        'JPG': 'jpg',
    }

    def _save(self, name, content):
        name, ext = os.path.splitext(name)
        image = Image.open(content)
        if image.format in self.format_extensions:
            name = "%s.%s" % (name, self.format_extensions[image.format])
        else:
            log.warn("Attempt to upload image of unknown format: %s" % (
                image.format,))
            raise Exception("Unknown image format: %s" % (image.format,))
        name = super(ImageStorage, self)._save(name, content)
        image.save(self.path(name), image.format)
        return name
