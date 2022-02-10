# pymessage
instant messenger written in pure python



## Socket endpoints:

all communication with the socket should send JSON, and should always include a `type` key that corresponds to the desired endpoint. 

### login - endpoint for initial socket authorization, should only be called once, and immediately after connection

* Arguments: 
* * username **|** string **|** username of desired user
* * pin **|** int **|** pin of user

* Expected response:
* * **{'type': 'resp', 'id': `user id` }**

* Error response:
* * **{'type': 'error', 'error': 'acc not found'}**


### create_acc - endpoint for account creation. socket is automatically authorized, DO NOT call `login`.

* Arguments:
* * username **|** string **|** desired username 
* * pin **|** string **|** desired pin

* Expected response:
* * **{'type': 'create_acc_resp', 'id': `user id` }**

* Error response:
* * **{'type': 'error', 'error': 'username is taken'}**
* * **{'type': 'error', 'error': 'failed to create account'}**


### send_msg - endpoint to send a message

* Arguments:
* * recipient **|** id (int) **|** user to send a message too
* * content **|** string **|** message content to send

* Expected response:
* * **{'type': 'send_resp', 'status' 'success'}**

* Error response:
* * **{'type': 'error', 'error': ' `recipient`  is not connected to the network'}**


### get_friends - endpoint to get your friend list
* Arguments:
* * none

* Expected response:
* * **{'type': 'friends_resp', 'friends': [{'username': `Username` , 'id': `id` }]}**

* Error response:
* * **{'type': 'error', 'error': 'failed to get friends'}**


### request_friend - endpoint to send a friend request
* Arguments: 
* * user **|** id (int) **|** user to send a friend request to

* Expected response:
* * **{'type': 'request_resp', 'status': 'sent'}**

* Error response:
* * **{'type': 'error', 'error': 'failed to send friend request to `user` '}**


### add_friend - endpoint to accept a friend request
* Arguments:
* * user **|** id (int) **|** id of the user to accept a request from

* Expected response:
* * **{'type': 'add_resp', 'status': 'added'}**


### deny_friend - endpoint to deny friend request
* Arguments:
* * user **|** id (int) **|** id of the user to deny a request from

* Expected response:
* * **{'type': 'deny_resp', 'status': 'success'}**



## Socket events:


all socket events send JSON, they always include a `type` key, all expected data is included in the json.


### friend_request - event to notify of an incoming friend request

* Expected data:
* * user **|** id (int) **|** id of user who sent a request


### message - event to notify of a new message

* Expected data:
* * sender **|** id (int) **|** id of user who sent a message
* * content **|** string **|** content of the message



## Socket examples:

`->` is data you send to the socket

`<-` is data you recieve from the socket

`|` means a possible alternative of the previous line (usually an error `type`)


* ### Authorization:
* * #### Login:
* * *  -> `{'type': 'login', 'username': 'EpicUserName', 'pin': 'password123'}`
* * * <- `{'type': 'resp', 'id': '12345678'}`


* * ### Creating an account:
* * * -> `{'type': 'create_acc', 'username': 'EpicUserName2', 'pin': 'password1234'}`
* * * <- `{'type': 'create_acc_resp', 'id': '12345678'}`
* * * | `{'type': 'error', 'error': 'username is taken'}`
* * * | `{'type': 'error', 'error': 'failed to create account'}`

## Rest api:

all rest endpoints expect arguments in query strings

### get_user - endpoint to get info about a user

* Arguments:
* * id **|** id (int) **|** id of user to get

* Expected response:
* * **{'user': {'username': 'EpicUserName'}}**
