import Link from 'next/link';

export default function Home() {
  return (
    <main className="min-h-screen bg-zinc-950 text-white">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 h-14 bg-zinc-900 z-50 flex items-center justify-between px-6 border-b border-zinc-800">
        <div className="font-mono text-lg font-bold text-cyan-400 tracking-wider">
          AO WORLD ENGINE
        </div>
        <nav className="flex gap-6">
          <Link href="/explore" className="text-sm font-medium text-zinc-300 hover:text-white transition-colors">
            Explore
          </Link>
          <Link href="/npcs" className="text-sm font-medium text-zinc-300 hover:text-white transition-colors">
            NPCs
          </Link>
          <Link href="/chat" className="text-sm font-medium text-zinc-300 hover:text-white transition-colors">
            Chat
          </Link>
          <Link href="/graph" className="text-sm font-medium text-zinc-300 hover:text-white transition-colors">
            Graph
          </Link>
        </nav>
      </header>

      <div className="pt-14 flex flex-col items-center justify-center min-h-screen p-8">
        {/* Hero */}
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold font-mono mb-6 text-cyan-400 tracking-wide">
            AO WORLD ENGINE
          </h1>
          <p className="text-lg text-zinc-300 max-w-2xl leading-relaxed">
            Decentralized, persistent world simulation on Arweave.
            Build living cities with NPCs that remember, grow, and evolve.
          </p>
        </div>

        {/* Feature Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 max-w-5xl mb-16">
          <Link href="/explore" className="group">
            <div className="bg-zinc-900 border border-zinc-700 rounded-lg p-6 hover:border-cyan-500 hover:bg-zinc-800/50 transition-all">
              <div className="text-3xl mb-4">🌃</div>
              <h2 className="text-base font-semibold text-white mb-2">Explore City</h2>
              <p className="text-zinc-400 text-sm leading-relaxed">
                Navigate the polygon city map. See NPCs move in real-time. Generate AI scene images.
              </p>
            </div>
          </Link>

          <Link href="/npcs" className="group">
            <div className="bg-zinc-900 border border-zinc-700 rounded-lg p-6 hover:border-cyan-500 hover:bg-zinc-800/50 transition-all">
              <div className="text-3xl mb-4">👥</div>
              <h2 className="text-base font-semibold text-white mb-2">NPC System</h2>
              <p className="text-zinc-400 text-sm leading-relaxed">
                Meet the founding citizens. View stats, schedules, and trust networks of 800+ characters.
              </p>
            </div>
          </Link>

          <Link href="/chat" className="group">
            <div className="bg-zinc-900 border border-zinc-700 rounded-lg p-6 hover:border-cyan-500 hover:bg-zinc-800/50 transition-all">
              <div className="text-3xl mb-4">💬</div>
              <h2 className="text-base font-semibold text-white mb-2">Chat with NPCs</h2>
              <p className="text-zinc-400 text-sm leading-relaxed">
                Talk to AI-powered characters. They remember your conversations and react to world events.
              </p>
            </div>
          </Link>

          <Link href="/graph" className="group">
            <div className="bg-zinc-900 border border-zinc-700 rounded-lg p-6 hover:border-cyan-500 hover:bg-zinc-800/50 transition-all">
              <div className="text-3xl mb-4">🕸️</div>
              <h2 className="text-base font-semibold text-white mb-2">Relationship Graph</h2>
              <p className="text-zinc-400 text-sm leading-relaxed">
                Visualize NPC connections. See trust networks, rivalries, and cascading events.
              </p>
            </div>
          </Link>
        </div>

        {/* Hero Image / City Showcase */}
        <div className="w-full max-w-4xl mb-16 rounded-lg overflow-hidden border border-zinc-800">
          <div className="relative aspect-[21/9] bg-zinc-900 flex items-center justify-center">
            <div className="text-center">
              <div className="text-6xl mb-4">🌆</div>
              <div className="text-xl font-mono text-cyan-400">RE:ECHO City</div>
              <div className="text-sm text-zinc-400 mt-1">Cyberpunk noir simulation</div>
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="flex gap-12 text-center mb-16 flex-wrap justify-center">
          <div>
            <div className="text-3xl font-mono font-bold text-white">800</div>
            <div className="text-xs text-zinc-400 mt-1">AI NPCs</div>
          </div>
          <div>
            <div className="text-3xl font-mono font-bold text-white">160</div>
            <div className="text-xs text-zinc-400 mt-1">Families</div>
          </div>
          <div>
            <div className="text-3xl font-mono font-bold text-white">19</div>
            <div className="text-xs text-zinc-400 mt-1">Buildings</div>
          </div>
          <div>
            <div className="text-3xl font-mono font-bold text-white">15</div>
            <div className="text-xs text-zinc-400 mt-1">Schedules</div>
          </div>
          <div>
            <div className="text-3xl font-mono font-bold text-cyan-400">∞</div>
            <div className="text-xs text-zinc-400 mt-1">Arweave</div>
          </div>
        </div>

        {/* Demo Notice */}
        <div className="bg-zinc-900 border border-zinc-700 rounded-lg p-5 max-w-2xl text-center">
          <div className="text-sm text-zinc-300">
            🎮 This demo showcases <span className="text-cyan-400 font-mono">RE:ECHO City</span> -
            a cyberpunk noir world built on the AO World Engine.
          </div>
          <div className="text-xs text-zinc-500 mt-2">
            The engine is open source. Create your own world!
          </div>
        </div>

        {/* Footer Links */}
        <div className="mt-12 flex gap-8 text-sm">
          <a href="https://github.com/WandernGeo/ao-world-engine" className="text-zinc-400 hover:text-white transition-colors">
            GitHub
          </a>
          <a href="/docs" className="text-zinc-400 hover:text-white transition-colors">
            Documentation
          </a>
          <a href="https://studioram.app" className="text-zinc-400 hover:text-white transition-colors">
            StudioRam
          </a>
        </div>
      </div>
    </main>
  );
}
