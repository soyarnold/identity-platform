import { BrowserRouter, Link, Route, Routes } from "react-router-dom";
import { CallbackPage } from "./pages/CallbackPage";
import { HomePage } from "./pages/HomePage";

export default function App() {
  return (
    <BrowserRouter>
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
