import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "@/context/AuthContext";
import { AddFilmPage } from "@/pages/AddFilmPage";
import { BrowsePage } from "@/pages/BrowsePage";
import { FilmDetailPage } from "@/pages/FilmDetailPage";
import { AuthPage } from "@/pages/AuthPage";
import { CollectionPage } from "@/pages/CollectionPage";
import { ChainItPage } from "@/pages/ChainItPage";
import { GameHubPage } from "@/pages/GameHubPage";
import { GameStatsPage } from "@/pages/GameStatsPage";
import { TagItPage } from "@/pages/TagItPage";
import { StatsPage } from "@/pages/StatsPage";
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
            <Route path="/stats" element={<StatsPage />} />
            <Route path="/game" element={<GameHubPage />} />
            <Route path="/game/tag-it" element={<TagItPage />} />
            <Route path="/game/chain-it" element={<ChainItPage />} />
            <Route path="/game/stats" element={<GameStatsPage />} />
            <Route path="/admin/taxonomy" element={<TaxonomyAdminPage />} />
            <Route path="/auth" element={<AuthPage />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
