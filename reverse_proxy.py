import json

import httpx
from fastapi import FastAPI, Request
from starlette.responses import Response

app = FastAPI()

TARGET_URL = "http://openrouter.ai/api/v1"  # Target URL to forward the requests to


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def forward(request: Request, path: str):
    body = await request.body()

    # Log the request body, consider logging more information as needed
    body_str = body.decode("utf-8")
    body_str = json.loads(body_str) if body_str else {}
    print("Request Body String:", json.dumps(body_str, indent=4))

    # Prepare the request to forward
    method = request.method
    headers = dict(request.headers)
    auth_header = request.headers.get("Authorization")
    if auth_header:
        headers["Authorization"] = auth_header

    # Remove the host header since it will be replaced with the target URL's host
    headers.pop("host", None)
    headers["host"] = "openrouter.ai"

    async with httpx.AsyncClient() as client:
        # Forward the request to the target URL
        target_url = f"{TARGET_URL}/{path}"
        print(f"Forwarding {method} request to {target_url}")
        response = await client.request(
            method, target_url, content=body, headers=headers
        )

        # Return the response received from the target URL
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
