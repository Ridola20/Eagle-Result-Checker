from app import app

# Vercel requires this for serverless functions
def handler(request, response):
    return app(request, response)