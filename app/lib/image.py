def image_path_generator(instance, filename):
    import os
    from datetime import datetime

    base, ext = os.path.splitext(filename)
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    new_filename = f"{base}_{timestamp}{ext}"
    return os.path.join("images", new_filename)