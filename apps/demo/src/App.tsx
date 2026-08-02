import { BrowserRouter, Link, Route, Routes } from "react-router-dom";
import { CallbackPage } from "./pages/CallbackPage";
import { HomePage } from "./pages/HomePage";

const basename =
  import.meta.env.BASE_URL === "/"
    ? undefined
    : import.meta.env.BASE_URL.replace(/\/$/, "");

export default function App() {
  return (
    <BrowserRouter basename={basename}>
      <div className="shell">
        <header className="topbar">
          <Link to="/" className="brand">
            Fieldkit
          </Link>
        </header>
        <main className="main">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/callback" element={<CallbackPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
