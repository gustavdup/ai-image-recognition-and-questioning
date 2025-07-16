# Question Generation Module for Educational Flashcards
import json
import httpx
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

class Question(BaseModel):
    text: str
    type: str  # "multiple_choice", "true_false", "identification", "counting", "spatial"
    correct_answer: str
    options: Optional[List[str]] = None
    difficulty: str
    category: str
    explanation: Optional[str] = None

class QuestionSet(BaseModel):
    image_id: str | List[str]  # Can be single image ID or list of image IDs
    questions: List[Question]
    total_questions: int
    difficulty_level: str
    generated_at: str
    is_multi_image: bool = False
    source_images_count: int = 1

class QuestionGenerator:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OpenAI API key not found in environment variables")
    
    async def generate_questions(
        self, 
        image_data: Dict[str, Any] | List[Dict[str, Any]], 
        difficulty_level: str = "elementary",
        num_questions: int = 5,
        question_types: Optional[List[str]] = None,
        block_assignments: Optional[Dict[str, str]] = None
    ) -> QuestionSet:
        """
        Generate educational questions from image analysis data
        
        Args:
            image_data: Single image data dict OR list of image data dicts for multi-image questions
            difficulty_level: "preschool", "elementary", "middle", "high"
            num_questions: Number of questions to generate
            question_types: Specific types to generate or None for mixed
            block_assignments: Map of image_id to block letter (A, B, C, etc.) for multi-image questions
        """
        
        # Determine if this is multi-image generation
        is_multi_image = isinstance(image_data, list)
        
        if is_multi_image:
            return await self._generate_multi_image_questions(
                image_data, difficulty_level, num_questions, question_types, block_assignments
            )
        else:
            return await self._generate_single_image_questions(
                image_data, difficulty_level, num_questions, question_types
            )
    
    async def _generate_single_image_questions(
        self, 
        image_data: Dict[str, Any], 
        difficulty_level: str = "elementary",
        num_questions: int = 5,
        question_types: Optional[List[str]] = None
    ) -> QuestionSet:
        """
        Generate educational questions from image analysis data
        
        Args:
            image_data: The parsed image analysis from your Edge Function
            difficulty_level: "preschool", "elementary", "middle", "high"
            num_questions: Number of questions to generate
            question_types: Specific types to generate or None for mixed
        """
        
        if question_types is None:
            question_types = ["identification", "counting", "spatial", "true_false", "multiple_choice"]
        
        # Extract relevant data from your image analysis
        print(f"🔍 Processing image data: {type(image_data)}")
        print(f"🔍 Image data keys: {list(image_data.keys()) if isinstance(image_data, dict) else 'Not a dict'}")
        
        tags = image_data.get('tags', {}) if isinstance(image_data, dict) else {}
        description = image_data.get('description', '') if isinstance(image_data, dict) else ''
        confidence = image_data.get('confidence', 0.8) if isinstance(image_data, dict) else 0.8
        
        print(f"🏷️ Tags extracted: {type(tags)}, content: {str(tags)[:200]}...")
        print(f"📝 Description: {description[:100]}...")
        
        # Build context for question generation
        try:
            context = self._build_question_context(tags, description)
            print(f"✅ Context built successfully: {len(context)} keys")
        except Exception as context_error:
            print(f"❌ Error building context: {context_error}")
            raise Exception(f"Failed to build question context: {str(context_error)}")
        
        # Generate questions using OpenAI
        try:
            prompt = self._create_question_prompt(context, difficulty_level, num_questions, question_types)
            print(f"✅ Prompt created successfully: {len(prompt)} characters")
        except Exception as prompt_error:
            print(f"❌ Error creating prompt: {prompt_error}")
            raise Exception(f"Failed to create question prompt: {str(prompt_error)}")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "gpt-4o-mini",
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are an expert educational content creator specializing in visual learning materials for children."
                            },
                            {
                                "role": "user", 
                                "content": prompt
                            }
                        ],
                        "max_tokens": 1500,
                        "temperature": 0.7
                    },
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    raise Exception(f"OpenAI API error: {response.status_code} - {response.text}")
                
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                # Parse the generated questions
                questions_data = self._parse_questions_response(content)
                
                return QuestionSet(
                    image_id=image_data.get('id', 'unknown'),
                    questions=questions_data,
                    total_questions=len(questions_data),
                    difficulty_level=difficulty_level,
                    generated_at=str(datetime.utcnow()),
                    is_multi_image=False,
                    source_images_count=1
                )
                
        except Exception as e:
            print(f"Error generating questions: {e}")
            # Return fallback questions based on available data
            return self._generate_fallback_questions(image_data, difficulty_level)
    
    async def _generate_multi_image_questions(
        self, 
        images_data: List[Dict[str, Any]], 
        difficulty_level: str = "elementary",
        num_questions: int = 5,
        question_types: Optional[List[str]] = None,
        block_assignments: Optional[Dict[str, str]] = None
    ) -> QuestionSet:
        """
        Generate educational questions comparing/analyzing multiple images
        
        Args:
            images_data: List of image analysis data from your Edge Function
            difficulty_level: "preschool", "elementary", "middle", "high"
            num_questions: Number of questions to generate
            question_types: Specific types to generate or None for mixed
            block_assignments: Map of image_id to block letter (A, B, C, etc.)
        """
        
        if question_types is None:
            question_types = ["identification", "counting", "spatial", "true_false", "multiple_choice", "comparison", "block_identification"]
        
        # Build aggregated context from all images
        multi_context = self._build_multi_image_context(images_data, block_assignments)
        
        # Generate questions using OpenAI with multi-image context
        prompt = self._create_multi_image_prompt(multi_context, difficulty_level, num_questions, question_types)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "gpt-4o-mini",
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are an expert educational content creator specializing in visual learning materials for children. You excel at creating comparative questions across multiple images."
                            },
                            {
                                "role": "user", 
                                "content": prompt
                            }
                        ],
                        "max_tokens": 2000,  # More tokens for multi-image analysis
                        "temperature": 0.7
                    },
                    timeout=45.0
                )
                
                if response.status_code != 200:
                    raise Exception(f"OpenAI API error: {response.status_code} - {response.text}")
                
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                # Parse the generated questions
                questions_data = self._parse_questions_response(content)
                
                # Get image IDs
                image_ids = [img.get('id', 'unknown') for img in images_data]
                
                return QuestionSet(
                    image_id=image_ids,
                    questions=questions_data,
                    total_questions=len(questions_data),
                    difficulty_level=difficulty_level,
                    generated_at=str(datetime.utcnow()),
                    is_multi_image=True,
                    source_images_count=len(images_data)
                )
                
        except Exception as e:
            print(f"Error generating multi-image questions: {e}")
            # Return fallback questions based on available data
            return self._generate_multi_image_fallback_questions(images_data, difficulty_level)
    
    def _build_question_context(self, tags: Dict, description: str) -> Dict[str, Any]:
        """Extract key elements for question generation"""
        # Handle both old flat structure and new nested structure
        
        print(f"🔧 Building context from tags: {type(tags)}")
        if not isinstance(tags, dict):
            print(f"⚠️ Tags is not a dict, using empty dict instead. Got: {type(tags)}")
            tags = {}
        
        if not isinstance(description, str):
            print(f"⚠️ Description is not a string, converting. Got: {type(description)}")
            description = str(description) if description is not None else ''
        
        # Try to extract from current flat structure (as used in Edge Function)
        try:
            context = {
                "description": description,
                "colors": tags.get('colors', []) or [],
                "shapes": tags.get('shapes', []) or [],
                "letters": tags.get('letters', []) or [],
                "numbers": tags.get('numbers', []) or [],
                "words": tags.get('words', []) or [],
                "objects": tags.get('objects', []) or [],
                "people": tags.get('people', []) or [],
                "animals": tags.get('animals', []) or [],
                "shape_colors": tags.get('shapeColors', []) or [],
                "shape_contents": tags.get('shapeContents', []) or [],
                "nested_elements": tags.get('nestedElements', []) or [],
                "text_color": tags.get('textColor', '') or '',
                "text_vs_semantic_mismatch": tags.get('textVsSemanticMismatch', '') or '',
                "text_location": tags.get('textLocation', '') or '',
                "object_colors": tags.get('objectColors', []) or [],
                "object_positions": tags.get('objectPositions', []) or [],
                "items_inside_shapes": tags.get('itemsInsideShapes', []) or [],
                "overlapping_items": tags.get('overlappingItems', []) or [],
                "relative_positions": tags.get('relativePositions', []) or [],
                "color_word_mismatches": tags.get('colorWordMismatches', []) or [],
                "highlighted_elements": tags.get('highlightedElements', []) or [],
                "background_color": tags.get('backgroundColor', 'white') or 'white',
                "has_colored_background": tags.get('hasColoredBackground', 'false') or 'false',
                "total_items": tags.get('totalItems', '0') or '0',
                "letter_count": tags.get('letterCount', '0') or '0',
                "number_count": tags.get('numberCount', '0') or '0',
                "object_count": tags.get('objectCount', '0') or '0',
                "shape_count": tags.get('shapeCount', '0') or '0',
                "category": tags.get('category', 'mixed') or 'mixed',
                "question_types": tags.get('questionTypes', []) or []
            }
            print(f"✅ Context built with {len(context)} fields")
            return context
        except Exception as e:
            print(f"❌ Error building context: {e}")
            # Return a safe fallback context
            return {
                "description": description,
                "colors": [], "shapes": [], "letters": [], "numbers": [], "words": [],
                "objects": [], "people": [], "animals": [], "shape_colors": [],
                "shape_contents": [], "nested_elements": [], "text_color": "",
                "text_vs_semantic_mismatch": "", "text_location": "", "object_colors": [],
                "object_positions": [], "items_inside_shapes": [], "overlapping_items": [],
                "relative_positions": [], "color_word_mismatches": [], "highlighted_elements": [],
                "background_color": "white", "has_colored_background": "false",
                "total_items": "0", "letter_count": "0", "number_count": "0",
                "object_count": "0", "shape_count": "0", "category": "mixed", "question_types": []
            }
    
    def _get_empty_multi_context(self) -> Dict[str, Any]:
        """Return empty multi-image context when processing fails"""
        return {
            "all_colors": [],
            "all_shapes": [], 
            "all_letters": [],
            "all_numbers": [],
            "all_objects": [],
            "all_categories": [],
            "color_counts": {},
            "shape_counts": {},
            "category_counts": {},
            "images_with_colors": {},
            "images_with_shapes": {},
            "images_with_letters": {},
            "images_with_numbers": {},
            "descriptions": [],
            "image_summaries": [],
            "num_images": 0
        }

    def _build_multi_image_context(self, images_data: List[Dict[str, Any]], block_assignments: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Build aggregated context from multiple images for comparative questions"""
        
        print(f"🔧 Building multi-image context from {len(images_data)} images")
        
        try:
            # Validate input
            if not images_data or not isinstance(images_data, list):
                print(f"⚠️ Invalid images_data: {type(images_data)}")
                return self._get_empty_multi_context()
            
            # Aggregate data across all images
            all_colors = set()
            all_shapes = set()
            all_letters = set()
            all_numbers = set()
            all_objects = set()
            all_categories = set()
            
            # Count occurrences for comparative questions
            color_counts = {}
            shape_counts = {}
            category_counts = {}
            
            # Track which images have what elements
            images_with_colors = {}
            images_with_shapes = {}
            images_with_letters = {}
            images_with_numbers = {}
            
            descriptions = []
            image_summaries = []
            
            for i, image_data in enumerate(images_data):
                try:
                    if not isinstance(image_data, dict):
                        print(f"⚠️ Image {i} is not a dict: {type(image_data)}")
                        continue
                        
                    tags = image_data.get('tags', {}) or {}
                    description = image_data.get('description', '') or ''
                    descriptions.append(description)
                    
                    print(f"📝 Processing image {i+1}: {description[:50]}...")
                    
                    # Extract elements for this image with safe access
                    colors = tags.get('colors', []) or []
                    shapes = tags.get('shapes', []) or []
                    letters = tags.get('letters', []) or []
                    numbers = tags.get('numbers', []) or []
                    objects = tags.get('objects', []) or []
                    category = tags.get('category', 'mixed') or 'mixed'
                    
                    # Ensure they're lists
                    if not isinstance(colors, list): colors = []
                    if not isinstance(shapes, list): shapes = []
                    if not isinstance(letters, list): letters = []
                    if not isinstance(numbers, list): numbers = []
                    if not isinstance(objects, list): objects = []
                    
                    # Add to aggregated sets
                    all_colors.update(colors)
                    all_shapes.update(shapes)
                    all_letters.update(letters)
                    all_numbers.update(numbers)
                    all_objects.update(objects)
                    all_categories.add(category)
                    
                    # Count occurrences across images
                    for color in colors:
                        color_counts[color] = color_counts.get(color, 0) + 1
                        if color not in images_with_colors:
                            images_with_colors[color] = []
                        images_with_colors[color].append(i + 1)
                    
                    for shape in shapes:
                        shape_counts[shape] = shape_counts.get(shape, 0) + 1
                        if shape not in images_with_shapes:
                            images_with_shapes[shape] = []
                        images_with_shapes[shape].append(i + 1)
                    
                    for letter in letters:
                        if letter not in images_with_letters:
                            images_with_letters[letter] = []
                        images_with_letters[letter].append(i + 1)
                    
                    for number in numbers:
                        if number not in images_with_numbers:
                            images_with_numbers[number] = []
                        images_with_numbers[number].append(i + 1)
                    
                    category_counts[category] = category_counts.get(category, 0) + 1
                    
                    # Get block assignment if available
                    image_id = image_data.get('id', f'unknown_{i}')
                    if block_assignments:
                        block_letter = block_assignments.get(image_id, f'{chr(65+i)}')
                    else:
                        block_letter = f'{chr(65+i)}'
                    
                    # Create summary for this image
                    image_summaries.append({
                        "image_number": i + 1,
                        "block_letter": block_letter,
                        "image_id": image_id,
                        "description": description[:100] + "..." if len(description) > 100 else description,
                        "colors": colors[:5],
                        "shapes": shapes[:5],
                        "letters": letters[:10],
                        "numbers": numbers[:10],
                        "category": category
                    })
                    
                except Exception as e:
                    print(f"⚠️ Error processing image {i}: {e}")
                    continue
                    
        except Exception as e:
            print(f"❌ Error building multi-image context: {e}")
            return self._get_empty_multi_context()
            
        # Build the final context
        try:
            context = {
                "all_colors": sorted(list(all_colors)),
                "all_shapes": sorted(list(all_shapes)),
                "all_letters": sorted(list(all_letters)),
                "all_numbers": sorted(list(all_numbers)),
                "all_objects": sorted(list(all_objects)),
                "all_categories": sorted(list(all_categories)),
                "color_counts": color_counts,
                "shape_counts": shape_counts,
                "category_counts": category_counts,
                "images_with_colors": images_with_colors,
                "images_with_shapes": images_with_shapes,
                "images_with_letters": images_with_letters,
                "images_with_numbers": images_with_numbers,
                "descriptions": descriptions,
                "image_summaries": image_summaries,
                "num_images": len(images_data)
            }
            
            print(f"✅ Built context: {len(all_colors)} colors, {len(all_shapes)} shapes, {len(all_letters)} letters")
            return context
            
        except Exception as e:
            print(f"❌ Error finalizing multi-image context: {e}")
            return self._get_empty_multi_context()

    def _create_question_prompt(self, context: Dict, difficulty: str, num_questions: int, types: List[str]) -> str:
        """Create the prompt for question generation"""
        
        # Safe access to context fields
        def safe_join(items, limit=5):
            if isinstance(items, list) and items:
                return ', '.join(str(item) for item in items[:limit])
            return 'none'
        
        def safe_get(key, default='none'):
            return str(context.get(key, default)) if context.get(key) else default
        
        return f"""Generate {num_questions} educational questions based on this flashcard image analysis:

CONTEXT:
- Description: {safe_get('description', 'No description available')}
- Colors present: {safe_join(context.get('colors', []))}
- Shapes present: {safe_join(context.get('shapes', []))}
- Letters: {safe_join(context.get('letters', []), 10)}
- Numbers: {safe_join(context.get('numbers', []), 10)}
- Objects: {safe_join(context.get('objects', []))}
- Total items: {safe_get('total_items', '0')}
- Category: {safe_get('category', 'mixed')}
- Shape-color combinations: {safe_join(context.get('shape_colors', []), 3)}
- Items inside shapes: {safe_join(context.get('shape_contents', []), 3)}
- Spatial relationships: {safe_join(context.get('relative_positions', []), 3)}
- Color-word mismatches: {safe_join(context.get('color_word_mismatches', []), 3)}

CRITICAL REQUIREMENTS FOR SMART QUESTIONS:
- Difficulty level: {difficulty}
- Question types to include: {', '.join(types)}
- Make questions specific to what's actually in the image
- For multiple choice, provide 4 options with only one correct
- For true/false, make statements that can be verified from the image
- Include brief explanations for educational value

SMART QUESTION GUIDELINES:
1. AVOID questions where multiple options could be technically correct
2. ENSURE multiple choice options are clearly distinct and verifiable
3. For counting questions, be specific about what to count
4. For identification questions, ask about clearly visible elements
5. Create meaningful distractors for multiple choice (wrong but plausible options)

QUESTION TYPES TO GENERATE:
1. Identification: "What color is the square?" or "What letter is shown in the image?"
2. Counting: "How many shapes are in this image?" or "How many letters can you see?"
3. Spatial: "Where is the letter located?" or "What shape contains the letter?"
4. True/False: "True or false: The letter is red" or "True or false: There are 3 shapes"
5. Multiple Choice: "What color is the background? A) White B) Blue C) Red D) Green"

AVOID THESE BAD QUESTION TYPES:
- Questions where all options are equally valid
- Asking about elements not clearly described in the context
- Multiple choice where the distinction between options is unclear
- Questions about subjective interpretations

Return ONLY a JSON array of question objects with this exact format:
[
  {{
    "text": "What color is the square?",
    "type": "identification",
    "correct_answer": "red",
    "options": null,
    "difficulty": "{difficulty}",
    "category": "colors",
    "explanation": "The square in the image is clearly red."
  }},
  {{
    "text": "How many shapes are in this image?",
    "type": "counting", 
    "correct_answer": "3",
    "options": ["2", "3", "4", "5"],
    "difficulty": "{difficulty}",
    "category": "counting",
    "explanation": "There are exactly 3 distinct shapes visible."
  }}
]

Generate exactly {num_questions} SMART questions with clear, unambiguous answers. Start with [ and end with ]. No other text."""

    def _create_multi_image_prompt(self, context: Dict, difficulty: str, num_questions: int, types: List[str]) -> str:
        """Create the prompt for multi-image question generation"""
        
        # Safe access to context fields
        image_summaries = context.get('image_summaries', [])
        num_images = context.get('num_images', 0)
        all_colors = context.get('all_colors', [])
        all_shapes = context.get('all_shapes', [])
        all_categories = context.get('all_categories', [])
        color_counts = context.get('color_counts', {})
        shape_counts = context.get('shape_counts', {})
        images_with_colors = context.get('images_with_colors', {})
        images_with_shapes = context.get('images_with_shapes', {})
        
        # Find common and unique elements
        common_colors = [color for color, count in color_counts.items() if count > 1]
        common_shapes = [shape for shape, count in shape_counts.items() if count > 1]
        unique_colors = [color for color, count in color_counts.items() if count == 1]
        unique_shapes = [shape for shape, count in shape_counts.items() if count == 1]
        
        # Create image summaries text
        image_summaries_text = ""
        for summary in image_summaries:
            image_summaries_text += f"""
Block {summary['block_letter']} (Image {summary['image_number']}): {summary['description']}
- Colors: {', '.join(summary['colors'])}
- Shapes: {', '.join(summary['shapes'])}
- Letters: {', '.join(summary['letters'])}
- Numbers: {', '.join(summary['numbers'])}
- Category: {summary['category']}
"""
        
        return f"""Generate {num_questions} educational questions comparing {num_images} flashcard images:

IMAGES OVERVIEW:
{image_summaries_text}

COMPARATIVE ANALYSIS:
- Colors appearing in multiple images: {', '.join(common_colors[:10])}
- Shapes appearing in multiple images: {', '.join(common_shapes[:10])}
- Unique colors (only in one image): {', '.join(unique_colors[:10])}
- Unique shapes (only in one image): {', '.join(unique_shapes[:10])}
- All categories present: {', '.join(all_categories)}

CRITICAL REQUIREMENTS FOR SMART QUESTIONS:
- Difficulty level: {difficulty}
- Question types to include: {', '.join(types)}
- Focus on COMPARATIVE and COUNTING questions across images
- Ask about patterns, similarities, and differences
- Count how many images contain specific elements

SMART QUESTION GUIDELINES:
1. AVOID questions where all options are technically correct (e.g., "Which letter appears once?" when all letters are unique)
2. ONLY ask comparison questions when there are meaningful differences to compare
3. Focus on elements that appear in MULTIPLE images for comparison questions
4. For counting questions, ensure the answer is verifiable and meaningful
5. If all elements are unique, ask about totals or categories instead

PREFERRED MULTI-IMAGE QUESTION TYPES:
1. Counting across images: "How many images contain squares?" (only if squares appear in 2+ images)
2. Most/least comparisons: "Which color appears in the most images?" (only if colors repeat)
3. Pattern identification: "What shape appears in all images?" (only if there's a common shape)
4. True/False about patterns: "True or false: All images contain letters" 
5. Category questions: "How many different categories are shown?"
6. Block identification: "In which block is the red circle?" or "Which block contains a house?"
7. Block comparisons: "True or false: Block A has more shapes than Block B"
8. Block content questions: "What color is the triangle in Block C?"

BLOCK-SPECIFIC QUESTION EXAMPLES:
- "In which block do you see a [specific object/color/shape]?"
- "True or false: Block [X] contains [specific element]"
- "Which block has the most [elements/colors/shapes]?"
- "What is the main color in Block [X]?"

AVOID THESE BAD QUESTIONS:
- "Which letter appears only once?" when all letters are different
- "Which color is unique?" when asking about obviously unique elements
- Multiple choice where all options are equally correct
- Questions about elements that don't actually create meaningful comparisons

SPECIFIC COUNTING OPPORTUNITIES:
- Images with yellow: {len(images_with_colors.get('yellow', []))}
- Images with squares: {len(images_with_shapes.get('square', []))}
- Total different letters across all images: {len(context.get('all_letters', []))}

Return ONLY a JSON array of question objects with this exact format:
[
  {{
    "text": "How many images contain yellow elements?",
    "type": "counting",
    "correct_answer": "2",
    "options": ["1", "2", "3", "4"],
    "difficulty": "{difficulty}",
    "category": "multi-image-counting",
    "explanation": "Yellow appears in images 1 and 3."
  }},
  {{
    "text": "In which block do you see a red circle?",
    "type": "block_identification",
    "correct_answer": "Block A",
    "options": ["Block A", "Block B", "Block C", "Block D"],
    "difficulty": "{difficulty}",
    "category": "block-identification",
    "explanation": "The red circle is located in Block A."
  }},
  {{
    "text": "True or false: Block B contains a triangle",
    "type": "true_false",
    "correct_answer": "true",
    "options": null,
    "difficulty": "{difficulty}",
    "category": "block-content",
    "explanation": "Block B does contain a triangle shape."
  }}
]

Generate exactly {num_questions} SMART questions that avoid pointless comparisons. Start with [ and end with ]. No other text."""

    def _parse_questions_response(self, content: str) -> List[Question]:
        """Parse the OpenAI response into Question objects"""
        try:
            # Clean the response
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
            # Parse JSON
            questions_json = json.loads(content)
            
            questions = []
            for q_data in questions_json:
                questions.append(Question(
                    text=q_data['text'],
                    type=q_data['type'],
                    correct_answer=q_data['correct_answer'],
                    options=q_data.get('options'),
                    difficulty=q_data['difficulty'],
                    category=q_data['category'],
                    explanation=q_data.get('explanation')
                ))
            
            return questions
            
        except Exception as e:
            print(f"Error parsing questions: {e}")
            print(f"Raw content: {content[:200]}...")
            return []
    
    def _generate_fallback_questions(self, image_data: Dict, difficulty: str) -> QuestionSet:
        """Generate simple fallback questions when AI generation fails"""
        tags = image_data.get('tags', {})
        
        fallback_questions = []
        
        # Simple color question if colors exist
        if tags.get('colors'):
            color = tags['colors'][0]
            fallback_questions.append(Question(
                text=f"Is there a {color} color in this image?",
                type="true_false",
                correct_answer="true",
                difficulty=difficulty,
                category="colors",
                explanation=f"Yes, {color} is visible in the image."
            ))
        
        # Simple counting question
        total_items = tags.get('totalItems', '1')
        if total_items.isdigit() and int(total_items) > 0:
            fallback_questions.append(Question(
                text="How many items can you see in this image?",
                type="counting",
                correct_answer=total_items,
                options=[str(max(1, int(total_items)-1)), total_items, str(int(total_items)+1), str(int(total_items)+2)],
                difficulty=difficulty,
                category="counting",
                explanation=f"There are {total_items} distinct items visible."
            ))
        
        return QuestionSet(
            image_id=image_data.get('id', 'unknown'),
            questions=fallback_questions,
            total_questions=len(fallback_questions),
            difficulty_level=difficulty,
            generated_at=str(datetime.utcnow()),
            is_multi_image=False,
            source_images_count=1
        )
    
    def _generate_multi_image_fallback_questions(self, images_data: List[Dict[str, Any]], difficulty: str) -> QuestionSet:
        """Generate simple fallback questions when multi-image AI generation fails"""
        
        fallback_questions = []
        
        # Build basic multi-image context
        multi_context = self._build_multi_image_context(images_data)
        
        # Simple counting question about number of images
        fallback_questions.append(Question(
            text=f"How many images are you looking at?",
            type="counting",
            correct_answer=str(len(images_data)),
            options=[str(len(images_data)-1), str(len(images_data)), str(len(images_data)+1), str(len(images_data)+2)] if len(images_data) > 1 else ["1", "2", "3", "4"],
            difficulty=difficulty,
            category="multi-image-counting",
            explanation=f"There are {len(images_data)} images to analyze."
        ))
        
        # Question about common colors if any exist
        color_counts = multi_context.get('color_counts', {})
        common_colors = [color for color, count in color_counts.items() if count > 1]
        
        if common_colors:
            common_color = common_colors[0]
            count = color_counts[common_color]
            fallback_questions.append(Question(
                text=f"How many images contain {common_color} elements?",
                type="counting",
                correct_answer=str(count),
                options=[str(max(1, count-1)), str(count), str(count+1), str(min(len(images_data), count+2))],
                difficulty=difficulty,
                category="multi-image-counting",
                explanation=f"{common_color.capitalize()} appears in {count} of the {len(images_data)} images."
            ))
        
        # Question about categories if multiple exist
        if len(multi_context['all_categories']) > 1:
            categories = list(multi_context['all_categories'])
            fallback_questions.append(Question(
                text="Do all images belong to the same category?",
                type="true_false",
                correct_answer="false",
                difficulty=difficulty,
                category="multi-image-comparison",
                explanation=f"The images belong to different categories: {', '.join(categories)}."
            ))
        
        image_ids = [img.get('id', 'unknown') for img in images_data]
        
        return QuestionSet(
            image_id=image_ids,
            questions=fallback_questions,
            total_questions=len(fallback_questions),
            difficulty_level=difficulty,
            generated_at=str(datetime.utcnow()),
            is_multi_image=True,
            source_images_count=len(images_data)
        )

# Example usage function
async def generate_questions_for_image(image_id: str, supabase_client) -> Optional[QuestionSet]:
    """
    Generate questions for a specific image from your database
    This is an example - adapt to your specific Supabase client setup
    """
    try:
        # This would be adapted to your specific Supabase client implementation
        # For now, this serves as a template
        generator = QuestionGenerator()
        
        # You would fetch the image data here using your existing methods
        # Example structure:
        image_data = {
            "id": image_id,
            "description": "Sample description",
            "confidence": 0.9,
            "tags": {
                "colors": ["red", "blue"],
                "shapes": ["circle", "square"],
                "category": "shapes"
            }
        }
        
        return await generator.generate_questions(
            image_data=image_data,
            difficulty_level="elementary",
            num_questions=5
        )
    except Exception as e:
        print(f"Error generating questions: {e}")
        return None
