#coding=utf-8

class UserModel:
    id=''
    username=''
    displayName=''
    currentAvatarImageUrl=''
    status=''
    statusDescription=''
    location=''

    def __init__(self,data):
        self.set_attrs(data)

    def set_attrs(self, attrs):
        for key, value in attrs.items():
            if hasattr(self, key):
                setattr(self, key, value)