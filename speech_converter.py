import asyncio
from config import (
    logger,
    HOSTNAME,
    PORT
)
from speech2text.core_handler import listen_stream, get_output_queue


async def handle_client(reader, writer, out_q):

    while True:
        message = await out_q.get()
        logger.info(f"Send: {message}")

        data = message.encode()
        writer.write(data)
        await writer.drain()



async def main():
    out_q = get_output_queue()
    server = await asyncio.start_server(lambda r, w: handle_client(r, w, out_q), HOSTNAME, PORT)

    addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    logger.info(f'Serving on {addrs}')

    t1 = asyncio.create_task(listen_stream(out_q))
    await t1

    async with server:
        await server.serve_forever()
        


if __name__ == "__main__":
    
    asyncio.run(main())