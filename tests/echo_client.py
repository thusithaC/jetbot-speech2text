import asyncio

async def tcp_echo_client():
    reader, writer = await asyncio.open_connection(
        '127.0.0.1', 9001)

    while True:
        data = await reader.read(1024*10)
        print(f'Received: {data.decode()!r}')


    print('Close the connection')
    writer.close()

asyncio.run(tcp_echo_client())