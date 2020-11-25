class GlobalDefaults:
    def __init__(self,
        username,
        password
    ):
        self.username = username
        self.password = password

class Settings:
    def __init__(self, 
        interval, 
        defaultUsername, 
        defaultPassword
    ):
        self.interval = int(interval)

        self.defaults = GlobalDefaults(
            username = defaultUsername,
            password = defaultPassword
        )
