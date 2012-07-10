import os
import tempfile
import urllib2
import Image
import logging
import datetime
import simplejson

from lxml import html

from django.conf import settings

from drumbeat.utils import get_partition_id, safe_filename

log = logging.getLogger(__name__)


def determine_image_upload_path(instance, filename):
    return "images/projects/%(partition)d/%(filename)s" % {
        'partition': get_partition_id(instance.pk),
        'filename': safe_filename(filename),
    }


class Mock(object):

    def __init__(self, pk):
        self.pk = pk

format_extensions = {
    'PNG': 'png',
    'GIF': 'gif',
    'JPEG': 'jpg',
    'JPG': 'jpg',
}

mime_types_extensions = {
    'image/jpeg': 'jpg',
    'image/jpg': 'jpg',
    'image/png': 'png',
    'image/gif': 'gif',
}

image_mime_types = mime_types_extensions.keys()


def copy_image(image_url):
    """
    Download an image into a temp file, transcode the image and save it in
    the project image directory.
    """
    try:
        image_fp = urllib2.urlopen(image_url, timeout=5)
    except urllib2.URLError:
        log.warn("Error opening %s. Returning." % (image_url,))
        return None

    if not image_fp:
        log.warn("Error opening %s. Returning." % (image_url,))
        return None
    headers = image_fp.info()

    max_image_size = getattr(settings, 'MAX_IMAGE_SIZE', None)
    if not max_image_size:
        log.warn("No MAX_IMAGE_SIZE set")
        return None

    # check that file is not too large and is an image.
    if 'Content-Length' not in headers:
        log.warn("No content-length in headers. Returning")
        return None
    if int(headers['Content-Length']) > max_image_size:
        log.warn("Content-length header exceeds max allowable size. Returning")
        return None
    if headers['Content-Type'] not in image_mime_types:
        log.warn("Content-type header not an allowable mime type. Returning")
        return None

    tmpfile, tmpfile_name = tempfile.mkstemp()
    tmpfile_fp = os.fdopen(tmpfile, 'w+b')

    downloaded = 0
    chunk_size = 1024
    while True:
        chunk = image_fp.read(chunk_size)
        if not chunk:
            break
        downloaded += chunk_size
        if downloaded > max_image_size:
            tmpfile_fp.close()
            image_fp.close()
            os.unlink(tmpfile_fp)
            return None
        tmpfile_fp.write(chunk)

    tmpfile_fp.close()
    image_fp.close()

    return tmpfile_name


def strip_remote_images(content, pk):
    """
    Find all img tags in content. Download the image referred to in the src
    attribute, run it through PIL to strip out any comments, and replace
    the attribute value with a local url.
    """
    tree = html.fromstring(content)
    img_urls = [img.get('src', None) for img in tree.xpath('//img')]

    media_root = getattr(settings, 'MEDIA_ROOT', None)
    media_url = getattr(settings, 'MEDIA_URL', None)

    if not media_root or not media_url:
        return None

    new_urls = []
    for img_url in img_urls:
        tmpfile = copy_image(img_url)
        if tmpfile is None:
            new_urls.append("")
            continue
        try:
            image_basename = img_url.split('/')[-1]
            image_path = determine_image_upload_path(Mock(pk), image_basename)
            destination = os.path.join(media_root, image_path)

            image = Image.open(tmpfile)
            basename, ext = os.path.splitext(destination)
            if (ext[1:] not in mime_types_extensions.values()):
                destination = "%s.%s" % (
                    basename, format_extensions[image.format])
            image.save(destination, image.format)
            new_urls.append(os.path.join(media_url, image_path))
        except Exception, e:
            log.warn("Error stripping out remote image: %s" % (e,))
            new_urls.append("")
        finally:
            os.unlink(tmpfile)

    for i in range(len(img_urls)):
        # markdown replaces & with &amp; even if it's part of a querystring
        old = img_urls[i].replace('&', '&amp;')
        new = new_urls[i]
        log.debug("replacing %s with %s" % (old, new))
        content = content.replace(old, new)

    return content

def json_date_encoder(obj):
    if isinstance(obj, datetime.date):
        return obj.isoformat()
    else:
        return simplejson.dumps(obj)
