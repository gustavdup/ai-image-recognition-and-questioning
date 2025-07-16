#!/usr/bin/env python3

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

async def test_multi_image_context():
    """Test the multi-image context building"""
    from app.question_generator import QuestionGenerator
    
    # Sample multi-image data
    images_data = [
        {
            "id": "img1",
            "description": "An image of a yellow square with the number 13",
            "tags": {
                "colors": ["yellow", "black"],
                "shapes": ["square"],
                "letters": ["1", "3"],
                "numbers": ["13"],
                "category": "numbers"
            }
        },
        {
            "id": "img2", 
            "description": "The image depicts the word 'blue' written in red font",
            "tags": {
                "colors": ["red", "white"],
                "shapes": [],
                "letters": ["b", "l", "u", "e"],
                "numbers": [],
                "category": "color-word-mismatch"
            }
        }
    ]
    
    generator = QuestionGenerator()
    
    # Test context building
    context = generator._build_multi_image_context(images_data)
    print("🔧 Multi-image context built:")
    print(f"  Colors: {context['all_colors']}")
    print(f"  Shapes: {context['all_shapes']}")
    print(f"  Letters: {context['all_letters']}")
    print(f"  Images: {context['num_images']}")
    
    # Test question generation with context
    try:
        questions = await generator.generate_questions(
            image_data=images_data,
            difficulty_level="elementary",
            num_questions=3
        )
        print(f"✅ Generated {questions.total_questions} questions")
        for i, q in enumerate(questions.questions):
            print(f"  Q{i+1}: {q.text}")
            print(f"      Answer: {q.correct_answer}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_multi_image_context())
