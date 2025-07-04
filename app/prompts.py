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

        ---SCRAPED TEXT START---
        {{WEBSITE_SCRAPED_CONTENT}}
        ---SCRAPED TEXT END---
    """ 

def get_faq_prompt():
    return """
        You are an expert site assistant.  

        **Task**  
        Read the text after the marker ---SCRAPED TEXT START--- and craft a JSON object that matches *exactly* the template shown below — no extra keys, no comments.


        ### Response template (fill in where indicated)
        {
        "faqs": [
                {
                    "question": "string",
                    "answer": "string"
                }
                // ← repeat until you have at least 10 items
            ]
        }


        Rules:
        • Provide **at least 10** FAQs that real visitors might ask.  
        • If the site mentions any prices/fees, include **≥ 2** pricing‑related Q&As.  
        • Each answer should be 1‑2 paragraphs, strictly based on the supplied content.  
        • Output JSON only—no markdown or commentary.

        ---SCRAPED TEXT START---
        {{WEBSITE_SCRAPED_CONTENT}}
        ---SCRAPED TEXT END---

    """