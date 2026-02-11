"""Image resize utility for project logos."""

from io import BytesIO

from django.core.files import File
from PIL import Image


class ImageResize:
    """Utility class to resize images while maintaining quality."""

    def resize_image(self, image, size=(900, 600)) -> File:
        """
        Resize an image to the specified size while maintaining aspect ratio.

        Args:
            image: The image file to resize
            size: Maximum size tuple (width, height)

        Returns:
            File: The resized image file
        """
        img = Image.open(image)

        # Convert RGBA and P modes to RGB
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        elif img.mode in ("JPEG"):
            pass

        # Resize while maintaining aspect ratio
        img.thumbnail(size)

        thumb_io = BytesIO()
        img.save(thumb_io, "JPEG", quality=100)

        import os

        base_name = os.path.basename(image.name)
        thumbnail = File(thumb_io, name=base_name)
        return thumbnail
