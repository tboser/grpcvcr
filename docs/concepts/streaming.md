# Streaming RPCs

grpcvcr supports all four gRPC call types.

## RPC Types

### Unary (Single Request, Single Response)

The simplest RPC type. One request, one response.

```python
with recorded_channel("test.yaml", "localhost:50051") as channel:
    stub = UserServiceStub(channel)
    response = stub.GetUser(GetUserRequest(id=1))
```

### Server Streaming (Single Request, Multiple Responses)

Client sends one request, server streams multiple responses.

```python
with recorded_channel("test.yaml", "localhost:50051") as channel:
    stub = UserServiceStub(channel)
    for user in stub.ListUsers(ListUsersRequest(limit=10)):
        print(user.name)
```

grpcvcr records all streamed responses and replays them in order.

### Client Streaming (Multiple Requests, Single Response)

Client streams multiple requests, server sends one response.

```python
def request_iterator():
    for name in ["Alice", "Bob", "Charlie"]:
        yield CreateUserRequest(name=name)


with recorded_channel("test.yaml", "localhost:50051") as channel:
    stub = UserServiceStub(channel)
    response = stub.CreateUsers(request_iterator())
    print(f"Created {response.count} users")
```

grpcvcr records all streamed requests (concatenated) and the final response.

### Bidirectional Streaming (Multiple Requests, Multiple Responses)

Both client and server stream messages.

```python
def chat_messages():
    yield ChatMessage(text="Hello")
    yield ChatMessage(text="How are you?")


with recorded_channel("test.yaml", "localhost:50051") as channel:
    stub = ChatServiceStub(channel)
    for response in stub.Chat(chat_messages()):
        print(response.text)
```

grpcvcr records all request messages and all response messages.

## Cassette Format for Streaming

Streaming interactions store multiple messages:

```yaml
interactions:
  - request:
      method: /myservice.UserService/ListUsers
      body: "base64-request"
      metadata: {}
    response:
      messages:
        - "base64-response-1"
        - "base64-response-2"
        - "base64-response-3"
      code: OK
    rpc_type: server_streaming
```

## Matching Streaming Requests

For client streaming and bidirectional streaming, all request messages are concatenated for matching:

```python
from grpcvcr import MethodMatcher, RequestMatcher

# These will match if the concatenated request bodies are identical
matcher = MethodMatcher() & RequestMatcher()
```
