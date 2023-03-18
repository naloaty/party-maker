class Resource:
    __invalid: bool = False

    def __getattribute__(self, name: str):
        if "invalid" in name:
            return super().__getattribute__(name)
        if self.__invalid:
            raise RuntimeError("Could not access resource outside of @action scope")
        else:
            return super().__getattribute__(name)

    def invalidate(self):
        attrs = [a for a in dir(self) if not a.startswith('__')]
        for attr_name in attrs:
            setattr(self, attr_name, None)
        self.__invalid = True

    def invalid(self) -> bool:
        return self.__invalid
