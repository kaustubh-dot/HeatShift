import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import App from "./App";
import { AppStateProvider } from "./state/appState";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <AppStateProvider>
      <App />
    </AppStateProvider>
  </StrictMode>,
);
