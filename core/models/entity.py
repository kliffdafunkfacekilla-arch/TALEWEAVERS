import uuid

class Entity:
    def __init__(self, name, x, y, char="?", color="white"):
        self.uid = str(uuid.uuid4())[:8]
        self.name = name
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        
        # THE CORE MAGIC: A simple set of strings
        self.tags = set()
        
        # Data payload for specific tags (e.g. lock difficulty)
        self.data = {} 

    def add_tag(self, tag, **kwargs):
        self.tags.add(tag)
        # Store extra data if needed (e.g., tag="locked", key_id="iron_key_1")
        if kwargs:
            self.data.update(kwargs)

    def has_tag(self, tag):
        return tag in self.tags

    def remove_tag(self, tag):
        self.tags.discard(tag)
