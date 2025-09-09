class MessagesBuilder:
    def __init__(self):
        self.messages = []

    def add_system(self, content: str):
        existing = next((msg for msg in self.messages if msg["role"] == "system"), None)
        if existing:
            existing["content"] += (
                "\n" + content
            )  # append with a newline for separation
        else:
            self.messages.insert(0, {"role": "system", "content": content})
        return self

    def add_user(self, content: str):
        self.messages.append({"role": "user", "content": content})
        return self

    def add_assistant(self, content: str):
        self.messages.append({"role": "assistant", "content": content})
        return self

    def build(self):
        return self.messages
    
    def clear(self):
        """
        Clear all messages in the builder.
        """
        self.messages = []
        return self