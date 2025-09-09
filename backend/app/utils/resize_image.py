from typing import Tuple
from PIL import Image
import os

def smart_resize_image(image_path: str, max_size: int, min_size: int) -> str:
    """
    Resize the image to the target size and save it.
    """
    with Image.open(image_path) as img:
        # Convert RGBA to RGB if saving as JPEG
        if img.mode == 'RGBA':
            # Create a white background and paste the RGBA image on it
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[-1])  # Use alpha channel as mask
            img = rgb_img
            
        width, height = img.size
        
        max_iterations = 20  # Limit iterations to prevent infinite loop
        # iteratively resize until within bounds, double or devide by 2 until within bounds
        while width > max_size or height > max_size or width < min_size or height < min_size:
            if width > max_size or height > max_size:
                # Scale down by half
                width = width // 2
                height = height // 2
            elif width < min_size or height < min_size:
                # Scale up by double
                width = width * 2
                height = height * 2
            max_iterations -= 1
            if max_iterations <= 0:
                raise ValueError("Image resizing exceeded maximum iterations, check image dimensions.")
        
        
        img = img.resize((width, height), Image.LANCZOS)
        
        # Generate resized file path, keeping original extension or using .jpg
        base_path = os.path.splitext(image_path)[0]
        original_ext = os.path.splitext(image_path)[1].lower()
        
        # Use .jpg for most formats, but preserve .png if original was PNG and no transparency issues
        if original_ext in ['.png', '.jpg', '.jpeg']:
            resized_path = f"{base_path}_resized{original_ext}"
        else:
            resized_path = f"{base_path}_resized.jpg"
        
        # Save with appropriate format
        if resized_path.endswith('.png'):
            img.save(resized_path, 'PNG')
        else:
            img.save(resized_path, 'JPEG', quality=95)
        
        return resized_path