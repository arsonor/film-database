import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "@/context/AuthContext";
import { AddFilmPage } from "@/pages/AddFilmPage";
import { BrowsePage } from "@/pages/BrowsePage";
import { FilmDetailPage } from "@/pages/FilmDetailPage";
import { AuthPage } from "@/pages/AuthPage";
import { CollectionPage } from "@/pages/CollectionPage";
import { TaxonomyAdminPage } from "@/pages/TaxonomyAdminPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30 * 1000,
      gcTime: 5 * 60 * 1000,
      refetchOnWindowFocus: false,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/" element={<Navigate to="/browse" replace />} />
            <Route path="/browse" element={<BrowsePage />} />
            <Route path="/films/:id" element={<FilmDetailPage />} />
            <Route path="/add" element={<AddFilmPage />} />
            <Route path="/collection" element={<CollectionPage />} />
            <Route path="/admin/taxonomy" element={<TaxonomyAdminPage />} />
            <Route path="/auth" element={<AuthPage />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
