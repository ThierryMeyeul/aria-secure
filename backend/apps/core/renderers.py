"""
Renderers personnalisés pour l'API REST d'ARIA Secure.
"""

from rest_framework import renderers
from rest_framework.utils import json
from rest_framework.renderers import JSONRenderer


class CustomJSONRenderer(JSONRenderer):
    """
    Renderer JSON personnalisé qui enveloppe toutes les réponses
    dans un format standardisé.
    """
    
    charset = 'utf-8'
    
    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Formate la réponse JSON avec une structure standard.
        """
        response = renderer_context.get('response')
        
        if response is None:
            return super().render(data, accepted_media_type, renderer_context)
        
        status_code = response.status_code
        
        if status_code >= 400:
            response_data = {
                'success': False,
                'error': data if isinstance(data, (str, dict)) else str(data),
                'status_code': status_code
            }
        else:
            if data is None:
                response_data = {
                    'success': True,
                    'data': None,
                    'status_code': status_code
                }
            elif isinstance(data, dict) and 'success' in data:
                response_data = data
                response_data['status_code'] = status_code
            else:
                response_data = {
                    'success': True,
                    'data': data,
                    'status_code': status_code
                }
        
        return super().render(response_data, accepted_media_type, renderer_context)


class PlainTextRenderer(renderers.BaseRenderer):
    """
    Renderer pour les réponses en texte brut.
    """
    
    media_type = 'text/plain'
    format = 'txt'
    charset = 'utf-8'
    
    def render(self, data, accepted_media_type=None, renderer_context=None):
        if isinstance(data, str):
            return data.encode(self.charset)
        return str(data).encode(self.charset)


class JPEGRenderer(renderers.BaseRenderer):
    """
    Renderer pour les images JPEG.
    """
    
    media_type = 'image/jpeg'
    format = 'jpg'
    charset = None
    render_style = 'binary'
    
    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data


class PNGRenderer(renderers.BaseRenderer):
    """
    Renderer pour les images PNG.
    """
    
    media_type = 'image/png'
    format = 'png'
    charset = None
    render_style = 'binary'
    
    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data


class PDFRenderer(renderers.BaseRenderer):
    """
    Renderer pour les fichiers PDF.
    """
    
    media_type = 'application/pdf'
    format = 'pdf'
    charset = None
    render_style = 'binary'
    
    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data