"""
Core constants used by the MediaWiper application.
"""

# Define standard file categories and extensions
FILE_CATEGORIES = {
    "Video": ['.mp4', '.avi', '.flv', '.wmv', '.mov', '.webm', '.mkv', '.f4v', '.vob', '.ogg', '.gifv', '.amv', '.mpg', '.mp2', '.mpeg', '.mpe', '.mpv', '.m4v', '.3gp'],
    "Audio": ['.wav', '.aiff', '.mp3', '.aac', '.wma', '.ogg', '.flac'],
    "Images": ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg'],
    "Documents": ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.rtf', '.odt']
}

# Constants for secure deletion
CHUNK_SIZE = 1024 * 1024  # 1MB chunks for overwriting
