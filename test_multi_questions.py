#!/usr/bin/env python3

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.question_generator import QuestionGenerator

async def test_multi_image_questions():
    """Test the multi-image question generation functionality"""
    
    # Sample data for multiple images (similar to what your Edge Function would produce)
    sample_images_data = [
        {
            "id": "image-1",
            "description": "A red circle and blue square on white background",
            "confidence": 0.92,
            "tags": {
                "colors": ["red", "blue", "white"],
                "shapes": ["circle", "square"],
                "letters": [],
                "numbers": [],
                "words": [],
                "objects": [],
                "shapeColors": ["red circle", "blue square"],
                "totalItems": "2",
                "category": "shapes"
            }
        },
        {
            "id": "image-2", 
            "description": "Yellow triangle and red star on white background",
            "confidence": 0.88,
            "tags": {
                "colors": ["yellow", "red", "white"],
                "shapes": ["triangle", "star"],
                "letters": [],
                "numbers": [],
                "words": [],
                "objects": [],
                "shapeColors": ["yellow triangle", "red star"],
                "totalItems": "2",
                "category": "shapes"
            }
        },
        {
            "id": "image-3",
            "description": "Green circle and yellow square with letter A",
            "confidence": 0.95,
            "tags": {
                "colors": ["green", "yellow", "white"],
                "shapes": ["circle", "square"],
                "letters": ["A"],
                "numbers": [],
                "words": [],
                "objects": [],
                "shapeColors": ["green circle", "yellow square"],
                "totalItems": "3",
                "category": "mixed"
            }
        }
    ]
    
    print("🧪 Testing Multi-Image Question Generation")
    print("=" * 60)
    
    try:
        # Create question generator
        generator = QuestionGenerator()
        print("✅ QuestionGenerator created successfully")
        
        print(f"\n📊 Analyzing {len(sample_images_data)} images:")
        for i, img in enumerate(sample_images_data):
            tags = img['tags']
            print(f"  Image {i+1}: {', '.join(tags['colors'])} | {', '.join(tags['shapes'])} | Category: {tags['category']}")
        
        print(f"\n🎓 Testing multi-image question generation...")
        
        try:
            question_set = await generator.generate_questions(
                image_data=sample_images_data,  # Pass list for multi-image
                difficulty_level="elementary",
                num_questions=6,
                question_types=["counting", "comparison", "true_false", "multiple_choice"]
            )
            
            print(f"✅ Generated {question_set.total_questions} multi-image questions")
            print(f"📈 Multi-image mode: {question_set.is_multi_image}")
            print(f"🖼️ Source images: {question_set.source_images_count}")
            
            for i, question in enumerate(question_set.questions):
                print(f"\n  Question {i+1}: {question.text}")
                print(f"  Type: {question.type}")
                print(f"  Category: {question.category}")
                print(f"  Answer: {question.correct_answer}")
                if question.options:
                    print(f"  Options: {question.options}")
                if question.explanation:
                    print(f"  Explanation: {question.explanation}")
                    
        except Exception as e:
            print(f"❌ Error generating multi-image questions: {e}")
            import traceback
            traceback.print_exc()
    
    except Exception as e:
        print(f"❌ Critical error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting Multi-Image Question Generation Test")
    asyncio.run(test_multi_image_questions())
    print("\n🎉 Test completed!")
