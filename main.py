import asyncio

import py_eureka_client.eureka_client as eureka_client
import strawberry
import uvicorn
from fastapi import FastAPI
from strawberry.asgi import GraphQL
from algorithms.models import Queries, URL, PolyData, AverageOutput
import os

app_name = 'models-python'


@strawberry.type
class Query:
    """This class represents the Query type for the GraphQL schema and is in charge of handling all the fields defined in it, which in this case are the image processing algorithms.
    """
    marching_squares: PolyData = strawberry.field(resolver=Queries.marching_squares, description="Algoritmo de marching squares")
    binarization: URL = strawberry.field(resolver=Queries.binarization, description="Algoritmo de binarization")
    average_and_deviation: AverageOutput = strawberry.field(resolver=Queries.average_and_deviation,
                                                            description="Algoritmo de media y desviación estándar")


schema = strawberry.Schema(query=Query)

graphql_app = GraphQL(schema)

app = FastAPI()
app.add_route("/graphql", graphql_app)
app.add_websocket_route("/graphql", graphql_app)


def get_server_info() -> str:
    """This function determines and provides the IP address of the application's local server.

    Returns:
        str: IP address of the application's local server
    """
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]


async def main():
    """
    This function is responsible for preparing and registering an instance of the application on a registration and discovery server called Spring Cloud Eureka. 
    This allows other applications to dynamically find and communicate with this application through the Eureka server. 
    Additional metadata, such as the microservice type, can help categorize and describe the application registered with the server.
    """
    ip = get_server_info()
    await eureka_client.init_async(eureka_server=os.environ.get("EUREKA_URL"),
                                   app_name=app_name,
                                   instance_port=8000,
                                   metadata={"microservice-type": "IA-MODEL"},
                                   instance_host=ip
                                   )


@app.on_event("shutdown")
async def unregister_from_eureka():
    """
    This function is responsible for performing unregistration and shutdown actions related to a Eureka client when the application is shutting down.
    """
    print("Shutting down....")
    try:
        await eureka_client.stop_async()
        print("Eureka client stopped successfully")
    except Exception as e:
        print(f"Error stopping Eureka client: {e}")


if __name__ == "__main__":
    asyncio.run(main())
    uvicorn.run(app, host='0.0.0.0', port=8000)
