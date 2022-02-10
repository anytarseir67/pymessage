import aiohttp
from aiohttp import web
import asyncpg
import secrets

try:
    import config
except ImportError:
    import sys
    sys.exit('config not found, create a config.py based on the example')

routes = web.RouteTableDef()

class PyMessageServer(web.Application):

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._port = config.port
        self.sockets = {} # id: socket


    def run(self) -> None:
        self.on_startup.append(self.db_init)
        self.add_routes(routes)
        web.run_app(self, port=self._port)


    async def db_init(self, app):
        self.conn = await asyncpg.connect(user=config.db_user, password=config.db_password,
                                    database=config.db, host=config.db_host)


    async def get_user(self, id: int) -> dict:
        resp = await self.conn.fetch('SELECT * FROM accounts WHERE id=$1', id)
        resp = resp[0]
        if resp:
            resp = resp[0]
            user = {'username': resp['username']}
            return user
        return None


    async def get_friends(self, id) -> list:
        try:
            _friends = await self.conn.fetch('SELECT added FROM accounts WHERE id=$1', id)
            _friends = _friends[0]
            friends = []
            for friend in _friends:
                friend = await self.get_user(friend)
                friends.append(friend)
            return {'type': 'friends_resp', 'friends': friends}
        except:
            return {'type': 'error', 'error': 'failed to get friends'}


    async def request_friend(self, sender: int, receiver: int):
        try:
            receiver_socket = self.sockets.get(receiver)
            if receiver_socket:
                await self.conn.execute('UPDATE accounts SET outgoing = array_append(outgoing, $1) WHERE id = $2', receiver, sender)
                await self.conn.execute('UPDATE accounts SET incoming = array_append(incoming, $1) WHERE id = $2', sender, receiver)
                await receiver_socket.send_json({'type': 'friend_request', 'user': sender})
                return {'type': 'request_resp', 'status': 'sent'}
            return {'type': 'request_resp', 'status': f'{receiver} is not connected to the network'}
        except:
            return {'type': 'error', 'error': f'failed to send friend request to {receiver}'}


    async def add_friend(self, sender: int, receiver: int):
        sender_list = await self.conn.fetch('SELECT outgoing FROM accounts WHERE id = $1', sender)
        receiver_list = await self.conn.fetch('SELECT incoming FROM accounts WHERE id = $1', receiver)
        sender_list = sender_list[0]['outgoing']
        receiver_list = receiver_list[0]['incoming']

        sender_list.pop(receiver)
        receiver_list.pop(sender)
        await self.conn.execute('UPDATE accounts SET outgoing = $1 WHERE id = $2', sender_list, sender)
        await self.conn.execute('UPDATE accounts SET incoming = $1 WHERE id = $2', receiver_list, receiver)

        await self.conn.execute('UPDATE accounts SET added = array_append(added, $1) WHERE id = $2', sender, receiver)
        await self.conn.execute('UPDATE accounts SET added = array_append(added, $1) WHERE id = $2', receiver, sender)
        return {'type': 'add_resp', 'status': 'added'}


    async def deny_friend(self, sender: int, receiver: int):
        await self.conn.execute('UPDATE accounts SET outgoing = array_remove(outgoing, $1) WHERE id = $2', receiver, sender)
        await self.conn.execute('UPDATE accounts SET incoming = array_remove(incoming, $1) WHERE id = $2', sender, receiver)
        return {'type': 'deny_resp', 'status': 'success'}


    async def send_message(self, user, data):
        to_send = self.sockets.get(data['recipient'])
        if not to_send:
            return {'type': 'error', "error": f"{data['recipient']} is not connected to the network"}
        if config.msg_nonfriend:
                await to_send.send_json({'type': 'message', 'sender': user, 'content': data['content']})
                return {'type': 'send_resp', 'status': 'success'}

        else:
            user_friends = self.conn.fetch('SELECT added FROM accounts WHERE id = $1', user)
            user_friends = user_friends[0]['added']
            if data['recipient'] in user_friends:
                await to_send.send_json({'type': 'message', 'sender': user, 'content': data['content']})
                return {'type': 'send_resp', 'status': 'success'}

            
    async def login(self, ws, msg: aiohttp.WSMessage, json):
        resp = await self.conn.fetch('SELECT id FROM accounts WHERE username=$1 AND pin=$2', json['username'], json['pin'])
        resp = resp[0]
        if len(str(resp['id'])) == 8:
            ws['user'] = resp['id']
            self.sockets[resp['id']] = ws
            return {'type': 'resp', 'id': resp['id']}
        return {'type': 'error', 'error': 'acc not found'}


    async def create_acc(self, ws, msg, json) -> bool:
        try:
            does_exist = await self.conn.fetch('SELECT id FROM accounts WHERE username=$1', json['username'])
            does_exist = does_exist[0]['id']
            if len(does_exist) == 0:
                id = secrets.choice(range(10000000, 99999999))
                usr = json['username']
                pin = json['pin']
                token = f'{id}_{secrets.token_hex(16)}'
                await self.conn.execute('INSERT INTO accounts (username, pin, id, token) VALUES ($1, $2, $3, $4)', usr, pin, id, token)
                id = await self.login(ws, msg, {'username': usr, 'pin': pin})
                return {'type': 'create_acc_resp', 'id': id}
            return {'type': 'error', 'error': 'username is taken'}
        except:
            return {'type': 'error', 'error': 'failed to create account'}


    @routes.get('/')
    async def listen(request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                data = msg.json()

                if data['type'] == 'login':
                    resp = await app.login(ws, msg, data)
                    await ws.send_json(resp)

                elif data['type'] == 'create_acc':
                    resp = await app.create_acc(ws, msg, data)
                    await ws.send_json(resp)

                elif ws.get('user'):
                    if data['type'] == 'send_msg':
                        await app.send_message(ws['user'], data)

                    elif data['type'] == 'get_friends':
                        friends = await app.get_friends(ws['user'])
                        await ws.send_json(friends)

                    elif data['type'] == 'request_friend':
                        resp = await app.request_friend(ws['user'], data['user'])
                        await ws.send_json(resp)
                    
                    elif data['type'] == 'add_friend':
                        resp = await app.add_friend(data['user'], ws['user'])
                        await ws.send_json(resp)

                    elif data['type'] == 'deny_friend':
                        resp = await app.deny_friend(data['user'], ws['user'])
                        await ws.send_json(resp)

                else:
                    await ws.send_json({'type': 'error', 'error': 'endpoint not found'})

            elif msg.type == aiohttp.WSMsgType.ERROR:
                print('ws connection closed with exception %s' % ws.exception())

        app.sockets.pop(ws['user'])

    @routes.get('/get_user')
    async def rest_get_user(request):
        user = await app.get_user(int(request.rel_url.query['id']))
        return web.json_response({'user': user})


if __name__ == "__main__":
    app = PyMessageServer()
    app.run()