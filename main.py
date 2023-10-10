import asyncio

import py_eureka_client.eureka_client as eureka_client
import strawberry
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from strawberry.asgi import GraphQL

from algorithms.models import Queries


@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "Hola, mundo!"


@strawberry.type
class Mutation:
    marching_squares: str = strawberry.field(resolver=Queries.marching_squares)
    binarization: str = strawberry.field(resolver=Queries.binarization)
    average_and_desviation: str = strawberry.field(resolver=Queries.average_and_deviation)


schema = strawberry.Schema(query=Query, mutation=Mutation)

graphql_app = GraphQL(schema)

app = FastAPI()
app.add_route("/graphql", graphql_app)
app.add_websocket_route("/graphql", graphql_app)

origins = [
    "http://localhost:4200",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_server_info():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]


async def main():
    ip = get_server_info()
    await eureka_client.init_async(eureka_server="http://localhost:8761",
                                   app_name="python-service",
                                   instance_port=8000,
                                   metadata={"microserviceType": "Procesamiento de Imágenes"},
                                   instance_host=ip
                                   )


@app.on_event("shutdown")
async def unregister_from_eureka():
    print("Shutting down....")
    try:
        await eureka_client.stop_async()
        print("Eureka client stopped successfully")
    except Exception as e:
        print(f"Error stopping Eureka client: {e}")


if __name__ == "__main__":
    asyncio.run(main())
    uvicorn.run(app, host='0.0.0.0', port=8000)
