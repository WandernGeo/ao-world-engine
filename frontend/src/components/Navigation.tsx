'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';

export default function Navigation() {
    const [menuOpen, setMenuOpen] = useState(false);
    const pathname = usePathname();

    const links = [
        { href: '/explore', label: 'Explore', icon: '🌃' },
        { href: '/npcs', label: 'NPCs', icon: '👥' },
        { href: '/chat', label: 'Chat', icon: '💬' },
        { href: '/graph', label: 'Graph', icon: '🕸️' },
        { href: '/monitor', label: 'Monitor', icon: '📊', highlight: true },
    ];

    const isActive = (href: string) => pathname === href;

    return (
        <>
            <header className="fixed top-0 left-0 right-0 h-14 bg-zinc-900/95 backdrop-blur z-50 flex items-center justify-between px-4 md:px-6 border-b border-zinc-800">
                <Link href="/" className="font-mono text-base md:text-lg font-bold text-cyan-400 tracking-wider hover:text-cyan-300 transition-colors">
                    AO WORLD ENGINE
                </Link>

                {/* Desktop Nav */}
                <nav className="hidden md:flex gap-1 lg:gap-2">
                    {links.map((link) => (
                        <Link
                            key={link.href}
                            href={link.href}
                            className={`text-sm font-medium px-3 py-1.5 rounded transition-colors ${isActive(link.href)
                                    ? 'text-white bg-zinc-700'
                                    : link.highlight
                                        ? 'text-cyan-400 hover:text-white border border-cyan-500/30 hover:bg-zinc-800'
                                        : 'text-zinc-300 hover:text-white hover:bg-zinc-800'
                                }`}
                        >
                            {link.label}
                        </Link>
                    ))}
                </nav>

                {/* Mobile Menu Button */}
                <button
                    onClick={() => setMenuOpen(!menuOpen)}
                    className="md:hidden p-2 text-zinc-300 hover:text-white rounded hover:bg-zinc-800 transition-colors"
                    aria-label="Toggle menu"
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
                <div
                    className="fixed top-14 left-0 right-0 bg-zinc-900/98 backdrop-blur border-b border-zinc-800 z-40 md:hidden"
                    onClick={() => setMenuOpen(false)}
                >
                    <nav className="flex flex-col p-3 gap-1">
                        {links.map((link) => (
                            <Link
                                key={link.href}
                                href={link.href}
                                className={`text-base font-medium py-3 px-4 rounded transition-colors flex items-center gap-3 ${isActive(link.href)
                                        ? 'text-white bg-zinc-700'
                                        : link.highlight
                                            ? 'text-cyan-400 bg-zinc-800/50 border border-cyan-500/30'
                                            : 'text-zinc-300 hover:text-white hover:bg-zinc-800'
                                    }`}
                            >
                                <span>{link.icon}</span>
                                {link.label}
                            </Link>
                        ))}
                    </nav>
                </div>
            )}

            {/* Spacer for fixed header */}
            <div className="h-14" />
        </>
    );
}
