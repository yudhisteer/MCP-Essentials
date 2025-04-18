import asyncio
import base64
import os
import traceback

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import OpenAI

from src.shared.utils import debug_print


async def analyze_image(image_url: str, query: str = "What's in this image?") -> str:
    """
    Analyze an image using OpenAI's vision API.

    Args:
        image_url: URL of the image to analyze.
        prompt: Question or instruction for image analysis (e.g., "What is the color of the shirt?").

    Returns:
        str: Description of the image from the LLM.
    """
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        if not client.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        response = client.chat.completions.create(
            model="gpt-4o",  # Use the correct model name
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": query},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url,
                                "detail": "auto",
                            },
                        },
                    ],
                }
            ],
        )

        result = response.choices[0].message.content.strip()
        return result
    except Exception as e:
        print(f"Error analyzing image with OpenAI: {str(e)}")
        raise


async def main(query: str) -> None:
    """
    Main function to capture a webcam screenshot and analyze it based on a user query.

    Args:
        query: User's question about the image (e.g., "What is the color of the shirt?").
    """
    # Server parameters
    server_params = StdioServerParameters(
        command="python", args=["src\servers\opencv_server\server.py"], env=None
    )

    debug_print("Starting client, attempting to connect to server")
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # Call the take_screenshot Tool
                result = await session.call_tool(
                    "take_screenshot",
                    arguments={"output_filename": "captured_image.png"},
                )

                # Extract the PNG image from the result
                for content in result.content:
                    if content.type == "image":
                        img_data = content.data

                        # Convert image data to the appropriate format
                        if isinstance(img_data, str):
                            debug_print("Image data is already a base64 string")
                            base64_image = img_data
                            raw_image_data = base64.b64decode(img_data)
                        else:
                            debug_print("Encoding image data to base64")
                            base64_image = base64.b64encode(img_data).decode("utf-8")
                            raw_image_data = img_data

                        # Save image to disk for debugging
                        parent_dir = os.path.abspath(os.path.join(os.getcwd(), "../../.."))
                        output_dir = os.path.join(parent_dir, "output")
                        os.makedirs(output_dir, exist_ok=True)
                        debug_path = os.path.join(output_dir, "debug_screenshot.png")
                        try:
                            with open(debug_path, "wb") as f:
                                f.write(raw_image_data)
                            debug_print(f"Saved image to {debug_path}")
                        except Exception as e:
                            traceback.print_exc()
                            print(f"Error saving image: {str(e)}")

                        # Convert image data to a URL
                        image_url = f"data:image/png;base64,{base64_image}"

                        # Analyze the image with OpenAI
                        result = await analyze_image(image_url, query)
                        print(f"Image analysis result: {result}")

    except Exception as e:
        print(f"Failed to connect to server or process screenshot: {str(e)}")
        traceback.print_exc()


if __name__ == "__main__":
    # Example query
    query = "Describe the image in detail"
    asyncio.run(main(query))
