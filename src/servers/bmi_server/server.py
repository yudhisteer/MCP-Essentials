from typing import Dict, Any
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP

class BMIResponse(BaseModel):
    """Response model for BMI calculation."""
    bmi: float = Field(..., description="Calculated BMI value", ge=0)
    category: str = Field(..., description="BMI category (Underweight, Normal, Overweight, Obese)")

# Initialize MCP server
mcp = FastMCP("BMI Calculator")

@mcp.tool()
def calculate_bmi(weight_kg: float = Field(..., description="Weight in kilograms", gt=0),
                 height_cm: float = Field(..., description="Height in centimeters", gt=0)) -> BMIResponse:
    """Calculate BMI given weight in kg and height in centimeters.
    
    Args:
        weight_kg: Weight in kilograms
        height_cm: Height in centimeters
        
    Returns:
        BMIResponse containing:
            - bmi: Calculated BMI value
            - category: BMI category (Underweight, Normal, Overweight, Obese)
    """
    # Convert height from cm to m
    height_m = height_cm / 100
    
    # Calculate BMI
    bmi = weight_kg / (height_m ** 2)
    
    # Determine BMI category
    if bmi < 18.5:
        category = "Underweight"
    elif bmi < 25:
        category = "Normal"
    elif bmi < 30:
        category = "Overweight"
    else:
        category = "Obese"
    
    return BMIResponse(
        bmi=round(bmi, 2),
        category=category
    )

if __name__ == "__main__":
    mcp.run()
