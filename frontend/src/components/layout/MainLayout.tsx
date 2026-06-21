import { Box } from "@mui/material";

export default function MainLayout({ children }: { children: React.ReactNode }) {
  return (
    <Box sx={{ display: "flex", height: "100vh" }}>
      
      {/* Sidebar */}
      <Box
        sx={{
          width: 260,
          borderRight: "1px solid #e0e0e0",
          p: 2
        }}
      >
        <h3>Chat History</h3>
      </Box>

      {/* Main area */}
      <Box sx={{ flex: 1, display: "flex", flexDirection: "column" }}>
        {children}
      </Box>

    </Box>
  );
}