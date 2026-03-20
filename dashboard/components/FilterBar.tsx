import React from 'react';

interface FilterBarProps {
  sources: string[];
  tags: string[];
  activeFilters: {
    source: string;
    sentiment: string;
    tag: string;
    dateFrom: string;
    dateTo: string;
  };
  onFilterChange: (name: string, value: string) => void;
}

export function FilterBar({ sources, tags, activeFilters, onFilterChange }: FilterBarProps) {
  return (
    <div className="bg-[#111] border border-[#222] rounded-2xl p-6 mb-10 shadow-2xl">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
        {/* Source Filter */}
        <div className="flex flex-col gap-2">
          <label className="text-[10px] uppercase tracking-widest font-bold text-gray-500">Source</label>
          <select 
            value={activeFilters.source}
            onChange={(e) => onFilterChange('source', e.target.value)}
            className="bg-[#1a1a1a] border border-[#333] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all font-medium"
          >
            <option value="All">All Sources</option>
            {sources.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>

        {/* Sentiment Filter */}
        <div className="flex flex-col gap-2">
          <label className="text-[10px] uppercase tracking-widest font-bold text-gray-500">Sentiment</label>
          <select 
            value={activeFilters.sentiment}
            onChange={(e) => onFilterChange('sentiment', e.target.value)}
            className="bg-[#1a1a1a] border border-[#333] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all font-medium"
          >
            <option value="All">All Sentiments</option>
            <option value="Bullish">Bullish</option>
            <option value="Bearish">Bearish</option>
            <option value="Neutral">Neutral</option>
          </select>
        </div>

        {/* Tag Filter */}
        <div className="flex flex-col gap-2">
          <label className="text-[10px] uppercase tracking-widest font-bold text-gray-500">Genre Tag</label>
          <select 
            value={activeFilters.tag}
            onChange={(e) => onFilterChange('tag', e.target.value)}
            className="bg-[#1a1a1a] border border-[#333] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all font-medium"
          >
            <option value="All">All Tags</option>
            {tags.map(t => <option key={t} value={t}>#{t}</option>)}
          </select>
        </div>

        {/* Date From */}
        <div className="flex flex-col gap-2">
          <label className="text-[10px] uppercase tracking-widest font-bold text-gray-500">From Date</label>
          <input 
            type="date"
            value={activeFilters.dateFrom}
            onChange={(e) => onFilterChange('dateFrom', e.target.value)}
            className="bg-[#1a1a1a] border border-[#333] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all [color-scheme:dark]"
          />
        </div>

        {/* Date To */}
        <div className="flex flex-col gap-2">
          <label className="text-[10px] uppercase tracking-widest font-bold text-gray-500">To Date</label>
          <input 
            type="date"
            value={activeFilters.dateTo}
            onChange={(e) => onFilterChange('dateTo', e.target.value)}
            className="bg-[#1a1a1a] border border-[#333] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all [color-scheme:dark]"
          />
        </div>
      </div>
    </div>
  );
}
