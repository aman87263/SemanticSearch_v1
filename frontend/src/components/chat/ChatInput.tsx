import { useState } from "react";
import { Box, TextField, IconButton } from "@mui/material";
import SendIcon from "@mui/icons-material/Send";

export default function ChatInput({
  onSend,
  disabled = false,
}: {
  onSend: (text: string) => Promise<void>;
  disabled?: boolean;
}) {
  const [text, setText] = useState("");

  const handleSend = () => {
    if (!text.trim()) return;
    void onSend(text);
    setText("");
  };

  return (
    <Box
      sx={{
        display: "flex",
        gap: 1,
        p: 2,
        borderTop: "1px solid #e0e0e0",
        bgcolor: "white",
      }}
    >
      <TextField
        fullWidth
        size="small"
        placeholder="Message..."
        value={text}
        disabled={disabled}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
          }
        }}
      />

      <IconButton onClick={handleSend} color="primary" disabled={disabled}>
        <SendIcon />
      </IconButton>
    </Box>
  );
}
