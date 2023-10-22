import io
import json
from typing import Annotated
import httpx
import os

import numpy as np
import pydicom
import strawberry
from PIL import Image
from skimage import measure
from strawberry.file_uploads import Upload


@strawberry.input(description="Tipo para algoritmo de binarización")
class BinarizationInput:
    threshold: int = strawberry.field(description="Threshold: Umbral de binarización")
    file: Upload = strawberry.field(description="File: Archivo de la imagen")


@strawberry.input(description="Tipo para el algoritmo de Marching Squares")
class MarchingInput:
    file: Upload = strawberry.field(description="File: Archivo de la imagen")


@strawberry.input(description="Tipo para el algoritmo de media y desviación estándar")
class AverageInput:
    file: Upload = strawberry.field(description="File: Archivo de la imagen")


@strawberry.type
class URL:
    url: str = strawberry.field(description="Url: Enlace de la imagen procesada")


@strawberry.type
class PolyData:
    points: str = strawberry.field(description="Points: Puntos de los contornos de la imagen")


@strawberry.type
class AverageOutput:
    media: str = strawberry.field(description="Media: Promedio de los pixeles de la imagen")
    deviation: str = strawberry.field(description="Deviation: Desviación estándar de los pixeles de la imagen")


class Queries:

    async def binarization(self, inpt: BinarizationInput) -> URL:
        image = await inpt.file.read()
        dicom_dataset = pydicom.dcmread(io.BytesIO(image))

        pixel_array = dicom_dataset.pixel_array

        binarized_array = pixel_array > inpt.threshold

        binarized_image = Image.fromarray((binarized_array * 255).astype(np.uint8))

        image_stream = io.BytesIO()
        binarized_image.save(image_stream, format="PNG")
        image_data = image_stream.getvalue()

        url = os.environ.get("FILES_URL")

        async with httpx.AsyncClient() as client:
            files = {'file': ('image.png', image_data, 'image/png')}
            response = await client.post(url, files=files)

        if response.status_code == 200:
            response_data = response.read().decode('utf-8')

        else:
            response_data = {"error": "Hubo un problema con la solicitud POST al manejador de archivos"}

        r = URL(url=response_data)
        return r

    async def marching_squares(self, inpt: Annotated[MarchingInput, strawberry.argument(
        description="Input to xtract contours from a DICOM image using Marching Squares.")]) -> PolyData:
        image = await inpt.file.read()
        ds = pydicom.dcmread(io.BytesIO(image))
        image = ds.pixel_array

        contours = measure.find_contours(image, 0.1, 'high')

        contours_np = [cont.astype(int) for cont in contours]
        serialized_contours = json.dumps([cont.tolist() for cont in contours_np])

        response = PolyData(points=serialized_contours)

        return response

    async def average_and_deviation(self, inpt: Annotated[AverageInput, strawberry.argument(
        description="Input to calculate average and deviation of pixel values in a DICOM image.")]) -> AverageOutput:
        print(inpt.file)
        image = await inpt.file.read()
        ds = pydicom.dcmread(io.BytesIO(image))
        image = ds.pixel_array

        media = np.mean(image)
        deviation = np.std(image)

        response = AverageOutput(media=media, deviation=deviation)

        return response
