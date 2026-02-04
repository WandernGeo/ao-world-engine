import Link from 'next/link';

export default function Home() {
  return (
    <main className="min-h-screen bg-zinc-950 text-white flex flex-col items-center justify-center p-8">
      {/* Hero */}
      <div className="text-center mb-12">
        <h1 className="text-5xl font-bold font-mono mb-4 bg-gradient-to-r from-cyan-400 via-purple-400 to-cyan-400 bg-clip-text text-transparent">
          AO WORLD ENGINE
        </h1>
        <p className="text-xl text-zinc-400 max-w-2xl">
          Decentralized, persistent world simulation on Arweave.
          Build living cities with NPCs that remember, grow, and evolve.
        </p>
      </div>

      {/* Feature Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mb-12">
        <Link href="/explore" className="group">
          <div className="bg-zinc-900/80 border border-cyan-500/30 rounded-xl p-6 hover:border-cyan-400 transition-all hover:shadow-lg hover:shadow-cyan-500/20">
            <div className="text-3xl mb-3">🌃</div>
            <h2 className="text-lg font-mono font-bold text-cyan-400 mb-2">Explore City</h2>
            <p className="text-zinc-500 text-sm">
              Navigate the polygon city map. See NPCs move in real-time. Generate AI scene images.
            </p>
          </div>
        </Link>

        <Link href="/chat" className="group">
          <div className="bg-zinc-900/80 border border-purple-500/30 rounded-xl p-6 hover:border-purple-400 transition-all hover:shadow-lg hover:shadow-purple-500/20">
            <div className="text-3xl mb-3">💬</div>
            <h2 className="text-lg font-mono font-bold text-purple-400 mb-2">Chat with NPCs</h2>
            <p className="text-zinc-500 text-sm">
              Talk to AI-powered characters. They remember your conversations and react to world events.
            </p>
          </div>
        </Link>

        <Link href="/graph" className="group">
          <div className="bg-zinc-900/80 border border-amber-500/30 rounded-xl p-6 hover:border-amber-400 transition-all hover:shadow-lg hover:shadow-amber-500/20">
            <div className="text-3xl mb-3">🕸️</div>
            <h2 className="text-lg font-mono font-bold text-amber-400 mb-2">Relationship Graph</h2>
            <p className="text-zinc-500 text-sm">
              Visualize NPC connections. See trust networks, rivalries, and cascading events.
            </p>
          </div>
        </Link>
      </div>

      {/* Stats */}
      <div className="flex gap-8 text-center mb-12">
        <div>
          <div className="text-3xl font-mono font-bold text-cyan-400">800</div>
          <div className="text-xs text-zinc-500">Simulated NPCs</div>
        </div>
        <div>
          <div className="text-3xl font-mono font-bold text-purple-400">19</div>
          <div className="text-xs text-zinc-500">Buildings</div>
        </div>
        <div>
          <div className="text-3xl font-mono font-bold text-amber-400">∞</div>
          <div className="text-xs text-zinc-500">Arweave Storage</div>
        </div>
      </div>

      {/* Demo Notice */}
      <div className="bg-zinc-900/50 border border-zinc-700 rounded-lg p-4 max-w-2xl text-center">
        <div className="text-sm text-zinc-400">
          🎮 This demo showcases <span className="text-cyan-400 font-mono">RE:ECHO City</span> -
          a cyberpunk noir world built on the AO World Engine.
        </div>
        <div className="text-xs text-zinc-600 mt-2">
          The engine is open source. Create your own world!
        </div>
      </div>

      {/* Footer Links */}
      <div className="mt-12 flex gap-6 text-sm text-zinc-500">
        <a href="https://github.com/WandernGeo/ao-world-engine" className="hover:text-cyan-400 transition-colors">
          GitHub
        </a>
        <a href="/docs" className="hover:text-cyan-400 transition-colors">
          Documentation
        </a>
        <a href="https://studioram.app" className="hover:text-cyan-400 transition-colors">
          StudioRam
        </a>
      </div>
    </main>
  );
}
