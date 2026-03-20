import React from 'react';
import Link from 'next/link';
import { supabase } from '@/lib/supabase';
import { ArrowLeft, ExternalLink, TrendingUp, BookOpen, Target, Users, BarChart3 } from 'lucide-react';
import { cn } from '@/components/ArticleCard';

interface ArticlePageProps {
  params: Promise<{ id: string }>;
}

export default async function ArticlePage({ params }: ArticlePageProps) {
  const { id } = await params;

  // Fetch article metadata
  const { data: article, error: articleError } = await supabase
    .from('articles')
    .select('*')
    .eq('id', id)
    .single();

  if (articleError || !article) {
    return (
      <div className="min-h-screen bg-[#0a0a0a] flex flex-col items-center justify-center p-6 text-center">
        <h1 className="text-2xl font-bold text-white mb-4">Article Intelligence Not Found</h1>
        <p className="text-gray-500 mb-8">The requested article could not be retrieved from our intelligence database.</p>
        <Link href="/" className="px-6 py-3 bg-blue-600 text-white rounded-xl font-bold hover:bg-blue-700 transition-all">
          ← Back to Dashboard
        </Link>
      </div>
    );
  }

  // Fetch article blocks
  const { data: blocks, error: blocksError } = await supabase
    .from('article_blocks')
    .select('*')
    .eq('article_id', id)
    .order('position', { ascending: true });

  const sentimentEmoji = {
    bullish: '🟢 Bullish',
    bearish: '🔴 Bearish',
    neutral: '⚪ Neutral',
  }[article.sentiment?.toLowerCase() || 'neutral'] || '⚪ Neutral';

  return (
    <div className="min-h-screen bg-[#0a0a0a] pb-24">
      {/* Navigation Header */}
      <nav className="sticky top-0 z-50 bg-[#0a0a0a]/80 backdrop-blur-md border-b border-white/5 py-4">
        <div className="max-w-4xl mx-auto px-6 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2 text-sm font-bold text-gray-400 hover:text-white transition-colors">
            <ArrowLeft className="w-4 h-4" />
            Back to Dashboard
          </Link>
          <div className="text-[10px] font-black text-blue-500 uppercase tracking-widest px-3 py-1 bg-blue-500/10 rounded-full border border-blue-500/20">
            {article.source_name}
          </div>
        </div>
      </nav>

      <div className="max-w-4xl mx-auto px-6 pt-12">
        <header className="mb-10">
          <h1 className="text-4xl md:text-5xl font-black text-white leading-tight mb-6">
            {article.title}
          </h1>
          <div className="flex flex-wrap items-center gap-4 text-sm text-gray-500">
            <span className="flex items-center gap-1.5">
              <TrendingUp className="w-4 h-4 text-gray-600" />
              {sentimentEmoji}
            </span>
            <span className="w-1.5 h-1.5 rounded-full bg-gray-800" />
            <div className="flex gap-2">
              {article.genre_tags?.map((tag: string) => (
                <span key={tag} className="px-2 py-0.5 rounded bg-white/5 text-[10px] font-bold uppercase tracking-wider text-blue-400 border border-blue-400/10">
                  {tag}
                </span>
              ))}
            </div>
          </div>
        </header>

        {/* AI Analysis Block */}
        <section className="bg-white rounded-3xl p-8 mb-16 shadow-2xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
            <TrendingUp className="w-24 h-24 text-blue-900" />
          </div>
          
          <div className="flex items-center gap-2 mb-8">
            <div className="p-2 bg-blue-600 rounded-lg">
              <Target className="w-5 h-5 text-white" />
            </div>
            <h2 className="text-xl font-black text-gray-900 tracking-tight italic uppercase">AI Intelligence Brief</h2>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
            {/* Summary & Takeaways */}
            <div className="lg:col-span-8 space-y-8">
              <div>
                <h3 className="text-[10px] uppercase tracking-widest font-black text-blue-600 mb-2">Executive Summary</h3>
                <p className="text-gray-700 leading-relaxed font-medium">
                  {article.ai_summary || "No automated summary generated."}
                </p>
              </div>

              <div>
                <h3 className="text-[10px] uppercase tracking-widest font-black text-blue-600 mb-3">Key Takeaways</h3>
                <ul className="space-y-3">
                  {article.key_takeaways?.map((item: string, idx: number) => (
                    <li key={idx} className="flex gap-3 text-sm text-gray-600 leading-relaxed">
                      <span className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-50 flex items-center justify-center text-[10px] font-black text-blue-600 border border-blue-100 italic">
                        {idx + 1}
                      </span>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Entities Mentioned */}
            <div className="lg:col-span-4 bg-gray-50/50 rounded-2xl p-6 border border-gray-100">
              <h3 className="text-[10px] uppercase tracking-widest font-black text-blue-600 mb-6 flex items-center gap-2">
                <BarChart3 className="w-3 h-3" />
                Entities Mentioned
              </h3>
              
              <div className="space-y-6">
                <div>
                  <div className="flex items-center gap-1.5 text-[10px] font-bold text-gray-400 uppercase mb-2">
                    <BookOpen className="w-3 h-3" /> Games
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {article.entities?.games?.length > 0 ? article.entities.games.map((g: string) => (
                      <span key={g} className="px-2 py-0.5 bg-white border border-gray-100 rounded text-[10px] font-medium text-gray-600">
                        {g}
                      </span>
                    )) : <span className="text-[10px] text-gray-400 italic">None identified</span>}
                  </div>
                </div>

                <div>
                  <div className="flex items-center gap-1.5 text-[10px] font-bold text-gray-400 uppercase mb-2">
                    <Users className="w-3 h-3" /> Studios
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {article.entities?.studios?.length > 0 ? article.entities.studios.map((s: string) => (
                      <span key={s} className="px-2 py-0.5 bg-white border border-gray-100 rounded text-[10px] font-medium text-gray-600">
                        {s}
                      </span>
                    )) : <span className="text-[10px] text-gray-400 italic">None identified</span>}
                  </div>
                </div>

                <div>
                  <div className="flex items-center gap-1.5 text-[10px] font-bold text-gray-400 uppercase mb-2">
                    <TrendingUp className="w-3 h-3" /> Metrics
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {article.entities?.metrics?.length > 0 ? article.entities.metrics.map((m: string) => (
                      <span key={m} className="px-2 py-0.5 bg-white border border-gray-100 rounded text-[10px] font-medium text-gray-600">
                        {m}
                      </span>
                    )) : <span className="text-[10px] text-gray-400 italic">None identified</span>}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Article Body */}
        <article className="prose prose-invert prose-blue max-w-none">
          {blocksError ? (
            <div className="p-10 bg-red-500/10 border border-red-500/20 rounded-2xl text-red-500 text-sm">
              Failed to load article structured content.
            </div>
          ) : (
            <div className="space-y-6">
              {blocks?.map((block) => {
                switch (block.type) {
                  case 'heading1':
                    return <h1 key={block.id} className="text-3xl font-black text-white mt-12 mb-6">{block.content}</h1>;
                  case 'heading2':
                    return <h2 key={block.id} className="text-2xl font-bold text-white mt-10 mb-4">{block.content}</h2>;
                  case 'paragraph':
                    return <p key={block.id} className="text-lg text-gray-400 leading-relaxed mb-6">{block.content}</p>;
                  case 'bullet':
                    return (
                      <ul key={block.id} className="list-disc list-inside space-y-2 mb-6">
                        <li className="text-lg text-gray-400 leading-relaxed">{block.content}</li>
                      </ul>
                    );
                  case 'quote':
                    return (
                      <blockquote key={block.id} className="border-l-4 border-blue-600 pl-6 italic text-xl text-gray-300 my-10 bg-white/5 py-4 rounded-r-xl">
                        {block.content}
                      </blockquote>
                    );
                  case 'image':
                    return (
                      <figure key={block.id} className="my-10">
                        <img 
                          src={block.content} 
                          alt="Article body content" 
                          className="w-full h-auto rounded-3xl shadow-2xl"
                        />
                      </figure>
                    );
                  default:
                    return null;
                }
              })}
            </div>
          )}
        </article>

        <footer className="mt-20 pt-10 border-t border-white/5 text-center">
          <a 
            href={article.original_url} 
            target="_blank" 
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 text-sm font-bold text-blue-500 hover:text-blue-400 transition-colors bg-blue-500/10 px-6 py-3 rounded-xl border border-blue-500/20 shadow-lg shadow-blue-500/10"
          >
            Read original source article on {article.source_name}
            <ExternalLink className="w-4 h-4" />
          </a>
        </footer>
      </div>
    </div>
  );
}
