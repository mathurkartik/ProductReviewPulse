"use client";

import React, { useState, useEffect } from 'react';

interface Theme {
  id: string;
  rank: number;
  label: string;
  description: string;
  sentiment: 'negative' | 'mixed' | 'positive';
  review_count: number;
}

interface Quote {
  text: str;
  rating: number;
  source: string;
}

interface PulseData {
  run_id: string;
  product: string;
  iso_week: string;
  status: string;
  window: { start: string; end: string };
  themes: Theme[];
  quotes: Quote[];
}

export default function Dashboard() {
  const [data, setData] = useState<PulseData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const res = await fetch(`${apiUrl}/api/pulse/latest`);
        if (!res.ok) throw new Error(`Failed to fetch: ${res.statusText}`);
        const json = await res.json();
        setData(json);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) return <div className="loading-state">Loading latest pulse report...</div>;
  if (error) return <div className="error-state">Error: {error}. Make sure your Render API is live.</div>;
  if (!data) return <div className="empty-state">No pulse data found.</div>;

  return (
    <div>
      {/* Top Navigation Bar */}
      <header className="top-nav">
        <div className="top-nav-left">
          <div className="logo">FinPulse <span>Analytics</span></div>
          <nav className="top-links">
            <a href="#" className="active">Reports</a>
            <a href="#">Dashboard</a>
          </nav>
        </div>
        <div className="top-nav-right">
          <button className="icon-btn">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg>
          </button>
          <div className="profile-avatar">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
          </div>
        </div>
      </header>

      <div className="app-container">
        {/* Sidebar */}
        <aside className="sidebar">
          <div className="sidebar-header">
            <h2>FinPulse</h2>
            <span className="subtitle">INTERNAL REVIEW TOOL</span>
          </div>
          
          <nav className="side-nav">
            <a href="#" className="nav-item">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>
              Dashboard
            </a>
            <a href="#" className="nav-item active">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
              Reports
            </a>
            <a href="#" className="nav-item">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>
              Sentiment Analysis
            </a>
            <a href="#" className="nav-item">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
              Settings
            </a>
          </nav>

          <div className="sidebar-footer">
            <a href="#" className="nav-item">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
              Help Center
            </a>
          </div>
        </aside>

        {/* Main Content */}
        <main className="main-content">
          
          {/* Page Header */}
          <div className="page-header">
            <div className="header-titles">
              <h1>{data.product} — Weekly Review Pulse</h1>
              <div className="header-meta">
                <span className="badge">WEEK: {data.iso_week}</span>
                <span className="period">Period: {data.window.start} to {data.window.end}</span>
              </div>
            </div>
            <div className="header-actions">
              <button className="btn btn-primary">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                Export PDF
              </button>
              <button className="btn btn-outline">Share Link</button>
            </div>
          </div>

          {/* Top Grid Layout */}
          <div className="grid-layout-top">
            
            {/* Top Themes Card */}
            <div className="card themes-card">
              <div className="card-header">
                <h3>Top Themes</h3>
                <span className="card-subtitle">AGGREGATED SENTIMENT</span>
              </div>
              <div className="themes-list">
                {data.themes.map((theme) => (
                  <div key={theme.id} className={`theme-item theme-${theme.sentiment}`}>
                    <div className="theme-title-row">
                      <h4>{theme.label}</h4>
                      <span className={`tag tag-${theme.sentiment}`}>
                        <span className="dot"></span> {theme.sentiment.toUpperCase()}
                      </span>
                      <span className="trend">{theme.review_count} reviews</span>
                    </div>
                    <p>{theme.description}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Right Column for Sentiment & Actions */}
            <div className="right-col">
              
              {/* Market Sentiment Card */}
              <div className="card sentiment-card">
                <div className="card-header">
                  <h3>Overall Status</h3>
                </div>
                <div className="sentiment-chart-container">
                  <div className="donut-chart">
                    <div className="donut-content">
                      <span className="donut-number" style={{ fontSize: '1.5rem' }}>{data.status.toUpperCase()}</span>
                    </div>
                  </div>
                </div>
                <p className="sentiment-desc">This report was generated for the {data.iso_week} cycle.</p>
              </div>

              {/* Action Ideas Card Placeholder */}
              <div className="card action-card">
                <div className="action-header">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#00D09C" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 18h6"></path><path d="M10 22h4"></path><path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5A4.61 4.61 0 0 1 8.91 14"></path></svg>
                  <h3>AI Insights</h3>
                </div>
                <div className="action-list">
                  <p style={{ fontSize: '0.9rem', color: '#666', padding: '10px' }}>
                    Based on {data.themes.length} identified themes, the system is monitoring for operational improvements.
                  </p>
                </div>
              </div>

            </div>
          </div>

          {/* Quotes Section */}
          <div className="card quotes-card">
            <div className="card-header">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#00D09C" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginRight: '8px' }}><path d="M3 21c3 0 7-1 7-8V5c0-1.25-.756-2.017-2-2H4c-1.25 0-2 .75-2 1.972V11c0 1.25.75 2 2 2 1 0 1 0 1 1v1c0 1-1 2-2 2s-1 .008-1 1.031V20c0 1 0 1 1 1z"></path><path d="M15 21c3 0 7-1 7-8V5c0-1.25-.757-2.017-2-2h-4c-1.25 0-2 .75-2 1.972V11c0 1.25.75 2 2 2h.75c0 2.25.25 4-2.75 4v3c0 1 0 1 1 1z"></path></svg>
              <h3>Real User Voices</h3>
            </div>
            <div className="quotes-grid">
              {data.quotes.map((quote, idx) => (
                <div key={idx} className="quote-box">
                  <p className="quote-text">"{quote.text}"</p>
                  <p className="quote-author">— Rating: {quote.rating}★ ({quote.source})</p>
                </div>
              ))}
            </div>
          </div>

        </main>
      </div>
    </div>
  );
}
