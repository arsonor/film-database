import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowDownAZ,
  ArrowUpAZ,
  Film,
  Filter,
  PanelLeftClose,
  PanelLeftOpen,
  Plus,
  Search,
  Tags,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { FilterState } from "@/types/api";

interface HeaderProps {
  filters: FilterState;
  totalFilms: number | null;
  onSearchChange: (q: string) => void;
  onSortChange: (
    sortBy: FilterState["sort_by"],
    sortOrder: FilterState["sort_order"],
  ) => void;
  onOpenMobileFilters: () => void;
  sidebarCollapsed?: boolean;
  onToggleSidebar?: () => void;
}

export function Header({
  filters,
  totalFilms,
  onSearchChange,
  onSortChange,
  onOpenMobileFilters,
  sidebarCollapsed,
  onToggleSidebar,
}: HeaderProps) {
  const navigate = useNavigate();
  const [searchInput, setSearchInput] = useState(filters.q);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>();

  useEffect(() => {
    setSearchInput(filters.q);
  }, [filters.q]);

  const handleSearchInput = useCallback(
    (value: string) => {
      setSearchInput(value);
      clearTimeout(debounceRef.current);
      debounceRef.current = setTimeout(() => {
        onSearchChange(value);
      }, 300);
    },
    [onSearchChange],
  );

  const clearSearch = useCallback(() => {
    setSearchInput("");
    onSearchChange("");
  }, [onSearchChange]);

  return (
    <header className="sticky top-0 z-40 flex h-16 items-center gap-4 border-b border-border bg-background/95 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/60 lg:px-6">
      {/* Left: Title + sidebar toggle */}
      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="icon"
          className="lg:hidden"
          onClick={onOpenMobileFilters}
        >
          <Filter className="h-5 w-5" />
        </Button>
        {onToggleSidebar && (
          <Button
            variant="ghost"
            size="icon"
            className="hidden lg:inline-flex"
            onClick={onToggleSidebar}
            title={sidebarCollapsed ? "Show filters" : "Hide filters"}
          >
            {sidebarCollapsed ? (
              <PanelLeftOpen className="h-5 w-5" />
            ) : (
              <PanelLeftClose className="h-5 w-5" />
            )}
          </Button>
        )}
        <div className="flex items-center gap-2">
          <Film className="h-5 w-5 text-primary" />
          <h1 className="hidden text-lg font-semibold sm:block">Film Database</h1>
        </div>
        {totalFilms !== null && (
          <span className="hidden rounded-md bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground sm:inline-flex">
            {totalFilms} films
          </span>
        )}
      </div>

      {/* Center: Search */}
      <div className="relative mx-auto w-full max-w-md">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          value={searchInput}
          onChange={(e) => handleSearchInput(e.target.value)}
          placeholder="Search films, directors, actors..."
          className="h-9 pl-9 pr-8"
        />
        {searchInput && (
          <button
            onClick={clearSearch}
            className="absolute right-2 top-1/2 -translate-y-1/2 rounded-sm p-0.5 text-muted-foreground hover:text-foreground"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Right: Add + Sort */}
      <div className="hidden items-center gap-2 sm:flex">
        <Button
          variant="outline"
          size="sm"
          className="gap-1.5"
          onClick={() => navigate("/add")}
        >
          <Plus className="h-4 w-4" />
          <span className="hidden lg:inline">Add Film</span>
        </Button>
        <Button
          variant="ghost"
          size="sm"
          className="gap-1.5"
          onClick={() => navigate("/admin/taxonomy")}
          title="Manage Taxonomy"
        >
          <Tags className="h-4 w-4" />
        </Button>
        <Select
          value={filters.sort_by}
          onValueChange={(val) =>
            onSortChange(val as FilterState["sort_by"], filters.sort_order)
          }
        >
          <SelectTrigger className="h-9 w-28 text-xs">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="year">Year</SelectItem>
            <SelectItem value="title">Title</SelectItem>
            <SelectItem value="duration">Duration</SelectItem>
          </SelectContent>
        </Select>

        <Button
          variant="ghost"
          size="icon"
          onClick={() =>
            onSortChange(
              filters.sort_by,
              filters.sort_order === "asc" ? "desc" : "asc",
            )
          }
          title={filters.sort_order === "asc" ? "Ascending" : "Descending"}
        >
          {filters.sort_order === "asc" ? (
            <ArrowUpAZ className="h-4 w-4" />
          ) : (
            <ArrowDownAZ className="h-4 w-4" />
          )}
        </Button>
      </div>
    </header>
  );
}
