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

    // OpenAI Vision API function
    async function analyzeImageWithGPT(imageUrl: string, openaiApiKey: string) {
      Logger.info("🔍 Starting OpenAI Vision analysis", { imageUrl });
      
      const prompt = `Analyze this educational flashcard quadrant image with precision for automatic question generation. Return a JSON object:

    {
      "description": "Brief description of what's in the image",
      "tags": {
        "backgroundInfo": {
          "backgroundColor": "specific background color",
          "hasColoredBackground": true/false
        },
        "shapes": {
          "geometricShapes": ["circle", "triangle", "square", "rectangle", "star", "heart", "diamond", "oval", "pentagon", "hexagon"],
          "shapeColors": ["red circle", "blue triangle", "yellow square"],
          "shapeContents": ["letter F inside red square", "number 5 inside yellow star"],
          "nestedElements": ["black circle inside orange star", "white text inside blue shape"]
        },
        "textContent": {
          "letters": ["A", "B", "C", "etc"],
          "numbers": ["0", "1", "2", "3", "etc"], 
          "words": ["red", "blue", "green"],
          "textColor": "actual display color of text",
          "textVsSemanticMismatch": "word 'red' displayed in blue color",
          "textLocation": "inside shape, on background, overlay"
        },
        "objects": {
          "realWorldItems": ["umbrella", "bicycle", "tree", "violin", "igloo", "key", "house", "nest"],
          "objectColors": ["red umbrella", "blue bicycle"],
          "objectCount": "number of distinct objects",
          "objectPositions": ["top", "bottom", "left", "right", "center", "overlapping"]
        },
        "people": ["boy", "girl", "man", "woman", "child"],
        "animals": ["cat", "dog", "bird", "fish", "horse"],
        "spatialRelationships": {
          "itemsInsideShapes": ["letter F inside red square", "number 17 inside yellow circle"],
          "overlappingItems": ["umbrella overlapping with tree"],
          "relativePositions": ["bicycle left of tree", "key above house"]
        },
        "colorAnalysis": {
          "distinctColors": ["red", "blue", "green", "yellow", "orange", "purple", "pink", "black", "white", "brown", "gray"],
          "colorWordMismatches": ["word 'green' written in red", "word 'blue' written in yellow"],
          "highlightedElements": ["yellow square overlay", "colored border around item"]
        },
        "quantitativeData": {
          "totalItems": "exact count of all distinct visual elements",
          "letterCount": "number of letters present",
          "numberCount": "number of numerical digits",
          "objectCount": "number of real-world objects",
          "shapeCount": "number of geometric shapes"
        },
        "educationalContext": {
          "category": "letters|numbers|shapes|colors|objects|mixed|color-word-mismatch",
          "difficulty": "basic|intermediate|advanced",
          "questionTypes": ["identification", "counting", "color", "position", "relationship", "true-false"]
        }
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

      Logger.info("📤 Sending request to OpenAI Vision API...");
      
      const response = await fetch("https://api.openai.com/v1/chat/completions", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${openaiApiKey}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          model: "gpt-4-turbo",
          messages: [
            {
              role: "user",
              content: [
                { type: "text", text: prompt },
                { type: "image_url", image_url: { url: imageUrl } }
              ]
            }
          ],
          max_tokens: 800
        })
      });

      Logger.info("📥 Vision API response", { status: response.status });

      if (!response.ok) {
        const errorText = await response.text();
        Logger.error("❌ OpenAI Vision API error", { 
          status: response.status, 
          statusText: response.statusText,
          error: errorText,
          imageUrl: imageUrl 
        });
        throw new Error(`OpenAI API error: ${response.status} ${response.statusText} - ${errorText}`);
      }

      const result = await response.json();
      Logger.success("✅ Vision API response received", { tokensUsed: result.usage?.total_tokens || "unknown" });
      return result;
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

        // Supabase client
        const supabase = createClient(supabaseUrl, supabaseKey);
        Logger.success(`✅ Supabase client initialized [${requestId}]`);

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
        
        // Get public URL for database storage
        const publicUrl = supabase.storage.from(bucket).getPublicUrl(newName).data.publicUrl;
        
        // Try to create a signed URL for OpenAI (more secure)
        const { data: signedUrlData, error: signedUrlError } = await supabase.storage
          .from(bucket)
          .createSignedUrl(newName, 60 * 60); // 1 hour for OpenAI processing
        
        let imageUrlForAI = publicUrl; // Default to public URL
        
        if (signedUrlError) {
          Logger.warning("⚠️ Could not create signed URL, using public URL", signedUrlError);
        } else {
          imageUrlForAI = signedUrlData.signedUrl;
          Logger.info("✅ Signed URL created successfully");
        }
        
        Logger.info("🔗 URLs configured", { 
          publicUrl: publicUrl, 
          aiUrl: imageUrlForAI 
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
          Logger.info("📊 URL test result", {
            status: testResponse.status,
            statusText: testResponse.statusText,
            contentType: testResponse.headers.get('content-type'),
            contentLength: testResponse.headers.get('content-length')
          });
          
          if (!testResponse.ok) {
            Logger.warning("⚠️ URL not accessible, trying public URL");
            imageUrlForAI = publicUrl;
          }
        } catch (testError) {
          Logger.warning("⚠️ URL test failed, using public URL", testError);
          imageUrlForAI = publicUrl;
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

        // Analyze image with OpenAI Vision
        try {
          const visionResponse = await analyzeImageWithGPT(imageUrlForAI, openaiApiKey);
          Logger.success(`📊 Vision analysis complete [${requestId}]`);

          const gptContent = visionResponse.choices[0]?.message?.content;
          if (!gptContent) {
            throw new Error("No content in GPT response");
          }

          console.log("📝 GPT response content:", gptContent);

          // Parse the JSON response - handle both pure JSON and markdown-wrapped JSON
          let analysisData;
          try {
            // First try parsing as-is
            analysisData = JSON.parse(gptContent);
          } catch (firstError) {
            // If that fails, try to extract JSON from markdown code blocks
            Logger.warning("⚠️ Initial JSON parse failed, trying to extract from markdown", { error: firstError.message });
            
            // Look for JSON content between ```json and ``` or between ``` and ```
            const jsonMatch = gptContent.match(/```(?:json)?\s*\n?([\s\S]*?)\n?```/);
            if (jsonMatch && jsonMatch[1]) {
              try {
                analysisData = JSON.parse(jsonMatch[1].trim());
                Logger.info("✅ Successfully extracted JSON from markdown");
              } catch (secondError) {
                Logger.error("❌ Failed to parse extracted JSON", { error: secondError.message, extracted: jsonMatch[1] });
                throw new Error(`JSON parsing failed: ${secondError.message}`);
              }
            } else {
              // Try to find any JSON-like content
              const jsonStart = gptContent.indexOf('{');
              const jsonEnd = gptContent.lastIndexOf('}') + 1;
              if (jsonStart !== -1 && jsonEnd > jsonStart) {
                const extractedJson = gptContent.slice(jsonStart, jsonEnd);
                try {
                  analysisData = JSON.parse(extractedJson);
                  Logger.info("✅ Successfully extracted JSON by finding braces");
                } catch (thirdError) {
                  Logger.error("❌ All JSON parsing attempts failed", { 
                    originalError: firstError.message,
                    extractedContent: extractedJson,
                    finalError: thirdError.message 
                  });
                  throw new Error(`Could not parse GPT response as JSON: ${firstError.message}`);
                }
              } else {
                throw new Error(`No valid JSON found in GPT response: ${firstError.message}`);
              }
            }
          }
          
          const description = analysisData.description;
          const tags = analysisData.tags;

          console.log("🏷️ Parsed analysis:", {
            description: description?.substring(0, 100) + "...",
            tagKeys: Object.keys(tags || {})
          });

          // Create embedding text from description and enhanced tags
          const embeddingText = `${description}. 
          Objects: ${tags.objects?.join(', ') || tags.content || ''}. 
          Colors: ${tags.colors?.join(', ') || tags.color || ''}. 
          Setting: ${tags.setting || ''}. 
          Style: ${tags.style || ''}. 
          Mood: ${tags.mood || ''}. 
          Category: ${tags.category || ''}. 
          Text: ${tags.text || ''}`.trim();
          console.log("📄 Embedding text prepared:", embeddingText.substring(0, 150) + "...");
          
          // Generate embedding
          const embedding = await generateEmbedding(embeddingText, openaiApiKey);

          // Update the record with AI-generated data
          console.log("💾 Updating record with AI data...");
          const { error: updateError } = await supabase
            .from("images")
            .update({
              description: description,
              tags: tags,
              raw_json: visionResponse,
              embedding: embedding
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
