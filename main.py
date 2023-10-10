import asyncio
from tokenize import String
from typing import List

import py_eureka_client.eureka_client as eureka_client
import strawberry
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from strawberry.asgi import GraphQL

from algorithms.models import Queries

campos = [
    '<div class="campo"><label for="direccion">Dirección</label><input type="text" id="direccion" name="direccion"></div>',
    '<div class="campo"><label for="ciudad">Ciudad</label><input type="text" id="ciudad" name="ciudad"></div>',
    '<div class="campo"><label for="codigo_postal">Código Postal</label><input type="text" id="codigo_postal" name="codigo_postal"></div>',
    '<div class="campo"><label for="fecha_nacimiento">Fecha de Nacimiento</label><input type="date" id="fecha_nacimiento" name="fecha_nacimiento"></div>',
    '<div class="campo"><label>Género</label><input type="radio" id="masculino" name="genero" value="Masculino"><label for="masculino">Masculino</label><input type="radio" id="femenino" name="genero" value="Femenino"><label for="femenino">Femenino</label><input type="radio" id="otro" name="genero" value="Otro"><label for="otro">Otro</label></div>',
    '<div class="campo"><label>Intereses</label><input type="checkbox" id="deportes" name="intereses" value="Deportes"><label for="deportes">Deportes</label><input type="checkbox" id="musica" name="intereses" value="Música"><label for="musica">Música</label><input type="checkbox" id="cine" name="intereses" value="Cine"><label for="cine">Cine</label></div>',
    '<div class="campo"><label for="comentarios">Comentarios</label><textarea id="comentarios" name="comentarios"></textarea></div>',
    '<div class="campo"><label for="opciones">Opciones</label><select id="opciones" name="opciones"><option value="Opción 1">Opción 1</option><option value="Opción 2">Opción 2</option><option value="Opción 3">Opción 3</option></select></div>'
]

@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "Hola, mundo!"

    @strawberry.field
    def campos(self) -> List[str]:
        return campos

#[{"html": campo} for campo in campos]

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
