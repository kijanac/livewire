import { useState } from "react";
import type { BillFilters, City } from "../types";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { formatTopic } from "@/lib/bill-utils";

interface FiltersProps {
  filters: BillFilters;
  cities: City[];
  topics: string[];
  onChange: (filters: BillFilters) => void;
}

const COMMON_STATUSES = [
  "Adopted",
  "Approved",
  "Committee",
  "Enacted",
  "Failed",
  "Filed",
  "Hearing Scheduled",
  "Introduced",
  "Passed",
  "Pending",
  "Referred",
  "Signed",
  "Vetoed",
  "Withdrawn",
];

const COMMON_TYPES = [
  "Ordinance",
  "Resolution",
  "Communication",
  "Report",
  "Motion",
  "Order",
  "Petition",
  "Proclamation",
  "Executive Order",
  "Local Law",
];

const CLEAR = "__clear__";

/**
 * Resettable select wrapper. Uses key-change strategy to force remount
 * when value is cleared, which resets Base UI Select back to placeholder.
 */
function FilterSelect({
  value,
  onValueChange,
  placeholder,
  children,
}: {
  value: string;
  onValueChange: (val: string) => void;
  placeholder: string;
  children: React.ReactNode;
}) {
  // Key includes the "empty" state so clearing forces a remount
  const isEmpty = !value;
  const selectKey = isEmpty ? `${placeholder}-empty` : `${placeholder}-set`;

  return (
    <Select
      key={selectKey}
      value={value || undefined}
      onValueChange={(val) => onValueChange(val === CLEAR ? "" : (val ?? ""))}
    >
      <SelectTrigger>
        <SelectValue placeholder={placeholder} />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={CLEAR}>{placeholder}</SelectItem>
        {children}
      </SelectContent>
    </Select>
  );
}

function Filters({ filters, cities, topics, onChange }: FiltersProps) {
  const [showMore, setShowMore] = useState(false);

  const update = (field: keyof BillFilters, value: string) => {
    onChange({ ...filters, [field]: value });
  };

  const moreFiltersActive =
    !!filters.status || !!filters.type_name || !!filters.urgency;

  return (
    <div className="mb-6 space-y-2">
      {/* Primary filters: search, city, issue — always visible */}
      <div className="flex flex-wrap gap-2 sm:gap-3">
        <div className="relative flex-1 min-w-[180px]">
          <svg
            className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground z-10"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth="2"
            stroke="currentColor"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z"
            />
          </svg>
          <Input
            type="text"
            value={filters.search}
            onChange={(e) => update("search", e.target.value)}
            placeholder="Search by keyword..."
            className="w-full pl-9"
          />
        </div>

        <FilterSelect
          value={filters.city}
          onValueChange={(val) => update("city", val)}
          placeholder="Any City"
        >
          {cities.map((city) => (
            <SelectItem key={city.id} value={city.id}>
              {city.name}, {city.state}
            </SelectItem>
          ))}
        </FilterSelect>

        <FilterSelect
          value={filters.topic}
          onValueChange={(val) => update("topic", val)}
          placeholder="Any Issue"
        >
          {topics.map((topic) => (
            <SelectItem key={topic} value={topic}>
              {formatTopic(topic)}
            </SelectItem>
          ))}
        </FilterSelect>

        <Button
          variant={showMore || moreFiltersActive ? "secondary" : "outline"}
          size="default"
          onClick={() => setShowMore(!showMore)}
          className="gap-1"
        >
          <svg
            className="h-4 w-4"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth="2"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M10.5 6h9.75M10.5 6a1.5 1.5 0 1 1-3 0m3 0a1.5 1.5 0 1 0-3 0M3.75 6H7.5m3 12h9.75m-9.75 0a1.5 1.5 0 0 1-3 0m3 0a1.5 1.5 0 0 0-3 0m-3.75 0H7.5m9-6h3.75m-3.75 0a1.5 1.5 0 0 1-3 0m3 0a1.5 1.5 0 0 0-3 0m-9.75 0h9.75"
            />
          </svg>
          Filters
          {moreFiltersActive && (
            <span className="ml-0.5 inline-flex items-center justify-center w-4 h-4 text-[10px] font-bold rounded-full bg-primary text-primary-foreground">
              {[filters.status, filters.type_name, filters.urgency].filter(Boolean).length}
            </span>
          )}
        </Button>
      </div>

      {/* Secondary filters: status, type, urgency — toggleable */}
      {showMore && (
        <div className="flex flex-wrap gap-2 sm:gap-3">
          <FilterSelect
            value={filters.status}
            onValueChange={(val) => update("status", val)}
            placeholder="Any Status"
          >
            {COMMON_STATUSES.map((status) => (
              <SelectItem key={status} value={status}>
                {status}
              </SelectItem>
            ))}
          </FilterSelect>

          <FilterSelect
            value={filters.type_name}
            onValueChange={(val) => update("type_name", val)}
            placeholder="Any Type"
          >
            {COMMON_TYPES.map((type) => (
              <SelectItem key={type} value={type}>
                {type}
              </SelectItem>
            ))}
          </FilterSelect>

          <FilterSelect
            value={filters.urgency}
            onValueChange={(val) => update("urgency", val)}
            placeholder="Any Timeline"
          >
            <SelectItem value="urgent">This Week</SelectItem>
            <SelectItem value="soon">This Month</SelectItem>
          </FilterSelect>
        </div>
      )}
    </div>
  );
}

export default Filters;
