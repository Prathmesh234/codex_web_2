import asyncio
import platform

# Set the correct event loop policy for Windows
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",              # module:app
        host="0.0.0.0",
        port=8000
    )