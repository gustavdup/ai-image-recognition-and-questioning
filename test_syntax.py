#!/usr/bin/env python3

# Simple syntax check
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

try:
    from app.question_generator import QuestionGenerator
    print("✅ QuestionGenerator imported successfully")
    
    # Test instantiation
    generator = QuestionGenerator()
    print("✅ QuestionGenerator instantiated successfully")
    
    # Test context building
    images_data = [
        {
            "id": "img1",
            "description": "A pink square with the letter 'F'",
            "tags": {
                "colors": ["pink", "black"],
                "shapes": ["square"],
                "letters": ["F"],
                "numbers": [],
                "category": "letters"
            }
        },
        {
            "id": "img2", 
            "description": "A yellow square with the letter 'A'",
            "tags": {
                "colors": ["yellow", "black"],
                "shapes": ["square"],
                "letters": ["A"],
                "numbers": [],
                "category": "letters"
            }
        }
    ]
    
    context = generator._build_multi_image_context(images_data)
    print("✅ Multi-image context built successfully")
    print(f"   Context keys: {list(context.keys())}")
    print(f"   Colors: {context['all_colors']}")
    print(f"   Shapes: {context['all_shapes']}")
    print(f"   Letters: {context['all_letters']}")
    print(f"   Number of images: {context['num_images']}")
    
    # Test fallback questions
    fallback = generator._generate_multi_image_fallback_questions(images_data, "elementary")
    print(f"✅ Fallback questions generated: {fallback.total_questions} questions")
    for i, q in enumerate(fallback.questions):
        print(f"   Q{i+1}: {q.text}")
        print(f"       Answer: {q.correct_answer}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
