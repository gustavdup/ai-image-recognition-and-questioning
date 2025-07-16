      // Enhanced Supabase Edge Function with OpenAI Vision API
      import { serve } from "https://deno.land/std@0.192.0/http/server.ts";
      import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

      // Structured logging helper
      class Logger {
        static info(message: string, data?: any) {
          const timestamp = new Date().toISOString();
          console.log(`[${timestamp}] ℹ️  ${message}`, data ? JSON.stringify(data, null, 2) : '');
        }
        
        static error(message: string, error?: any) {
          const timestamp = new Date().toISOString();
          console.error(`[${timestamp}] ❌ ${message}`);
          if (error) {
            console.error('Error details:', error);
            if (error.stack) console.error('Stack trace:', error.stack);
          }
        }
        
        static success(message: string, data?: any) {
          const timestamp = new Date().toISOString();
          console.log(`[${timestamp}] ✅ ${message}`, data ? JSON.stringify(data, null, 2) : '');
        }
        
        static warning(message: string, data?: any) {
          const timestamp = new Date().toISOString();
          console.warn(`[${timestamp}] ⚠️  ${message}`, data ? JSON.stringify(data, null, 2) : '');
        }
        
        static debug(message: string, data?: any) {
          const timestamp = new Date().toISOString();
          console.log(`[${timestamp}] 🐛 ${message}`, data ? JSON.stringify(data, null, 2) : '');
        }
      }

      // OpenAI Vision API function with two-tier approach
      async function analyzeImageWithGPT(imageUrl: string, openaiApiKey: string) {
        Logger.info("🔍 Starting OpenAI Vision analysis", { 
          imageUrl,
          urlLength: imageUrl.length,
          isDataUrl: imageUrl.startsWith('data:'),
          isHttpUrl: imageUrl.startsWith('http'),
          urlPreview: imageUrl.substring(0, 100) + (imageUrl.length > 100 ? "..." : "")
        });
        
        // 🚨 CRITICAL CHECK: Detect if we're accidentally passing base64 data
        if (imageUrl.startsWith('data:')) {
          Logger.error("🚨 BASE64 DETECTED! This will cause massive token usage!", {
            dataUrlLength: imageUrl.length,
            first100Chars: imageUrl.substring(0, 100)
          });
        }
        
        // 📝 EDUCATIONAL PROMPT: Comprehensive flashcard analysis with flat structure
        const prompt = `Analyze this educational flashcard quadrant image with precision for automatic question generation. Return a JSON object:

{
  "description": "Brief description of what's in the image",
  "confidence": "Rate your confidence in this analysis from 0.0 to 1.0. Consider image quality, clarity of objects, and analysis completeness. Be realistic , 0.9+ only when youre exceptionally confident",
  "tags": {
    "colors": ["red", "blue", "green", "yellow", "orange", "purple", "pink", "black", "white", "brown", "gray"],
    "shapes": ["circle", "triangle", "square", "rectangle", "star", "heart", "diamond", "oval", "pentagon", "hexagon"],
    "letters": ["A", "B", "C"],
    "numbers": ["0", "1", "2", "3"],
    "words": ["red", "blue", "green"],
    "objects": ["umbrella", "bicycle", "tree", "violin", "igloo", "key", "house", "nest"],
    "people": ["boy", "girl", "man", "woman", "child"],
    "animals": ["cat", "dog", "bird", "fish", "horse"],
    "shapeColors": ["red circle", "blue triangle", "yellow square"],
    "shapeContents": ["letter F inside red square", "number 5 inside yellow star"],
    "nestedElements": ["black circle inside orange star", "white text inside blue shape"],
    "textColor": "actual display color of text",
    "textVsSemanticMismatch": "word 'red' displayed in blue color",
    "textLocation": "inside shape, on background, overlay",
    "objectColors": ["red umbrella", "blue bicycle"],
    "objectPositions": ["top", "bottom", "left", "right", "center", "overlapping"],
    "itemsInsideShapes": ["letter F inside red square", "number 17 inside yellow circle"],
    "overlappingItems": ["umbrella overlapping with tree"],
    "relativePositions": ["bicycle left of tree", "key above house"],
    "colorWordMismatches": ["word 'green' written in red", "word 'blue' written in yellow"],
    "highlightedElements": ["yellow square overlay", "colored border around item"],
    "backgroundColor": "specific background color",
    "hasColoredBackground": "true or false",
    "totalItems": "exact count of all distinct visual elements",
    "letterCount": "number of letters present",
    "numberCount": "number of numerical digits",
    "objectCount": "number of real-world objects",
    "shapeCount": "number of geometric shapes",
    "category": "letters|numbers|shapes|colors|objects|mixed|color-word-mismatch",
    "questionTypes": ["identification", "counting", "color", "position", "relationship", "true-false"]
  }
}

CRITICAL ANALYSIS REQUIREMENTS:
1. **TEXT vs VISUAL DISCREPANCY**: Detect when color words don't match their display color (e.g., "red" written in blue)
2. **NESTED CONTENT**: Identify what's inside geometric shapes (letters, numbers, objects)
3. **SPATIAL RELATIONSHIPS**: Map relative positions and overlapping elements
4. **BACKGROUND CONTEXT**: Distinguish between background colors and shape colors
5. **HIGHLIGHTED ELEMENTS**: Detect yellow overlays, borders, or emphasis markers
6. **COUNTING PRECISION**: Count all distinct visual elements accurately
7. **COLOR SPECIFICITY**: Name exact colors, not generic terms
8. **OBJECT CLASSIFICATION**: Identify specific real-world items (violin, not just "instrument")
9. **TEXT EXTRACTION**: OCR all visible letters, numbers, and words
10. **RELATIONSHIP MAPPING**: What contains what, what's next to what

Enable questions like:
- "What color is the square in this quadrant?" 
- "What letter is inside the red shape?"
- "Name the color, not the word, in this image"
- "What number is on the yellow square?"
- "How many items are in this quadrant - two or three?"
- "What musical instrument has 6 letters and starts with this letter?"
- "True or false? There is an umbrella in this image"
- "What is the color and shape of this element?"
- "Which items are highlighted with yellow?"
- "What letters are in the yellow squares?"

IMPORTANT: Return ONLY the JSON object, no markdown formatting, no code blocks. Start with { and end with }.`;
        
        // 🔍 PROdo a gMPT LENGTH CHECK
        Logger.info("📏 Prompt analysis", {
          promptLength: prompt.length,
          promptCharCount: prompt.length,
          promptWordCount: prompt.split(' ').length,
          promptPreview: prompt.substring(0, 200) + "..."
        });

        // First attempt: Use GPT-4o (better for complex analysis)
        Logger.info("📤 First attempt with GPT-4o (initial analysis)...");
        
        let result = await makeVisionRequest(imageUrl, openaiApiKey, prompt, "gpt-4o", 2000);
        let attempt = 1;
        let confidence = 0.0;
        
        // Extract confidence from first attempt
        try {
          const gptContent = result.choices[0]?.message?.content;
          if (gptContent) {
            Logger.debug("🔍 Raw GPT content for confidence parsing", { 
              contentPreview: gptContent.substring(0, 300),
              contentLength: gptContent.length 
            });
            
            const analysisData = await parseGPTResponse(gptContent);
            confidence = analysisData.confidence || 0.0;
            
            // More detailed confidence debugging
            Logger.info(`📊 First attempt confidence: ${confidence}`, { 
              model: "gpt-4o",
              rawConfidence: analysisData.confidence,
              confidenceType: typeof analysisData.confidence,
              confidenceString: String(analysisData.confidence),
              parsedAsNumber: Number(analysisData.confidence),
              analysisDataKeys: Object.keys(analysisData),
              hasConfidenceProperty: analysisData.hasOwnProperty('confidence')
            });
            
            // Log raw JSON snippet around confidence
            const confidenceMatch = gptContent.match(/"confidence":\s*"?([^",}]+)"?/);
            if (confidenceMatch) {
              Logger.debug("🎯 Confidence field found in raw JSON", {
                matchedValue: confidenceMatch[1],
                fullMatch: confidenceMatch[0]
              });
            } else {
              Logger.warning("⚠️ No confidence field found in raw JSON");
            }
          }
        } catch (parseError) {
          Logger.warning("⚠️ Could not parse confidence from first attempt", { 
            error: parseError.message,
            stack: parseError.stack 
          });
          confidence = 0.0; // Force retry on parse error
        }
        
        // If confidence is below 80%, retry with GPT-4o as fallback
        if (confidence < 0.8) {
          Logger.info("🔄 Low confidence detected, retrying with gpt-4-turbo as fallback...");
          result = await makeVisionRequest(imageUrl, openaiApiKey, prompt, "gpt-4-turbo", 1000);
          attempt = 2;
          
          // Update confidence from second attempt
          try {
            const gptContent = result.choices[0]?.message?.content;
            if (gptContent) {
              Logger.debug("🔍 Raw GPT content for second attempt confidence parsing", { 
                contentPreview: gptContent.substring(0, 300),
                contentLength: gptContent.length 
              });
              
              const analysisData = await parseGPTResponse(gptContent);
              confidence = analysisData.confidence || 0.0;
              
              Logger.info(`📊 Second attempt confidence: ${confidence}`, { 
                model: "gpt-4-turbo",
                rawConfidence: analysisData.confidence,
                analysisDataKeys: Object.keys(analysisData),
                hasConfidenceProperty: analysisData.hasOwnProperty('confidence')
              });
            }
          } catch (parseError) {
            Logger.warning("⚠️ Could not parse confidence from second attempt", {
              error: parseError.message,
              stack: parseError.stack
            });
          }
        }
        
        // Extract token usage information and add attempt metadata
        const usage = result.usage || {};
        const promptTokens = usage.prompt_tokens || 0;
        const completionTokens = usage.completion_tokens || 0;
        const totalTokens = usage.total_tokens || 0;
        
        Logger.success("✅ Vision API analysis complete", { 
          attempts: attempt,
          finalConfidence: confidence,
          promptTokens,
          completionTokens,
          totalTokens
        });
        
        return { 
          ...result, 
          tokenUsage: { promptTokens, completionTokens, totalTokens },
          analysisMetadata: { attempts: attempt, finalConfidence: confidence }
        };
      }

      // Helper function to make vision API requests
      async function makeVisionRequest(imageUrl: string, openaiApiKey: string, prompt: string, model: string, maxTokens: number) {
        // 🔍 DETAILED REQUEST DEBUGGING
        Logger.info("🚀 Preparing OpenAI Vision API request", {
          model,
          maxTokens,
          imageUrl: imageUrl,
          imageUrlLength: imageUrl.length,
          isDataUrl: imageUrl.startsWith('data:'),
          isHttpUrl: imageUrl.startsWith('http'),
          promptLength: prompt.length,
          promptPreview: prompt.substring(0, 200) + "..."
        });
        
        // Check if image URL looks like base64 (which would cause high token usage)
        if (imageUrl.startsWith('data:')) {
          Logger.error("❌ DETECTED BASE64 IMAGE URL - This will cause high token usage!", {
            urlStart: imageUrl.substring(0, 50),
            totalLength: imageUrl.length
          });
        }
        
        const requestPayload = {
          model: model,
          messages: [
            {
              role: "user",
              content: [
                { type: "text", text: prompt },
                { type: "image_url", image_url: { url: imageUrl } }
              ]
            }
          ],
          max_tokens: maxTokens
        };
        
        // Log the exact payload being sent (but truncate if it's huge)
        const payloadStr = JSON.stringify(requestPayload);
        
        // 🔍 DETAILED PAYLOAD ANALYSIS
        const textContent = requestPayload.messages[0].content.find(c => c.type === 'text')?.text || '';
        const imageContent = requestPayload.messages[0].content.find(c => c.type === 'image_url')?.image_url?.url || '';
        
        Logger.debug("📤 Exact OpenAI request payload analysis", {
          payloadSize: payloadStr.length,
          textContentLength: textContent.length,
          imageUrlLength: imageContent.length,
          payloadPreview: payloadStr.length > 1000 ? payloadStr.substring(0, 1000) + "..." : payloadStr,
          isLargePayload: payloadStr.length > 10000,
          containsBase64: payloadStr.includes('data:image'),
          messageCount: requestPayload.messages.length,
          contentItemCount: requestPayload.messages[0].content.length,
          actualImageUrl: imageContent
        });
        
        const response = await fetch("https://api.openai.com/v1/chat/completions", {
          method: "POST",
          headers: {
            "Authorization": `Bearer ${openaiApiKey}`,
            "Content-Type": "application/json",
          },
          body: payloadStr
        });

        Logger.info("📥 Vision API response", { status: response.status, model });

        if (!response.ok) {
          const errorText = await response.text();
          Logger.error("❌ OpenAI Vision API error", { 
            status: response.status, 
            statusText: response.statusText,
            error: errorText,
            model,
            imageUrl: imageUrl 
          });
          throw new Error(`OpenAI API error (${model}): ${response.status} ${response.statusText} - ${errorText}`);
        }

        const responseData = await response.json();
        
        // 🔍 DETAILED RESPONSE ANALYSIS
        Logger.info("📊 OpenAI Response Details", {
          model: responseData.model,
          usage: responseData.usage,
          promptTokens: responseData.usage?.prompt_tokens,
          completionTokens: responseData.usage?.completion_tokens,
          totalTokens: responseData.usage?.total_tokens,
          choicesCount: responseData.choices?.length,
          contentLength: responseData.choices?.[0]?.message?.content?.length
        });
        
        return responseData;
      }

      // Helper function to parse GPT response with enhanced error handling
      async function parseGPTResponse(gptContent: string) {
        Logger.debug("🔍 Raw GPT content received", { length: gptContent.length, preview: gptContent.substring(0, 200) });
        
        // Helper function to clean and fix common JSON issues
        function cleanJson(jsonStr: string): string {
          let cleaned = jsonStr.trim();
          
          // Remove any trailing commas before closing braces/brackets
          cleaned = cleaned.replace(/,(\s*[}\]])/g, '$1');
          
          // Fix any unescaped quotes in string values (basic attempt)
          // This is a simple fix - in production you might want more sophisticated handling
          cleaned = cleaned.replace(/([^\\])"([^",:}\]]*)"([^,:}\]]+)"/g, '$1"$2\\"$3"');
          
          return cleaned;
        }
        
        // Parse the JSON response - handle both pure JSON and markdown-wrapped JSON
        try {
          // First try parsing as-is
          const parsed = JSON.parse(gptContent);
          Logger.debug("✅ JSON parsed successfully", { 
            hasConfidence: parsed.hasOwnProperty('confidence'),
            confidenceValue: parsed.confidence,
            confidenceType: typeof parsed.confidence,
            topLevelKeys: Object.keys(parsed)
          });
          return parsed;
        } catch (firstError) {
          Logger.warning("⚠️ Initial JSON parse failed, trying to extract and clean", { 
            error: firstError.message,
            position: gptContent.substring(Math.max(0, 1070), 1100) // Show content around error position
          });
          
          // Try to clean common JSON issues
          try {
            const cleanedContent = cleanJson(gptContent);
            const parsed = JSON.parse(cleanedContent);
            Logger.debug("✅ Cleaned JSON parsed successfully", { 
              hasConfidence: parsed.hasOwnProperty('confidence'),
              confidenceValue: parsed.confidence,
              confidenceType: typeof parsed.confidence
            });
            return parsed;
          } catch (cleanError) {
            Logger.warning("⚠️ Cleaned JSON parse failed, trying markdown extraction", { error: cleanError.message });
          }
          
          // Look for JSON content between ```json and ``` or between ``` and ```
          const jsonMatch = gptContent.match(/```(?:json)?\s*\n?([\s\S]*?)\n?```/);
          if (jsonMatch && jsonMatch[1]) {
            try {
              const extractedJson = cleanJson(jsonMatch[1].trim());
              const parsed = JSON.parse(extractedJson);
              Logger.debug("✅ Markdown extracted JSON parsed successfully", { 
                hasConfidence: parsed.hasOwnProperty('confidence'),
                confidenceValue: parsed.confidence,
                confidenceType: typeof parsed.confidence
              });
              return parsed;
            } catch (secondError) {
              Logger.error("❌ Failed to parse extracted and cleaned JSON", { 
                error: secondError.message, 
                extracted: jsonMatch[1].substring(0, 500) + "..." 
              });
            }
          }
          
          // Try to find any JSON-like content and clean it
          const jsonStart = gptContent.indexOf('{');
          const jsonEnd = gptContent.lastIndexOf('}') + 1;
          if (jsonStart !== -1 && jsonEnd > jsonStart) {
            const extractedJson = gptContent.slice(jsonStart, jsonEnd);
            try {
              const cleanedJson = cleanJson(extractedJson);
              Logger.debug("🔧 Attempting to parse cleaned extracted JSON", { 
                original: extractedJson.substring(0, 200),
                cleaned: cleanedJson.substring(0, 200)
              });
              const parsed = JSON.parse(cleanedJson);
              Logger.debug("✅ Final extraction JSON parsed successfully", { 
                hasConfidence: parsed.hasOwnProperty('confidence'),
                confidenceValue: parsed.confidence,
                confidenceType: typeof parsed.confidence
              });
              return parsed;
            } catch (thirdError) {
              Logger.error("❌ All JSON parsing attempts failed", { 
                originalError: firstError.message,
                extractedLength: extractedJson.length,
                cleaningError: thirdError.message,
                errorPosition: extractedJson.substring(Math.max(0, 1070), 1100)
              });
              
              // As a last resort, return a minimal valid response to prevent total failure
              Logger.warning("🚨 Returning fallback response due to JSON parse failure");
              return {
                description: "Analysis failed due to JSON parsing error",
                confidence: 0.1,
                tags: {
                  colors: [],
                  shapes: [],
                  letters: [],
                  numbers: [],
                  words: [],
                  objects: [],
                  people: [],
                  animals: [],
                  shapeColors: [],
                  shapeContents: [],
                  nestedElements: [],
                  textColor: "unknown",
                  textVsSemanticMismatch: "none detected",
                  textLocation: "unknown",
                  objectColors: [],
                  objectPositions: [],
                  itemsInsideShapes: [],
                  overlappingItems: [],
                  relativePositions: [],
                  colorWordMismatches: [],
                  highlightedElements: [],
                  backgroundColor: "unknown",
                  hasColoredBackground: "false",
                  totalItems: "0",
                  letterCount: "0",
                  numberCount: "0",
                  objectCount: "0",
                  shapeCount: "0",
                  category: "unknown",
                  questionTypes: []
                }
              };
            }
          } else {
            Logger.error("❌ No JSON-like content found in response");
            throw new Error(`No valid JSON found in GPT response: ${firstError.message}`);
          }
        }
      }

      // Generate embedding from text
      async function generateEmbedding(text: string, openaiApiKey: string) {
        console.log("🔢 Generating embedding for text:", text.substring(0, 100) + "...");
        
        const response = await fetch("https://api.openai.com/v1/embeddings", {
          method: "POST",
          headers: {
            "Authorization": `Bearer ${openaiApiKey}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            model: "text-embedding-3-small",
            input: text
          })
        });

        console.log("📥 Embedding API response status:", response.status);

        if (!response.ok) {
          const errorText = await response.text();
          console.error("❌ OpenAI Embedding API error:", response.status, errorText);
          throw new Error(`OpenAI Embedding API error: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();
        console.log("✅ Embedding generated, dimensions:", data.data[0].embedding.length);
        return data.data[0].embedding;
      }

      serve(async (req) => {
        const functionStart = Date.now();
        const requestId = crypto.randomUUID().substring(0, 8); // Short ID for this request
        Logger.info(`🚀 Edge Function triggered [${requestId}]`);
        
        // 🔍 CHECK FOR DUPLICATE CALLS
        const callTimestamp = Date.now();
        Logger.info(`📞 Function call tracking [${requestId}]`, {
          timestamp: callTimestamp,
          requestId,
          userAgent: req.headers.get('user-agent'),
          contentType: req.headers.get('content-type'),
          authorization: req.headers.get('authorization') ? 'present' : 'missing'
        });
        
        try {
          const body = await req.json();
          Logger.info(`📨 Webhook payload received [${requestId}]`, body);
          
          // Handle different webhook payload formats
          const record = body.record || body;
          const supabaseUrl = Deno.env.get("SUPABASE_URL");
          const supabaseKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
          const openaiApiKey = Deno.env.get("OPENAI_API_KEY");
          const bucket = "images"; // Hardcoded bucket name

          Logger.info(`🔧 Environment check [${requestId}]`, {
            hasSupabaseUrl: !!supabaseUrl,
            hasSupabaseKey: !!supabaseKey,
            hasOpenAIKey: !!openaiApiKey,
            bucketName: bucket
          });

          if (!record || !record.name) {
            Logger.error(`❌ No file info found in payload [${requestId}]`, { payload: body });
            return new Response(JSON.stringify({ error: "No file info", payload: body }), { status: 400 });
          }

          if (!openaiApiKey) {
            Logger.error(`❌ Missing OpenAI API key [${requestId}]`);
            return new Response(JSON.stringify({ error: "Missing OpenAI API key" }), { status: 500 });
          }

          // Supabase client
          const supabase = createClient(supabaseUrl, supabaseKey);
          Logger.success(`✅ Supabase client initialized [${requestId}]`);

          // 🛡️ DEDUPLICATION: Check if this file has already been processed
          Logger.info(`🔍 Checking for existing record [${requestId}]`, { fileName: record.name });
          const { data: existingImages, error: checkError } = await supabase
            .from("images")
            .select("id, image_name, description")
            .eq("image_name", record.name)
            .limit(1);
          
          if (checkError) {
            Logger.warning(`⚠️ Error checking existing records [${requestId}]`, checkError);
          } else if (existingImages && existingImages.length > 0) {
            const existing = existingImages[0];
            Logger.info(`🚫 File already processed [${requestId}]`, { 
              fileName: record.name,
              existingId: existing.id,
              hasDescription: !!existing.description
            });
            
            // If already has AI analysis, skip completely
            if (existing.description) {
              Logger.success(`✅ Skipping duplicate processing [${requestId}]`);
              return new Response(JSON.stringify({ 
                success: true, 
                message: "Already processed",
                id: existing.id,
                skipped: true 
              }), { status: 200 });
            }
          }

          // Generate UUID and new filename
          const uuid = crypto.randomUUID();
          const ext = record.name.split('.').pop();
          const newName = `${uuid}.${ext}`;
          
          Logger.info(`📁 File processing [${requestId}]`, {
            originalName: record.name,
            newName: newName,
            uuid: uuid,
            extension: ext
          });

          // Add small random delay to reduce race conditions with concurrent uploads
          const randomDelay = Math.floor(Math.random() * 500) + 100; // 100-600ms
          await new Promise(resolve => setTimeout(resolve, randomDelay));

          // Move/rename file with retry logic
          Logger.info(`🔄 Moving/renaming file [${requestId}]...`);
          let moveRes;
          let retryCount = 0;
          const maxRetries = 3;
          
          while (retryCount < maxRetries) {
            moveRes = await supabase.storage.from(bucket).move(record.name, newName);
            if (!moveRes.error) break;
            
            retryCount++;
            if (retryCount < maxRetries) {
              Logger.warning(`⚠️ Move retry ${retryCount}/${maxRetries} [${requestId}]`, moveRes.error);
              await new Promise(resolve => setTimeout(resolve, 1000 * retryCount)); // Exponential backoff
            }
          }
          
          if (moveRes.error) {
            Logger.error(`❌ Move error after ${maxRetries} attempts [${requestId}]`, moveRes.error);
            return new Response(JSON.stringify({ error: moveRes.error.message }), { status: 500 });
          }
          Logger.success(`✅ File renamed successfully [${requestId}]`);

          // Verify file exists and get its metadata
          Logger.info(`🔍 Verifying file exists [${requestId}]...`);
          const { data: fileList, error: listError } = await supabase.storage
            .from(bucket)
            .list('', {
              search: newName
            });
          
          if (listError) {
            Logger.error(`❌ Error checking file existence [${requestId}]`, listError);
          } else if (!fileList || fileList.length === 0) {
            Logger.error(`❌ File not found after rename [${requestId}]`, { fileName: newName });
            return new Response(JSON.stringify({ error: "File not found after upload" }), { status: 500 });
          } else {
            const fileInfo = fileList[0];
            Logger.info(`✅ File verified [${requestId}]`, {
              name: fileInfo.name,
              size: fileInfo.metadata?.size,
              type: fileInfo.metadata?.mimetype,
              lastModified: fileInfo.updated_at
            });
          }

          // Processing delay to ensure file is fully available
          await new Promise(resolve => setTimeout(resolve, 1500));

          // Get URLs for AI processing and database storage
          Logger.info("🔗 Generating URLs...");
          
          // Use public URL for both database storage and AI processing
          const publicUrl = supabase.storage.from(bucket).getPublicUrl(newName).data.publicUrl;
          const imageUrlForAI = publicUrl; // Always use public URL now
          
          Logger.info("🔗 URLs configured", { 
            publicUrl: publicUrl, 
            aiUrl: imageUrlForAI,
            note: "Using public URLs for better performance"
          });

          // Test if the URL is accessible
          Logger.info("🧪 Testing URL accessibility...");
          try {
            const testResponse = await fetch(imageUrlForAI, { 
              method: 'HEAD',
              headers: {
                'User-Agent': 'Supabase-Edge-Function/1.0'
              }
            });
            
            // 🔍 GET IMAGE SIZE AND DETAILS
            const contentLength = testResponse.headers.get('content-length');
            const contentType = testResponse.headers.get('content-type');
            
            Logger.info("📊 URL test result", {
              status: testResponse.status,
              statusText: testResponse.statusText,
              contentType: contentType,
              contentLength: contentLength,
              fileSizeBytes: contentLength ? parseInt(contentLength) : 'unknown',
              fileSizeKB: contentLength ? Math.round(parseInt(contentLength) / 1024) : 'unknown',
              fileSizeMB: contentLength ? Math.round(parseInt(contentLength) / (1024 * 1024) * 100) / 100 : 'unknown'
            });
            
            // 🚨 CHECK FOR LARGE IMAGES
            if (contentLength) {
              const sizeBytes = parseInt(contentLength);
              const sizeMB = sizeBytes / (1024 * 1024);
              
              if (sizeMB > 20) {
                Logger.error("🚨 VERY LARGE IMAGE DETECTED!", {
                  sizeMB: Math.round(sizeMB * 100) / 100,
                  sizeBytes,
                  message: "Large images can cause high token usage in OpenAI Vision API"
                });
              } else if (sizeMB > 10) {
                Logger.warning("⚠️ Large image detected", {
                  sizeMB: Math.round(sizeMB * 100) / 100,
                  sizeBytes
                });
              } else {
                Logger.success("✅ Normal image size", {
                  sizeMB: Math.round(sizeMB * 100) / 100,
                  sizeBytes
                });
              }
            }
            
            if (!testResponse.ok) {
              Logger.error("❌ Public URL not accessible", { url: imageUrlForAI });
              return new Response(JSON.stringify({ error: "Image not accessible via public URL" }), { status: 500 });
            }
          } catch (testError) {
            Logger.error("❌ URL test failed", { error: testError.message, url: imageUrlForAI });
            return new Response(JSON.stringify({ error: "Image URL test failed" }), { status: 500 });
          }

          // Insert basic record first
          Logger.info("💾 Inserting basic record to database...");
          
          const { error: insertError } = await supabase.from("images").insert({
            id: uuid,
            image_name: newName,
            image_url: publicUrl, // Store the permanent public URL
            created_at: new Date().toISOString(),
          });
          
          if (insertError) {
            Logger.error("❌ Database insert error", insertError);
            return new Response(JSON.stringify({ error: insertError.message, details: insertError }), { status: 500 });
          }
          Logger.success("✅ Basic record inserted successfully");

          Logger.info(`🤖 Starting AI analysis [${requestId}]...`);

          // 🔍 FINAL URL CHECK before sending to AI
          Logger.info("🔍 Final image URL validation before AI analysis", {
            imageUrlForAI,
            urlLength: imageUrlForAI.length,
            isDataUrl: imageUrlForAI.startsWith('data:'),
            isHttpUrl: imageUrlForAI.startsWith('http'),
            domain: imageUrlForAI.includes('supabase.co') ? 'supabase' : 'other',
            requestId
          });

          // Analyze image with OpenAI Vision
          try {
            const visionResponse = await analyzeImageWithGPT(imageUrlForAI, openaiApiKey);
            Logger.success(`📊 Vision analysis complete [${requestId}]`);

            const gptContent = visionResponse.choices[0]?.message?.content;
            if (!gptContent) {
              throw new Error("No content in GPT response");
            }

            console.log("📝 GPT response content:", gptContent);

            // Parse the JSON response using helper function
            const analysisData = await parseGPTResponse(gptContent);
            
            const description = analysisData.description;
            const confidence = analysisData.confidence || 0.0;
            const tags = analysisData.tags;
            
            // Extract token usage and analysis metadata
            const tokenUsage = visionResponse.tokenUsage || {};
            const promptTokens = tokenUsage.promptTokens || 0;
            const completionTokens = tokenUsage.completionTokens || 0;
            const totalTokens = tokenUsage.totalTokens || 0;
            const attempts = visionResponse.analysisMetadata?.attempts || 1;

            console.log("🏷️ Parsed analysis:", {
              description: description?.substring(0, 100) + "...",
              confidence: confidence,
              attempts: attempts,
              promptTokens,
              completionTokens,
              totalTokens,
              tagKeys: Object.keys(tags || {})
            });

            // 🚨 HIGH TOKEN USAGE ALERT
            if (promptTokens > 5000) {
              Logger.error("🚨 HIGH TOKEN USAGE DETECTED!", {
                promptTokens,
                totalTokens,
                imageUrl: imageUrlForAI,
                isDataUrl: imageUrlForAI.startsWith('data:'),
                urlLength: imageUrlForAI.length,
                requestId,
                message: "This indicates possible base64 encoding or other issue"
              });
            } else if (promptTokens > 2000) {
              Logger.warning("⚠️ Elevated token usage", {
                promptTokens,
                totalTokens,
                imageUrl: imageUrlForAI,
                requestId
              });
            } else {
              Logger.success("✅ Normal token usage", {
                promptTokens,
                totalTokens,
                requestId
              });
            }

            // Create embedding text from description and simplified tags structure
            const tagsData = analysisData.tags || {};
            const embeddingText = `${description}. 
            Confidence: ${confidence}. 
            Objects: ${Array.isArray(tagsData.objects) ? tagsData.objects.join(', ') : ''}. 
            Colors: ${Array.isArray(tagsData.colors) ? tagsData.colors.join(', ') : ''}. 
            Shapes: ${Array.isArray(tagsData.shapes) ? tagsData.shapes.join(', ') : ''}. 
            Letters: ${Array.isArray(tagsData.letters) ? tagsData.letters.join(', ') : ''}. 
            Numbers: ${Array.isArray(tagsData.numbers) ? tagsData.numbers.join(', ') : ''}. 
            Words: ${Array.isArray(tagsData.words) ? tagsData.words.join(', ') : ''}. 
            People: ${Array.isArray(tagsData.people) ? tagsData.people.join(', ') : ''}. 
            Animals: ${Array.isArray(tagsData.animals) ? tagsData.animals.join(', ') : ''}. 
            Category: ${tagsData.category || ''}. 
            Relationships: ${Array.isArray(tagsData.relationships) ? tagsData.relationships.join(', ') : ''}. 
            Background: ${tagsData.backgroundColor || ''}`.trim();
            console.log("📄 Embedding text prepared:", embeddingText.substring(0, 150) + "...");
            
            // Generate embedding
            const embedding = await generateEmbedding(embeddingText, openaiApiKey);

            // Update the record with AI-generated data
            console.log("💾 Updating record with AI data...");
            const { error: updateError } = await supabase
              .from("images")
              .update({
                description: description,
                confidence: confidence,
                tags: tags,
                raw_json: visionResponse,
                embedding: embedding,
                prompt_tokens: promptTokens,
                completion_tokens: completionTokens,
                total_tokens: totalTokens,
                analysis_attempts: attempts
              })
              .eq("id", uuid);

            if (updateError) {
              console.error("❌ Database update error:", updateError);
              // Don't fail the whole function, basic record is already inserted
            } else {
              console.log("✅ AI analysis complete and saved to database");
            }

          } catch (aiError) {
            console.error("❌ AI processing error:", aiError);
            console.error("Stack trace:", aiError.stack);
            // Don't fail the whole function, basic record is already inserted
          }

          const functionDuration = Date.now() - functionStart;
          Logger.success(`🎉 Function completed successfully [${requestId}]`, { 
            id: uuid, 
            image_url: publicUrl,
            duration_ms: functionDuration 
          });
          return new Response(JSON.stringify({ success: true, id: uuid, image_url: publicUrl }), { status: 200 });
          
        } catch (err) {
          const functionDuration = Date.now() - functionStart;
          Logger.error(`💥 Function error [${requestId}]`, { 
            error: err.message, 
            stack: err.stack,
            duration_ms: functionDuration 
          });
          return new Response(JSON.stringify({ error: err.message, stack: err.stack }), { status: 500 });
        }
      });
