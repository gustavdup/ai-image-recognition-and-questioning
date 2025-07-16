#!/usr/bin/env python3

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.question_generator import QuestionGenerator

async def test_question_generation():
    """Test the question generation functionality"""
    
    # Sample image data (similar to what your Edge Function would produce)
    sample_image_data = {
        "id": "test-image-123",
        "description": "A colorful educational flashcard showing a red circle, blue square, and yellow triangle on a white background. The word 'RED' is written in blue letters next to the red circle.",
        "confidence": 0.92,
        "tags": {
            "colors": ["red", "blue", "yellow", "white"],
            "shapes": ["circle", "square", "triangle"],
            "letters": ["R", "E", "D"],
            "numbers": [],
            "words": ["RED"],
            "objects": [],
            "people": [],
            "animals": [],
            "shapeColors": ["red circle", "blue square", "yellow triangle"],
            "shapeContents": [],
            "nestedElements": [],
            "textColor": "blue",
            "textVsSemanticMismatch": "word 'RED' displayed in blue color",
            "textLocation": "next to shape",
            "objectColors": [],
            "objectPositions": ["left", "center", "right"],
            "itemsInsideShapes": [],
            "overlappingItems": [],
            "relativePositions": ["word next to circle"],
            "colorWordMismatches": ["word 'RED' written in blue"],
            "highlightedElements": [],
            "backgroundColor": "white",
            "hasColoredBackground": "false",
            "totalItems": "4",
            "letterCount": "3",
            "numberCount": "0",
            "objectCount": "0",
            "shapeCount": "3",
            "category": "color-word-mismatch",
            "questionTypes": ["identification", "counting", "color", "true-false"]
        }
    }
    
    print("🧪 Testing Question Generation")
    print("=" * 50)
    
    try:
        # Create question generator
        generator = QuestionGenerator()
        print("✅ QuestionGenerator created successfully")
        
        # Test different difficulty levels
        for difficulty in ["preschool", "elementary", "middle"]:
            print(f"\n🎓 Testing {difficulty} level questions...")
            
            try:
                question_set = await generator.generate_questions(
                    image_data=sample_image_data,
                    difficulty_level=difficulty,
                    num_questions=3,
                    question_types=["identification", "true_false", "multiple_choice"]
                )
                
                print(f"✅ Generated {question_set.total_questions} questions for {difficulty}")
                
                for i, question in enumerate(question_set.questions):
                    print(f"\n  Question {i+1}: {question.text}")
                    print(f"  Type: {question.type}")
                    print(f"  Answer: {question.correct_answer}")
                    if question.options:
                        print(f"  Options: {question.options}")
                    if question.explanation:
                        print(f"  Explanation: {question.explanation}")
                        
            except Exception as e:
                print(f"❌ Error generating questions for {difficulty}: {e}")
                # Print the fallback questions
                fallback = generator._generate_fallback_questions(sample_image_data, difficulty)
                print(f"📋 Fallback: Generated {fallback.total_questions} fallback questions")
    
    except Exception as e:
        print(f"❌ Critical error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting Question Generation Test")
    asyncio.run(test_question_generation())
    print("\n🎉 Test completed!")
