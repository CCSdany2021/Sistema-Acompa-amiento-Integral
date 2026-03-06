import requests
from src.config import settings
from src import models

def get_external_students(course=None, section=None, grado=None):
    """
    Fetches students from the external Master DB API.
    """
    url = settings.API_ESTUDIANTES_URL
    headers = {
        "X-API-Key": settings.API_ESTUDIANTES_KEY
    }
    
    params = {"estado": "activo"}
    if course:
        params["curso"] = course
    if grado:
        params["grado"] = grado
    
    # Note: The external API might use different section names than our Enum.
    # We might need to map them if we filter by section on the API level.
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching from external API: {e}")
        return []

def map_external_section(ext_section):
    """
    Maps external section strings to local SectionEnum.
    """
    mapping = {
        "jardin_a_tercero": models.SectionEnum.PREESCOLAR_PRIMARIA,
        "preescolar": models.SectionEnum.PREESCOLAR_PRIMARIA,
        "primaria": models.SectionEnum.PREESCOLAR_PRIMARIA, 
        "basica_primaria": models.SectionEnum.PREESCOLAR_PRIMARIA, # Or MEDIA_BASKICA depending on grade, but matching name
        "basica_secundaria": models.SectionEnum.MEDIA_BASKICA,
        "cuarto_a_septimo": models.SectionEnum.MEDIA_BASKICA,
        "media_academica": models.SectionEnum.BACHILLERATO,
        "media_fortalecida": models.SectionEnum.BACHILLERATO,
        "bachillerato": models.SectionEnum.BACHILLERATO,
    }
    return mapping.get(ext_section.lower(), models.SectionEnum.BACHILLERATO)
