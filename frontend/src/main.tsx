import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import App from "./App";
import { AppStateProvider } from "./state/appState";
import "./styles/tokens.css";
import "./styles/app.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <AppStateProvider>
      <App />
    </AppStateProvider>
  </StrictMode>,
);
