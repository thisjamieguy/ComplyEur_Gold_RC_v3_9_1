import { StrictMode } from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import "./index.css";
import "./App.css";
import "./ui/calendar-reset.css"; // Phase 3.4 Layout Stabilization
import { CalendarShell } from "./modules/CalendarShell";

const queryClient = new QueryClient();

const rootElement = document.getElementById("maavsi-calendar-root");

if (rootElement) {
  ReactDOM.createRoot(rootElement).render(
    <StrictMode>
      <QueryClientProvider client={queryClient}>
        <CalendarShell />
      </QueryClientProvider>
    </StrictMode>
  );
}