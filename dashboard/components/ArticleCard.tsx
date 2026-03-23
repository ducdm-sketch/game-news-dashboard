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
  };
}

export function ArticleCard({ article }: ArticleCardProps) {
  return (
    <div className="group relative flex flex-col bg-white rounded-xl overflow-hidden shadow-lg hover:shadow-2xl transition-all duration-300 hover:-translate-y-1 cursor-pointer">
      {/* Image Container */}
      <div className="relative h-48 w-full bg-gray-200 overflow-hidden border-b border-gray-100">
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
          <div className="w-full h-full flex items-center justify-center bg-gray-50 text-gray-400">
            <span className="text-sm font-medium">No Image</span>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="p-6 flex flex-col flex-grow">
        <div className="text-[10px] font-black text-blue-600 uppercase tracking-widest mb-3 italic">
          {article.source_name}
        </div>
        
        <h3 className="text-lg font-bold text-gray-900 leading-tight line-clamp-3">
          {article.title}
        </h3>
      </div>
    </div>
  );
}
