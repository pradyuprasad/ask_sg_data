def make_safe_filename(collection_name: str) -> str:
    """
    Converts a string into a safe filename by replacing unsafe characters with underscores.

    Args:
        collection_name (str): The original string to convert.

    Returns:
        str: A filename-safe version of the input string.
    """
    unsafe_characters: list[str] = [' ', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
    safe_filename: str = collection_name
    for char in unsafe_characters:
        safe_filename = safe_filename.replace(char, '_')
    return safe_filename
