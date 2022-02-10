import aiohttp
import asyncio

def login() -> bool:
    _login = input('do you have an existing account? y/n')
    if _login.lower() in ['yes', 'y']:
        login = True
    else:
        login = False

    if login:
        usr = input('username: ')
        passwrd = input('password: ')
        # idk
    else:
        usr = input('enter new username: ')
        # check if taken
        _passwrd = input('enter password: ')
        __passwrd = input('repeat password')
        if _passwrd != __passwrd:
            return False
        # send account request

if __name__ == "__main__":
    while login() != True:
        pass
