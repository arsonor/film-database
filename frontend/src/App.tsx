import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AddFilmPage } from "@/pages/AddFilmPage";
import { BrowsePage } from "@/pages/BrowsePage";
import { FilmDetailPage } from "@/pages/FilmDetailPage";
import { TaxonomyAdminPage } from "@/pages/TaxonomyAdminPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/browse" replace />} />
        <Route path="/browse" element={<BrowsePage />} />
        <Route path="/films/:id" element={<FilmDetailPage />} />
        <Route path="/add" element={<AddFilmPage />} />
        <Route path="/admin/taxonomy" element={<TaxonomyAdminPage />} />
      </Routes>
    </BrowserRouter>
  );
}
