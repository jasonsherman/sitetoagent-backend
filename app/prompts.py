def get_analysis_prompt():
    return """
        You are a meticulous web‑content analyst. 
        Read the text after the line `---SCRAPED TEXT START---` and do **not** copy that text verbatim.
        Instead, fill the following JSON schema **exactly** (no extra keys, no comments):

        {
            "type": "object",
            "title": "Website",
            "properties": {
                "businessOverview":        { "type": "string" },
                "uniqueSellingPoints":     { "type": "array",  "items": { "type": "string" } },
                "servicesProducts":        { "type": "array",  "items": { "type": "string" } },
                "brandVoice":              { "type": "string" },
                "valuePropositions":       { "type": "array",  "items": { "type": "string" } },

                "providedServicesProducts":{ "type": "string",
                                            "description": "Two or more paragraphs answering: What services or products does your business provide?" },
                "competitiveDifference":   { "type": "string",
                                            "description": "Two or more paragraphs answering: How are you different from your competitors?" },
                "mostProfitableLineItems": { "type": "string",
                                            "description": "Two or more paragraphs answering: What are your most profitable line items?" },

                "bestSalesLines":          { "type": "array",   "items": { "type": "string" } },

                "greetings": {
                    "type": "array",
                    "items": { "type": "string" },
                    "description": "Five friendly welcome messages, each ending with a question to spark conversation. Feel free to use ${domain} as a placeholder."
                }

            },
            "required": [
                "businessOverview",
                "uniqueSellingPoints",
                "servicesProducts",
                "brandVoice",
                "valuePropositions",
                "providedServicesProducts",
                "competitiveDifference",
                "mostProfitableLineItems",
                "bestSalesLines",
                "greetings"
            ]
        }

        Rules:
        * Output **only** valid JSON (no markdown fencing, no explanatory prose).
        * Each array must have **exactly 5 elements** where the schema calls for 5.
        * For providedServicesProducts, competitiveDifference, and mostProfitableLineItems  
            – write **at least two paragraphs**, separated by a blank line, max three sentences each. 
        * For greetings
            – provide five concise, friendly welcome lines (1 – 2 sentences each),  
            – you *may* insert **${domain}** anywhere to reference the site dynamically. 
        * If the answer is unknown, output an empty string (`""`) or an empty array (`[]`) as appropriate.
        * For faqs
            – generate **≥ 10** question–answer pairs the average visitor might ask.  
            – If any pricing info is present on the page, include **at least two** pricing‑related Q&As.  
            – Each answer 1‑2 short paragraphs, grounded in the scraped text (no wild guesses).
        * Think step by step, but at the end, return only the final answer prefixed with MyResponse:

        ---SCRAPED TEXT START---
        {{WEBSITE_SCRAPED_CONTENT}}
        ---SCRAPED TEXT END---
    """ 

def get_faq_prompt():
    return """
        You are an expert site assistant.  
        Read the text after the line `---SCRAPED TEXT START---` and do **not** copy that text verbatim.
        Instead, fill the following JSON schema **exactly** (no extra keys, no comments):

        {
            "type": "object",
            "properties": {
                "faqs": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "question": { "type": "string" },
                            "answer": { "type": "string" }
                        }
                    }
                }
            }
        }


        Rules:
        • Provide **at least 10** FAQs that real visitors might ask.  
        • If prices or fees appear in the text, include **at least two** pricing‑related questions.  
        • Each answer should be 1‑2 paragraphs, strictly based on the supplied content.  
        • Output JSON only—no markdown or commentary.
        • Think step by step, but at the end, return only the final answer prefixed with MyResponse:

        ---SCRAPED TEXT START---
        {{WEBSITE_SCRAPED_CONTENT}}
        ---SCRAPED TEXT END---

    """