import io
import json
import os

import httpx
import numpy as np
import pydicom
import strawberry
from PIL import Image
from skimage import measure
from strawberry.file_uploads import Upload


@strawberry.input(description="Tipo para algoritmo de binarización")
class BinarizationInput:
    """
    Threshold: binarization threshold
    """ 
    threshold: int = strawberry.field(description="Threshold: Umbral de binarización")
    """
    File: Image file to be processed
    """ 
    file: Upload = strawberry.field(description="File: Archivo de la imagen")



@strawberry.input(description="Tipo para el algoritmo de Marching Squares")
class MarchingInput:
    """
    Level: Threshold level to identify image contours
    """ 
    level: float = strawberry.field(description="Level: Nivel de umbral para identificar los contornos. Rango: [0,1]")
    """
    Fully_connected: Controls the connectivity of pixels on the contour
    """ 
    fully_connected: str = strawberry.field(
        description="Fully_connected: Controla la conectividad de los píxeles en el contorno. Valores: [high,low]")
    """
    Positive_orientation: Orientation of pixels on the contour
    """ 
    positive_orientation: str = strawberry.field(
        description="Positive_orientation: Controla la orientación de los píxeles en el contorno. Valores: [high,low]")
    """
    File: Image file to be processed
    """ 
    file: Upload = strawberry.field(description="File: Archivo de la imagen")


@strawberry.input(description="Tipo para el algoritmo de media y desviación estándar")
class AverageInput:
    """
    File: Image file to be processed
    """ 
    file: Upload = strawberry.field(description="File: Archivo de la imagen")


@strawberry.type
class URL:
    """
    Url: Link to the processed image
    """ 
    url: str = strawberry.field(description="Url: Enlace de la imagen procesada")


@strawberry.type
class PolyData:
    """
    Points: Points and connections representing image contours
    """ 
    points: str = strawberry.field(description="Points: Puntos de los contornos de la imagen")


@strawberry.type
class AverageOutput:
    """
    Media: Average of the image pixels
    """ 
    media: str = strawberry.field(description="Media: Promedio de los pixeles de la imagen")
    """
    Deviation: Standard deviation of image pixels
    """ 
    deviation: str = strawberry.field(description="Deviation: Desviación estándar de los pixeles de la imagen")

    
class Queries:
    """
    This class is responsible for handling all image processing algorithms, each in independent functions.
    """
    
    async def binarization(self, inpt: BinarizationInput) -> URL:
        """Function that executes the binarization algorithm on an image

        Args:
            inpt (BinarizationInput): Input type for the binarization algorithm defined for the GraphQL scheme

        Returns:
            URL: Output type defined when the response is an url for GraphQL schema
        """
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

    async def marching_squares(self, inpt: MarchingInput) -> PolyData:
        """Function that executes the marching squares algorithm on an image

        Args:
            inpt (MarchingInput): Input type for the marching squares algorithm defined for the GraphQL scheme

        Returns:
            PolyData: Output type defined when the response is a list of points and connections called polydata for GraphQL schema
        """
        image = await inpt.file.read()
        ds = pydicom.dcmread(io.BytesIO(image))
        image = ds.pixel_array

        contours = measure.find_contours(image, inpt.level, inpt.fully_connected, inpt.positive_orientation)

        contours_np = [cont.astype(int) for cont in contours]
        serialized_contours = json.dumps([cont.tolist() for cont in contours_np])

        response = PolyData(points=serialized_contours)

        return response

    async def average_and_deviation(self, inpt: AverageInput) -> AverageOutput:
        """Function that executes the average and deviation algorithm on an image

        Args:
            inpt (AverageInput): Input type for the average and deviation algorithm defined for the GraphQL scheme

        Returns:
            AverageOutput: Output type defined when the response is two strings representing the mean and standard deviation for GraphQL schema
        """
        image = await inpt.file.read()
        ds = pydicom.dcmread(io.BytesIO(image))
        image = ds.pixel_array

        media = np.mean(image)
        deviation = np.std(image)

        response = AverageOutput(media=media, deviation=deviation)

        return response
