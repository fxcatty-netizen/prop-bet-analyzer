import anthropic
import base64
from typing import List, Optional, Dict
import json
import re
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class ClaudeOCRService:
    """Service for using Claude to extract prop bets from bet slip images."""
    
    def __init__(self):
        # Note: Add ANTHROPIC_API_KEY to your .env file
        self.client = anthropic.Anthropic(
            api_key=getattr(settings, 'ANTHROPIC_API_KEY', None)
        )
    
    async def extract_props_from_image(self, image_data: bytes, mime_type: str) -> List[Dict]:
        """
        Extract prop bets from a bet slip image using Claude's vision capabilities.
        
        Args:
            image_data: Image bytes
            mime_type: Image MIME type (e.g., 'image/jpeg')
            
        Returns:
            List of prop bet dictionaries
        """
        try:
            # Convert image to base64
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            # Create the prompt for Claude
            prompt = self._create_extraction_prompt()
            
            # Call Claude API with vision
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": mime_type,
                                    "data": base64_image
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )
            
            # Extract the response text
            response_text = message.content[0].text
            
            # Parse the JSON response
            props = self._parse_claude_response(response_text)
            
            logger.info(f"Successfully extracted {len(props)} props from image")
            return props
            
        except Exception as e:
            logger.error(f"Failed to extract props from image: {e}")
            raise
    
    def _create_extraction_prompt(self) -> str:
        """Create the prompt for Claude to extract prop bets."""
        return """Analyze this sports betting slip image and extract all the prop bets. 

For each prop bet you find, extract:
1. Player name (full name)
2. Stat type (points, rebounds, assists, threes, steals, blocks, etc.)
3. Line value (the number threshold)
4. Over/Under
5. Opponent team (if visible)

Return the data as a JSON array with this exact format:
```json
[
  {
    "player_name": "Anthony Black",
    "stat_type": "points",
    "line": 15.5,
    "over_under": "over",
    "opponent_name": "Cleveland Cavaliers"
  }
]
```

Important:
- For stat_type, use lowercase: points, rebounds, assists, threes, steals, blocks
- For over_under, use lowercase: "over" or "under"
- If opponent is not visible, omit the opponent_name field
- Line should be a number (float or int)
- Only include the JSON array, no other text

Extract all props you can find in the image."""
    
    def _parse_claude_response(self, response_text: str) -> List[Dict]:
        """Parse Claude's response to extract prop bet data."""
        try:
            # Remove markdown code blocks if present
            cleaned_text = response_text.strip()
            if '```json' in cleaned_text:
                # Extract JSON from code block
                match = re.search(r'```json\s*(.*?)\s*```', cleaned_text, re.DOTALL)
                if match:
                    cleaned_text = match.group(1)
            elif '```' in cleaned_text:
                # Remove generic code blocks
                cleaned_text = re.sub(r'```.*?```', '', cleaned_text, flags=re.DOTALL)
            
            # Parse JSON
            props_data = json.loads(cleaned_text.strip())
            
            # Validate and clean each prop
            validated_props = []
            for prop in props_data:
                if self._validate_prop(prop):
                    validated_props.append(self._clean_prop(prop))
            
            return validated_props
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Claude response: {e}")
            logger.error(f"Response text: {response_text}")
            return []
    
    def _validate_prop(self, prop: Dict) -> bool:
        """Validate that a prop has required fields."""
        required_fields = ['player_name', 'stat_type', 'line', 'over_under']
        return all(field in prop for field in required_fields)
    
    def _clean_prop(self, prop: Dict) -> Dict:
        """Clean and normalize prop data."""
        cleaned = {
            'player_name': str(prop['player_name']).strip(),
            'stat_type': str(prop['stat_type']).lower().strip(),
            'line': float(prop['line']),
            'over_under': str(prop['over_under']).lower().strip()
        }
        
        # Add optional fields
        if 'opponent_name' in prop:
            cleaned['opponent_name'] = str(prop['opponent_name']).strip()
        
        if 'odds' in prop:
            try:
                cleaned['odds'] = int(prop['odds'])
            except (ValueError, TypeError):
                pass
        
        return cleaned


# Global instance
claude_ocr_service = ClaudeOCRService()
