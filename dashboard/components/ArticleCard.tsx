import React from 'react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/** Utility for merging tailwind classes safely */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface ArticleCardProps {
  article: {
    id: string;
    title: string;
    source_name: string;
    cover_image_url: string | null;
    ai_summary: string | null;
    sentiment: string | null;
    genre_tags: string[] | null;
  };
}

export function ArticleCard({ article }: ArticleCardProps) {
  const sentimentEmoji = {
    bullish: '🟢 Bullish',
    bearish: '🔴 Bearish',
    neutral: '⚪ Neutral',
  }[article.sentiment?.toLowerCase() || 'neutral'] || '⚪ Neutral';

  return (
    <div className="group relative flex flex-col bg-white rounded-xl overflow-hidden shadow-lg hover:shadow-2xl transition-all duration-300 hover:-translate-y-1 cursor-pointer">
      {/* Image Container */}
      <div className="relative h-48 w-full bg-gray-200 overflow-hidden">
        {article.cover_image_url ? (
          <img
            src={article.cover_image_url}
            alt={article.title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
            onError={(e) => {
              (e.target as HTMLImageElement).src = 'https://via.placeholder.com/400x200?text=No+Image';
            }}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-gray-100 text-gray-400">
            <span className="text-sm font-medium">No Image</span>
          </div>
        )}
        
        {/* Sentiment Badge on Image */}
        <div className="absolute top-3 right-3">
          <span className={cn(
            "px-2 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider backdrop-blur-md shadow-sm border",
            article.sentiment?.toLowerCase() === 'bullish' ? "bg-green-500/10 text-green-600 border-green-500/20" :
            article.sentiment?.toLowerCase() === 'bearish' ? "bg-red-500/10 text-red-600 border-red-500/20" :
            "bg-gray-500/10 text-gray-600 border-gray-500/20"
          )}>
            {sentimentEmoji}
          </span>
        </div>
      </div>

      {/* Content */}
      <div className="p-5 flex flex-col flex-grow">
        <div className="text-[10px] font-bold text-blue-600 uppercase tracking-widest mb-2">
          {article.source_name}
        </div>
        
        <h3 className="text-lg font-bold text-gray-900 leading-tight mb-3 line-clamp-2 min-h-[3rem]">
          {article.title}
        </h3>
        
        <p className="text-sm text-gray-500 line-clamp-2 mb-4 italic">
          "{article.ai_summary || "No summary available."}"
        </p>

        {/* Tags */}
        <div className="mt-auto flex flex-wrap gap-1.5">
          {article.genre_tags?.slice(0, 3).map((tag) => (
            <span 
              key={tag}
              className="px-2 py-0.5 rounded-md bg-gray-100 text-gray-600 text-[10px] font-medium"
            >
              #{tag}
            </span>
          ))}
          {(article.genre_tags?.length || 0) > 3 && (
            <span className="text-[10px] text-gray-400 self-center font-medium">
              +{(article.genre_tags?.length || 0) - 3} more
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
