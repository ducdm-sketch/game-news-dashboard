'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { supabase } from '@/lib/supabase';
import { ArticleCard } from '@/components/ArticleCard';
import { FilterBar } from '@/components/FilterBar';
import { Loader2, TrendingUp, Newspaper, Search } from 'lucide-react';

export default function DashboardPage() {
  const [articles, setArticles] = useState<any[]>([]);
  const [filteredArticles, setFilteredArticles] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [sources, setSources] = useState<string[]>([]);
  const [tags, setTags] = useState<string[]>([]);

  const [filters, setFilters] = useState({
    source: 'All',
    dateFrom: '',
    dateTo: '',
  });

  useEffect(() => {
    async function fetchData() {
      try {
        const { data, error } = await supabase
          .from('articles')
          .select('*')
          .order('crawled_date', { ascending: false });

        if (error) throw error;

        if (data) {
          setArticles(data);
          setFilteredArticles(data);
          
          // Extract unique sources for filter dropdown
          const uniqueSources = Array.from(new Set(data.map((a: any) => a.source_name))).sort();
          setSources(uniqueSources);
        }
      } catch (err) {
        console.error('Error fetching articles:', err);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  useEffect(() => {
    let result = [...articles];

    if (filters.source !== 'All') {
      result = result.filter(a => a.source_name === filters.source);
    }


    if (filters.dateFrom) {
      result = result.filter(a => new Date(a.crawled_date) >= new Date(filters.dateFrom));
    }

    if (filters.dateTo) {
      result = result.filter(a => new Date(a.crawled_date) <= new Date(filters.dateTo));
    }

    setFilteredArticles(result);
  }, [filters, articles]);

  const handleFilterChange = (name: string, value: string) => {
    setFilters(prev => ({ ...prev, [name]: value }));
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Header Section */}
      <header className="mb-12">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-blue-600 rounded-lg shadow-lg shadow-blue-600/20">
            <Newspaper className="text-white w-6 h-6" />
          </div>
          <h1 className="text-3xl font-black text-white tracking-tight">
            Game News <span className="text-blue-500 underline decoration-blue-500/30 underline-offset-8">Tracker</span>
          </h1>
        </div>
        <p className="text-gray-400 max-w-2xl leading-relaxed">
          Real-time discovery of the mobile gaming market. Stay ahead with 
          centralized coverage across all major industry sources.
        </p>
      </header>

      {/* Stats Quick View (Wow factor) */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-12">
        <div className="bg-[#111] border border-blue-500/20 p-6 rounded-2xl flex items-center justify-between">
          <div>
            <div className="text-[10px] uppercase tracking-widest font-black text-gray-500 mb-1">Total Coverage</div>
            <div className="text-2xl font-bold text-white">{articles.length} <span className="text-sm font-medium text-gray-400">articles</span></div>
          </div>
          <Search className="text-blue-500 w-8 h-8 opacity-20" />
        </div>
        <div className="bg-[#111] border border-orange-500/20 p-6 rounded-2xl flex items-center justify-between">
          <div>
            <div className="text-[10px] uppercase tracking-widest font-black text-gray-500 mb-1">Active Sources</div>
            <div className="text-2xl font-bold text-orange-500">{sources.length} <span className="text-sm font-medium text-gray-400">monitored</span></div>
          </div>
          <Newspaper className="text-orange-500 w-8 h-8 opacity-20" />
        </div>
      </div>

      <FilterBar 
        sources={sources} 
        activeFilters={filters} 
        onFilterChange={handleFilterChange} 
      />

      {loading ? (
        <div className="flex flex-col items-center justify-center py-24 gap-4">
          <Loader2 className="w-12 h-12 text-blue-600 animate-spin" />
          <p className="text-gray-500 font-medium tracking-wide">Syncing latest intelligence...</p>
        </div>
      ) : filteredArticles.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
          {filteredArticles.map((article) => (
            <a 
              key={article.id} 
              href={article.original_url} 
              target="_blank" 
              rel="noopener noreferrer"
              className="block"
            >
              <ArticleCard article={article} />
            </a>
          ))}
        </div>
      ) : (
        <div className="bg-[#111] rounded-3xl p-20 text-center border border-dashed border-gray-800">
          <div className="inline-block p-4 bg-gray-900 rounded-full mb-6">
            <Search className="w-8 h-8 text-gray-700" />
          </div>
          <h3 className="text-xl font-bold text-white mb-2">No intelligence found</h3>
          <p className="text-gray-500 max-w-xs mx-auto">
            Try adjusting your filters or search criteria to explore more industry signals.
          </p>
        </div>
      )}
    </div>
  );
}
