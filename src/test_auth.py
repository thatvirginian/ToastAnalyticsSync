# -*- coding: utf-8 -*-

from src.toast_api import ToastAPI

def test_auth():
    toast = ToastAPI()
    token = toast.get_token()
    print("Access token:", token[:25] + "...")  # only show first chars

if __name__ == "__main__":
    test_auth()