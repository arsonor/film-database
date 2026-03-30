import { useState, useEffect } from "react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { Header } from "./Header";
import { SidebarContent } from "./Sidebar";
import { fetchTaxonomy } from "@/api/client";
import type {
  ArrayFilterKey,
  FilterState,
  TaxonomyItem,
} from "@/types/api";

interface LayoutProps {
  filters: FilterState;
  totalFilms: number | null;
  taxonomies: Record<string, TaxonomyItem[]>;
  onSearchChange: (q: string) => void;
  onSortChange: (
    sortBy: FilterState["sort_by"],
    sortOrder: FilterState["sort_order"],
  ) => void;
  onToggleFilter: (dimension: ArrayFilterKey, value: string) => void;
  onUpdateFilters: (updates: Partial<FilterState>) => void;
  onSetVu: (vu: boolean | null) => void;
  children: React.ReactNode;
}

export function Layout({
  filters,
  totalFilms,
  taxonomies,
  onSearchChange,
  onSortChange,
  onToggleFilter,
  onUpdateFilters,
  onSetVu,
  children,
}: LayoutProps) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [languages, setLanguages] = useState<TaxonomyItem[]>([]);

  // Fetch languages once
  useEffect(() => {
    fetchTaxonomy("languages").then((data) => setLanguages(data.items)).catch(() => {});
  }, []);

  const sidebarProps = {
    filters,
    taxonomies,
    languages,
    onToggleFilter,
    onUpdateFilters,
    onSetVu,
  };

  return (
    <div className="flex h-screen flex-col">
      <Header
        filters={filters}
        totalFilms={totalFilms}
        onSearchChange={onSearchChange}
        onSortChange={onSortChange}
        onOpenMobileFilters={() => setMobileOpen(true)}
        sidebarCollapsed={sidebarCollapsed}
        onToggleSidebar={() => setSidebarCollapsed((v) => !v)}
      />

      <div className="flex flex-1 overflow-hidden">
        {/* Desktop sidebar */}
        <aside
          className={`hidden shrink-0 border-r border-border bg-sidebar-background transition-[width] duration-300 lg:block ${
            sidebarCollapsed ? "w-0 overflow-hidden border-r-0" : "w-72"
          }`}
        >
          <SidebarContent {...sidebarProps} />
        </aside>

        {/* Mobile sidebar (Sheet) */}
        <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
          <SheetContent side="left" className="w-80 p-0">
            <SheetHeader className="p-4 pb-0">
              <SheetTitle>Filters</SheetTitle>
              <SheetDescription className="sr-only">
                Filter films by taxonomy dimensions
              </SheetDescription>
            </SheetHeader>
            <SidebarContent {...sidebarProps} />
          </SheetContent>
        </Sheet>

        {/* Main content */}
        <main className="flex-1 overflow-y-auto p-4 lg:p-6">{children}</main>
      </div>
    </div>
  );
}
