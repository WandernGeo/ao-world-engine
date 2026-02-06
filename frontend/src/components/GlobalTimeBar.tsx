'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useSimulation } from './SimulationProvider';

export function GlobalTimeBar() {
    const pathname = usePathname();
    const simulation = useSimulation();

    // Use demoMode from shared context (persisted in SimulationProvider via localStorage)
    const demoMode = simulation.demoMode;
    const toggleDemoMode = (value: boolean) => simulation.setDemoMode(value);

    const navItems = [
        { href: '/explore', label: 'Explore' },
        { href: '/npcs', label: 'NPCs' },
        { href: '/chat', label: 'Chat' },
        { href: '/graph', label: 'Graph' },
        { href: '/monitor', label: 'Monitor' },
    ];

    return (
        <>
            {/* Fixed Header */}
            <header className="fixed top-0 left-0 right-0 h-14 bg-zinc-900 z-50 flex items-center px-4 border-b border-cyan-500/30">
                <Link href="/" className="font-mono text-lg font-bold bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">
                    AO WORLD ENGINE
                </Link>

                <nav className="ml-8 flex gap-1">
                    {navItems.map(item => (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={`text-sm font-medium px-3 py-1.5 rounded transition-colors ${pathname === item.href
                                ? 'text-cyan-400 bg-cyan-500/10'
                                : 'text-gray-300 hover:text-cyan-400'
                                }`}
                        >
                            {item.label}
                        </Link>
                    ))}
                </nav>

                {/* Right side controls */}
                <div className="ml-auto flex items-center gap-4">
                    {/* Mode Toggle - LIVE/DEMO with persistence */}
                    <div className="flex items-center bg-gray-800 rounded-full p-0.5">
                        <button
                            onClick={() => toggleDemoMode(false)}
                            className={`px-3 py-1 text-xs font-medium rounded-full transition-all ${!demoMode
                                ? 'bg-red-500 text-white animate-pulse'
                                : 'text-gray-400 hover:text-white'
                                }`}
                        >
                            ● LIVE
                        </button>
                        <button
                            onClick={() => toggleDemoMode(true)}
                            className={`px-3 py-1 text-xs font-medium rounded-full transition-all ${demoMode
                                ? 'bg-yellow-500 text-black'
                                : 'text-gray-400 hover:text-white'
                                }`}
                        >
                            ◉ DEMO
                        </button>
                    </div>

                    {/* Current Tick */}
                    <span className="text-xs text-gray-400 font-mono">
                        T{simulation.tick}
                    </span>
                </div>
            </header>

            {/* Fixed Time Controls Bar (below header) */}
            <div className="fixed top-14 left-0 right-0 h-12 bg-zinc-900/95 backdrop-blur border-b border-gray-700 px-4 z-40 flex items-center gap-4">
                {/* Playback Controls */}
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => simulation.advanceTick(-10)}
                        className="p-1.5 bg-gray-700 hover:bg-gray-600 rounded text-sm"
                        title="Rewind 10 ticks"
                    >
                        ⏪
                    </button>
                    <button
                        onClick={() => simulation.isPlaying ? simulation.pause() : simulation.play()}
                        className="p-1.5 bg-cyan-600 hover:bg-cyan-700 rounded text-sm"
                        title={simulation.isPlaying ? 'Pause' : 'Play'}
                    >
                        {simulation.isPlaying ? '⏸' : '▶'}
                    </button>
                    <button
                        onClick={() => simulation.advanceTick(10)}
                        className="p-1.5 bg-gray-700 hover:bg-gray-600 rounded text-sm"
                        title="Forward 10 ticks"
                    >
                        ⏩
                    </button>
                </div>

                {/* Speed Controls */}
                <div className="flex items-center gap-1">
                    <span className="text-xs text-gray-400">Speed:</span>
                    {[0.5, 1, 2, 5, 10].map(s => (
                        <button
                            key={s}
                            onClick={() => simulation.setPlaybackSpeed(s)}
                            className={`px-2 py-0.5 text-xs rounded ${simulation.playbackSpeed === s
                                ? 'bg-cyan-600 text-white'
                                : 'bg-gray-700 hover:bg-gray-600 text-gray-300'
                                }`}
                        >
                            {s}x
                        </button>
                    ))}
                </div>

                {/* Time Display */}
                <div className="ml-auto text-right">
                    <div className="text-sm font-bold text-white font-mono">
                        Day {simulation.day} • {simulation.period}
                    </div>
                    <div className="text-xs text-gray-400">
                        Year {simulation.year} • Tick {simulation.tick}
                    </div>
                </div>
            </div>
        </>
    );
}
