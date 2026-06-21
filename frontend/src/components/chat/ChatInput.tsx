import { useState } from "react";
import { Box, TextField, Button } from "@mui/material";

export default function ChatInput({
  onSend,
}: {
  onSend: (text: string) => void;
}) {
  const [text, setText] = useState("");

  const handleSend = () => {
    if (!text.trim()) return;
    onSend(text);
    setText("");
  };

  return (
    <Box
      sx={{
        display: "flex",
        gap: 1,
        padding: 2,
        borderTop: "1px solid #e0e0e0",
      }}
    >
      <TextField
        fullWidth
        size="small"
        placeholder="Ask something..."
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && handleSend()}
      />    

      <Button variant="contained" onClick={handleSend}>
        Send
      </Button>
    </Box>
  );
}