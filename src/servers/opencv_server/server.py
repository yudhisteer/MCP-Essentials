import os
import traceback

import cv2
from mcp.server.fastmcp import FastMCP, Image

from src.shared.utils import debug_print

# Initialize the MCP server
mcp = FastMCP("WebcamScreenshotServer")


@mcp.tool()
def take_screenshot(
    output_filename="captured_image.png",
) -> Image:
    """Capture a single frame from a webcam and return it as a PNG image.

    Args:
        output_filename: Name of the file to save the captured image (default: captured_image.png)
    """
    try:
        # Initialize the camera
        cap = cv2.VideoCapture(0)

        # Check if the camera opened successfully
        if not cap.isOpened():
            raise ValueError(
                "Could not open camera. Ensure the webcam is connected and accessible."
            )

        # Capture a single frame
        ret, frame = cap.read()

        # Save the captured image
        parent_dir = os.path.abspath(os.path.join(os.getcwd(), "../../.."))
        output_dir = os.path.join(parent_dir, "output")
        os.makedirs(output_dir, exist_ok=True)  # Ensure output directory exists
        output_path = f"{output_dir}/{output_filename}"
        cv2.imwrite(
            output_path, frame, [cv2.IMWRITE_PNG_COMPRESSION, 9]
        )  # Save as PNG with maximum compression
        debug_print(f"Image saved as {output_path}")

        # Release the camera
        cap.release()

        # Check if the frame was captured successfully
        if not ret:
            raise ValueError("Failed to capture image from the webcam.")

        # Encode the frame as PNG
        _, buffer = cv2.imencode(".png", frame, [cv2.IMWRITE_PNG_COMPRESSION, 9])
        image_data = buffer.tobytes()

        # Return as MCP Image object with explicit PNG format
        return Image(data=image_data, format="png")
    except Exception as e:
        # Return error message if capture fails
        traceback.print_exc()
        raise ValueError(f"Failed to capture webcam screenshot: {str(e)}")


if __name__ == "__main__":
    mcp.run()
