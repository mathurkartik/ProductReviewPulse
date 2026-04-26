"use client";

import React from 'react';

export default function Dashboard() {
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
              <h1>Groww — Weekly Review Pulse</h1>
              <div className="header-meta">
                <span className="badge">REPORT ID: WR-2023-42</span>
                <span className="period">Period: Last 8-12 weeks (rolling window)</span>
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
                <div className="theme-item theme-critical">
                  <div className="theme-title-row">
                    <h4>App performance & bugs</h4>
                    <span className="tag tag-critical"><span className="dot"></span> CRITICAL</span>
                    <span className="trend trend-critical">42% Growth</span>
                  </div>
                  <p>Systematic lag, frequent app crashes, and login timeouts reported across various regions.</p>
                </div>
                
                <div className="theme-item theme-negative">
                  <div className="theme-title-row">
                    <h4>Customer support friction</h4>
                    <span className="tag tag-negative"><span className="dot"></span> NEGATIVE</span>
                    <span className="trend trend-negative">28% Impact</span>
                  </div>
                  <p>Increasing dissatisfaction with slow response times and non-resolution of complex queries.</p>
                </div>
                
                <div className="theme-item theme-neutral">
                  <div className="theme-title-row">
                    <h4>UX & feature gaps</h4>
                    <span className="tag tag-neutral"><span className="dot"></span> NEUTRAL</span>
                    <span className="trend trend-neutral">15% Trend</span>
                  </div>
                  <p>Users finding certain navigation paths confusing; requests for advanced technical analysis tools.</p>
                </div>
              </div>
            </div>

            {/* Right Column for Sentiment & Actions */}
            <div className="right-col">
              
              {/* Market Sentiment Card */}
              <div className="card sentiment-card">
                <div className="card-header">
                  <h3>Market Sentiment</h3>
                </div>
                <div className="sentiment-chart-container">
                  <div className="donut-chart">
                    <svg viewBox="0 0 36 36" className="circular-chart">
                      <path className="circle-bg"
                        d="M18 2.0845
                        a 15.9155 15.9155 0 0 1 0 31.831
                        a 15.9155 15.9155 0 0 1 0 -31.831"
                      />
                      <path className="circle"
                        strokeDasharray="62, 100"
                        d="M18 2.0845
                        a 15.9155 15.9155 0 0 1 0 31.831
                        a 15.9155 15.9155 0 0 1 0 -31.831"
                      />
                    </svg>
                    <div className="donut-content">
                      <span className="donut-number">62</span>
                      <span className="donut-label">VOLATILITY</span>
                    </div>
                  </div>
                </div>
                <p className="sentiment-desc">Sentiment score is down 12% from previous rolling window due to API instability.</p>
              </div>

              {/* Action Ideas Card */}
              <div className="card action-card">
                <div className="action-header">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#00D09C" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 18h6"></path><path d="M10 22h4"></path><path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5A4.61 4.61 0 0 1 8.91 14"></path></svg>
                  <h3>Action Ideas</h3>
                </div>
                <div className="action-list">
                  <div className="action-item">
                    <div className="action-num">01.</div>
                    <div className="action-text">
                      <h4>Stabilize peak-time performance</h4>
                      <p>Optimize socket connections during market open (9:15 AM).</p>
                    </div>
                  </div>
                  <div className="action-item">
                    <div className="action-num">02.</div>
                    <div className="action-text">
                      <h4>Improve support SLA visibility</h4>
                      <p>Add real-time queue position indicators in the help desk.</p>
                    </div>
                  </div>
                  <div className="action-item">
                    <div className="action-num">03.</div>
                    <div className="action-text">
                      <h4>Enhance power-user features</h4>
                      <p>Roll out advanced charting beta for high-AUM accounts.</p>
                    </div>
                  </div>
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
              <div className="quote-box">
                <p className="quote-text">"The app freezes exactly when the market opens, very frustrating."</p>
                <p className="quote-author">— High Frequency Trader</p>
              </div>
              <div className="quote-box">
                <p className="quote-text">"Support takes days to reply and doesn't solve the issue."</p>
                <p className="quote-author">— Verified User</p>
              </div>
              <div className="quote-box">
                <p className="quote-text">"Good for beginners but lacks detailed analysis tools."</p>
                <p className="quote-author">— Advanced Investor</p>
              </div>
            </div>
          </div>

          {/* Operational Insights Section */}
          <div className="card metrics-card">
            <div className="card-header">
              <h3>Operational Insights</h3>
              <div className="legend">
                <span className="legend-item"><span className="dot dot-success"></span> SUCCESS</span>
                <span className="legend-item"><span className="dot dot-danger"></span> FAILURES</span>
              </div>
            </div>
            <div className="metrics-grid">
              <div className="metric-item">
                <span className="metric-label">API UPTIME</span>
                <span className="metric-value">99.92%</span>
                <div className="progress-bar"><div className="progress fill-success" style={{ width: '99.92%' }}></div></div>
              </div>
              <div className="metric-item">
                <span className="metric-label">AVG LATENCY</span>
                <span className="metric-value">24ms</span>
                <div className="progress-bar"><div className="progress fill-success" style={{ width: '24%' }}></div></div>
              </div>
              <div className="metric-item">
                <span className="metric-label">TICKET VOLUME</span>
                <span className="metric-value">1.2k <span className="metric-unit">/day</span></span>
                <div className="progress-bar"><div className="progress fill-danger" style={{ width: '80%' }}></div></div>
              </div>
              <div className="metric-item">
                <span className="metric-label">USER CHURN RISK</span>
                <span className="metric-value">Medium</span>
                <div className="progress-bar"><div className="progress fill-neutral" style={{ width: '50%' }}></div></div>
              </div>
            </div>
          </div>

          {/* Bottom Layout */}
          <div className="bottom-layout">
            <div className="solves-section">
              <h3>What this solves</h3>
              <p>This report identifies critical technical bottlenecks causing user drop-off and provides a direct roadmap for CX alignment. By focusing on peak-time stability, we protect the primary revenue window.</p>
            </div>
            
            <div className="metadata-card">
              <h4>MCP DELIVERY METADATA</h4>
              <ul className="meta-list">
                <li>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                  Archived: <a href="#">Groww_WR_42.doc</a>
                </li>
                <li>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path><polyline points="22,6 12,13 2,6"></polyline></svg>
                  Email sent to stakeholders
                </li>
                <li>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                  Next review: Oct 28, 2023
                </li>
              </ul>
            </div>
          </div>

        </main>
      </div>
    </div>
  );
}
