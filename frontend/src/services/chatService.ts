import type { ChatResponse } from "../types/chatResponse";

export async function sendMessage(message: string): Promise<ChatResponse> {

    console.log("User:", message);

    await new Promise(resolve => setTimeout(resolve, 1000));
    return {
        content: `
# AI Response

You asked:

> ${message}

This is a **mock response**.

Later this response will come from the backend.

\`\`\`python
print("Hello from AI")
\`\`\`
`,
        "sources": [
            {
                "documentName": "system-design.pdf",
                "pageNumber": 42
            }
        ]
    }
}