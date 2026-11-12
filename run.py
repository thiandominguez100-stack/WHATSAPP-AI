from backend.app import create_app

app = create_app()

if __name__ == "__main__":
    import os

    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "5000"))
    # Keep the development server bound to localhost by default.
    app.run(host=host, port=port, debug=False)
