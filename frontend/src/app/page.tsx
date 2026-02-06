'use client';

import Link from 'next/link';
import { useState, useEffect } from 'react';
import { getWorldState } from '@/lib/ao-client';

// Fetch live status from AO
async function fetchStatus() {
  try {
    const state = await getWorldState();
    if (state) {
      return {
        npc_count: state.population,
        time: { tick: state.tick },
        events: { length: Math.floor(state.tick / 10) }
      };
    }
  } catch { }
  return null;
}

export default function Home() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [status, setStatus] = useState<{ npc_count: number; time: { tick: number }; events: { length: number } } | null>(null);

  useEffect(() => {
    fetchStatus().then(setStatus);
    const interval = setInterval(() => fetchStatus().then(setStatus), 60000); // Refresh every 60s
    return () => clearInterval(interval);
  }, []);

  return (
    <main className="min-h-screen bg-zinc-950 text-white">
      {/* Header - Responsive */}
      <header className="fixed top-0 left-0 right-0 h-14 bg-zinc-900/95 backdrop-blur z-50 flex items-center justify-between px-4 md:px-6 border-b border-zinc-800">
        <Link href="/" className="font-mono text-base md:text-lg font-bold text-cyan-400 tracking-wider">
          AO WORLD ENGINE
        </Link>

        {/* Desktop Nav */}
        <nav className="hidden md:flex gap-4 lg:gap-6">
          <Link href="/explore" className="text-sm font-medium text-zinc-300 hover:text-white transition-colors px-2 py-1">
            Explore
          </Link>
          <Link href="/npcs" className="text-sm font-medium text-zinc-300 hover:text-white transition-colors px-2 py-1">
            NPCs
          </Link>
          <Link href="/chat" className="text-sm font-medium text-zinc-300 hover:text-white transition-colors px-2 py-1">
            Chat
          </Link>
          <Link href="/graph" className="text-sm font-medium text-zinc-300 hover:text-white transition-colors px-2 py-1">
            Graph
          </Link>
          <Link href="/monitor" className="text-sm font-medium text-cyan-400 hover:text-white transition-colors px-2 py-1 border border-cyan-500/30 rounded">
            📊 Monitor
          </Link>
        </nav>

        {/* Mobile Menu Button */}
        <button
          onClick={() => setMenuOpen(!menuOpen)}
          className="md:hidden p-2 text-zinc-300 hover:text-white"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            {menuOpen ? (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            )}
          </svg>
        </button>
      </header>

      {/* Mobile Menu Dropdown */}
      {menuOpen && (
        <div className="fixed top-14 left-0 right-0 bg-zinc-900/98 backdrop-blur border-b border-zinc-800 z-40 md:hidden">
          <nav className="flex flex-col p-4 gap-2">
            <Link href="/explore" className="text-base font-medium text-zinc-300 hover:text-white py-3 px-4 rounded hover:bg-zinc-800 transition-colors">
              🌃 Explore City
            </Link>
            <Link href="/npcs" className="text-base font-medium text-zinc-300 hover:text-white py-3 px-4 rounded hover:bg-zinc-800 transition-colors">
              👥 NPCs
            </Link>
            <Link href="/chat" className="text-base font-medium text-zinc-300 hover:text-white py-3 px-4 rounded hover:bg-zinc-800 transition-colors">
              💬 Chat
            </Link>
            <Link href="/graph" className="text-base font-medium text-zinc-300 hover:text-white py-3 px-4 rounded hover:bg-zinc-800 transition-colors">
              🕸️ Graph
            </Link>
            <Link href="/monitor" className="text-base font-medium text-cyan-400 hover:text-white py-3 px-4 rounded bg-zinc-800/50 border border-cyan-500/30 transition-colors">
              📊 Live Monitor
            </Link>
          </nav>
        </div>
      )}

      <div className="pt-14 flex flex-col items-center justify-center min-h-screen p-4 md:p-8 gradient-bg-cyber">
        {/* Hero - Enhanced with gradient text */}
        <div className="text-center mb-8 md:mb-12">
          <h1 className="text-3xl md:text-5xl font-bold font-mono mb-4 md:mb-6 gradient-text-cyber tracking-wide">
            AO WORLD ENGINE
          </h1>
          <p className="text-base md:text-lg text-zinc-300 max-w-2xl leading-relaxed px-4">
            Decentralized, persistent world simulation on Arweave.
            Build living cities with NPCs that remember, grow, and evolve.
          </p>
          <div className="mt-4 flex justify-center gap-4">
            <span className="live-badge pulse-live">LIVE ON ARWEAVE</span>
          </div>
        </div>

        {/* Live Status Card - Enhanced with glassmorphism */}
        <Link href="/monitor" className="w-full max-w-md mb-8 group">
          <div className="glass-card glass-card-hover p-4 pulse-glow-live">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse"></div>
                <span className="text-sm font-mono text-cyan-400">LIVE SIMULATION</span>
              </div>
              <span className="text-xs text-zinc-400 group-hover:text-cyan-400 transition-colors">View dashboard →</span>
            </div>
            {status ? (
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <div className="text-xl font-mono font-bold text-white">{status.npc_count || 800}</div>
                  <div className="text-xs text-zinc-400">NPCs</div>
                </div>
                <div>
                  <div className="text-xl font-mono font-bold text-white">T{status.time?.tick || 100}</div>
                  <div className="text-xs text-zinc-400">Tick</div>
                </div>
                <div>
                  <div className="text-xl font-mono font-bold text-green-400">{status.events?.length || 2}</div>
                  <div className="text-xs text-zinc-400">Events</div>
                </div>
              </div>
            ) : (
              <div className="text-center text-zinc-500 text-sm py-2">Loading status...</div>
            )}
          </div>
        </Link>

        {/* Feature Cards - Responsive Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 max-w-6xl mb-12 w-full px-2">
          <Link href="/explore" className="group">
            <div className="bg-zinc-900 border border-zinc-700 rounded-lg p-5 hover:border-cyan-500 hover:bg-zinc-800/50 transition-all h-full">
              <div className="text-2xl mb-3">🌃</div>
              <h2 className="text-sm font-semibold text-white mb-2">Explore City</h2>
              <p className="text-zinc-400 text-xs leading-relaxed">
                Navigate the polygon city. See NPCs in real-time.
              </p>
            </div>
          </Link>

          <Link href="/npcs" className="group">
            <div className="bg-zinc-900 border border-zinc-700 rounded-lg p-5 hover:border-cyan-500 hover:bg-zinc-800/50 transition-all h-full">
              <div className="text-2xl mb-3">👥</div>
              <h2 className="text-sm font-semibold text-white mb-2">NPC System</h2>
              <p className="text-zinc-400 text-xs leading-relaxed">
                800+ characters with schedules and relationships.
              </p>
            </div>
          </Link>

          <Link href="/chat" className="group">
            <div className="bg-zinc-900 border border-zinc-700 rounded-lg p-5 hover:border-cyan-500 hover:bg-zinc-800/50 transition-all h-full">
              <div className="text-2xl mb-3">💬</div>
              <h2 className="text-sm font-semibold text-white mb-2">Chat</h2>
              <p className="text-zinc-400 text-xs leading-relaxed">
                Talk to AI NPCs. They remember conversations.
              </p>
            </div>
          </Link>

          <Link href="/graph" className="group">
            <div className="bg-zinc-900 border border-zinc-700 rounded-lg p-5 hover:border-cyan-500 hover:bg-zinc-800/50 transition-all h-full">
              <div className="text-2xl mb-3">🕸️</div>
              <h2 className="text-sm font-semibold text-white mb-2">Graph</h2>
              <p className="text-zinc-400 text-xs leading-relaxed">
                3D relationship visualization.
              </p>
            </div>
          </Link>

          <Link href="/monitor" className="group">
            <div className="bg-zinc-900 border border-cyan-500/50 rounded-lg p-5 hover:border-cyan-400 hover:bg-zinc-800/50 transition-all h-full">
              <div className="text-2xl mb-3">📊</div>
              <h2 className="text-sm font-semibold text-cyan-400 mb-2">Monitor</h2>
              <p className="text-zinc-400 text-xs leading-relaxed">
                Live simulation dashboard.
              </p>
            </div>
          </Link>
        </div>

        {/* Stats - Responsive */}
        <div className="flex gap-6 md:gap-12 text-center mb-12 flex-wrap justify-center">
          <div>
            <div className="text-2xl md:text-3xl font-mono font-bold text-white">800</div>
            <div className="text-xs text-zinc-400 mt-1">AI NPCs</div>
          </div>
          <div>
            <div className="text-2xl md:text-3xl font-mono font-bold text-white">160</div>
            <div className="text-xs text-zinc-400 mt-1">Families</div>
          </div>
          <div>
            <div className="text-2xl md:text-3xl font-mono font-bold text-white">19</div>
            <div className="text-xs text-zinc-400 mt-1">Buildings</div>
          </div>
          <div>
            <div className="text-2xl md:text-3xl font-mono font-bold text-cyan-400">∞</div>
            <div className="text-xs text-zinc-400 mt-1">Arweave</div>
          </div>
        </div>

        {/* Demo Notice */}
        <div className="bg-zinc-900 border border-zinc-700 rounded-lg p-4 max-w-lg text-center mx-4">
          <div className="text-sm text-zinc-300">
            🎮 <span className="text-cyan-400 font-mono">RE:ECHO City</span> - Cyberpunk noir world on AO World Engine.
          </div>
          <div className="text-xs text-zinc-500 mt-2">
            Open source. Create your own world!
          </div>
        </div>

        {/* Footer Links */}
        <div className="mt-8 flex gap-6 md:gap-8 text-sm flex-wrap justify-center">
          <a href="https://github.com/WandernGeo/ao-world-engine" className="text-zinc-400 hover:text-white transition-colors">
            GitHub
          </a>
          <a href="/docs" className="text-zinc-400 hover:text-white transition-colors">
            Docs
          </a>
          <a href="https://studioram.app" className="text-zinc-400 hover:text-white transition-colors">
            StudioRam
          </a>
        </div>
      </div>
    </main>
  );
}
