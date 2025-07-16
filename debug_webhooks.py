"""
Check for potential webhook multiplication issues
"""

def analyze_webhook_behavior():
    print("🔍 WEBHOOK MULTIPLICATION ANALYSIS")
    print("=" * 40)
    
    print("💡 POSSIBLE WEBHOOK TRIGGERS:")
    print("1. 📤 Initial file upload (INSERT on storage.objects)")
    print("2. 🔄 File rename/move operation (UPDATE on storage.objects)")  
    print("3. 🏷️  Metadata updates (multiple UPDATEs)")
    print("4. 🔗 URL generation or access")
    print()
    
    print("🚨 MULTIPLICATION SCENARIOS:")
    print("• Webhook configured for INSERT + UPDATE events")
    print("• Multiple webhook endpoints configured")
    print("• File move triggering additional INSERT/UPDATE")
    print("• Retry logic in webhook delivery")
    print("• Browser/frontend making multiple upload requests")
    print()
    
    print("🛠️  DEBUGGING STEPS:")
    print("1. Check Supabase webhook configuration:")
    print("   - How many webhooks are configured?")
    print("   - What events trigger them (INSERT/UPDATE/DELETE)?")
    print()
    print("2. Check Edge Function logs:")
    print("   - Are you seeing multiple '[RequestID] Edge Function triggered' logs?")
    print("   - Are the same file being processed multiple times?")
    print()
    print("3. Add request deduplication:")
    print("   - Track processed files to prevent reprocessing")
    print("   - Add early exit for already-processed images")
    print()
    
    # Expected vs actual token calculation
    expected_tokens_single = 512 + 425  # prompt + small image
    expected_tokens_two_tier = 512 + 425 + 512 + 425  # if confidence < 0.8
    actual_tokens = 9035
    
    multiplier = actual_tokens / expected_tokens_single
    
    print("📊 TOKEN MATH:")
    print(f"   Single call expected: {expected_tokens_single:,} tokens")
    print(f"   Two-tier expected: {expected_tokens_two_tier:,} tokens")
    print(f"   Your actual usage: {actual_tokens:,} tokens")
    print(f"   Multiplication factor: {multiplier:.1f}x")
    print()
    
    if multiplier > 10:
        print("🚨 LIKELY CAUSE: Webhook multiplication!")
        print(f"   You're getting ~{multiplier:.0f} webhook calls per image")
        print("   This suggests webhook misconfiguration or frontend issues")

if __name__ == "__main__":
    analyze_webhook_behavior()
