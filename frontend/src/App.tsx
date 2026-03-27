import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AddFilmPage } from "@/pages/AddFilmPage";
import { BrowsePage } from "@/pages/BrowsePage";
import { FilmDetailPage } from "@/pages/FilmDetailPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/browse" replace />} />
        <Route path="/browse" element={<BrowsePage />} />
        <Route path="/films/:id" element={<FilmDetailPage />} />
        <Route path="/add" element={<AddFilmPage />} />
      </Routes>
    </BrowserRouter>
  );
}
