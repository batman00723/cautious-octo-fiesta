from ninja_extra import api_controller, route

@api_controller('/health', tags=['Health Check'])
class HealthController:
    
    @route.get('/ping')
    def ping(self):
        """Simple health check endpoint to keep instances alive."""
        return {"status": "pong"}
