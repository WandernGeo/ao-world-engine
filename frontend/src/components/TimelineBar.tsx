'use client';

import { useState, useEffect } from 'react';

interface TimelineEvent {
    tick: number;
    timestamp: string;
    type: string;
    description: string;
    participants?: string[];
}

interface TimelineBarProps {
    currentTick: number;
    maxTick: number;
    events: TimelineEvent[];
    onTickChange: (tick: number) => void;
    onEventClick?: (event: TimelineEvent) => void;
}

export function TimelineBar({
    currentTick,
    maxTick,
    events,
    onTickChange,
    onEventClick
}: TimelineBarProps) {
    const [isDragging, setIsDragging] = useState(false);
    const [hoveredEvent, setHoveredEvent] = useState<TimelineEvent | null>(null);

    const tickToPercent = (tick: number) => (tick / maxTick) * 100;

    const formatTick = (tick: number) => {
        const hour = tick % 24;
        const day = Math.floor(tick / 24) + 1;
        return `Day ${day}, ${hour.toString().padStart(2, '0')}:00`;
    };

    const handleTimelineClick = (e: React.MouseEvent<HTMLDivElement>) => {
        const rect = e.currentTarget.getBoundingClientRect();
        const percent = (e.clientX - rect.left) / rect.width;
        const newTick = Math.round(percent * maxTick);
        onTickChange(Math.max(0, Math.min(maxTick, newTick)));
    };

    const getEventColor = (type: string) => {
        switch (type) {
            case 'conflict': return 'bg-red-500';
            case 'gossip': return 'bg-purple-500';
            case 'trade': return 'bg-green-500';
            case 'friendly_chat': return 'bg-blue-500';
            case 'news': return 'bg-yellow-500';
            default: return 'bg-gray-500';
        }
    };

    return (
        <div className="w-full bg-gray-900/80 backdrop-blur-sm rounded-lg p-4 space-y-2">
            {/* Header */}
            <div className="flex justify-between items-center text-sm">
                <span className="text-cyan-400 font-mono">
                    {formatTick(currentTick)}
                </span>
                <span className="text-gray-500">
                    Tick {currentTick} / {maxTick}
                </span>
            </div>

            {/* Timeline Track */}
            <div
                className="relative h-8 bg-gray-800 rounded cursor-pointer"
                onClick={handleTimelineClick}
                onMouseDown={() => setIsDragging(true)}
                onMouseUp={() => setIsDragging(false)}
                onMouseLeave={() => setIsDragging(false)}
            >
                {/* Progress bar */}
                <div
                    className="absolute h-full bg-gradient-to-r from-cyan-600 to-purple-600 rounded-l"
                    style={{ width: `${tickToPercent(currentTick)}%` }}
                />

                {/* Event markers */}
                {events.map((event, i) => (
                    <div
                        key={i}
                        className={`absolute top-1 w-2 h-6 rounded ${getEventColor(event.type)} 
                       hover:ring-2 hover:ring-white cursor-pointer transition-transform hover:scale-125`}
                        style={{ left: `${tickToPercent(event.tick)}%` }}
                        onMouseEnter={() => setHoveredEvent(event)}
                        onMouseLeave={() => setHoveredEvent(null)}
                        onClick={(e) => {
                            e.stopPropagation();
                            onEventClick?.(event);
                        }}
                    />
                ))}

                {/* Current position marker */}
                <div
                    className="absolute top-0 w-1 h-8 bg-white shadow-lg"
                    style={{ left: `${tickToPercent(currentTick)}%` }}
                />
            </div>

            {/* Hovered event tooltip */}
            {hoveredEvent && (
                <div className="bg-gray-800 rounded p-2 text-sm animate-fadeIn">
                    <div className="flex items-center gap-2">
                        <span className={`w-2 h-2 rounded-full ${getEventColor(hoveredEvent.type)}`} />
                        <span className="text-white font-medium">{hoveredEvent.type}</span>
                        <span className="text-gray-400 text-xs">{formatTick(hoveredEvent.tick)}</span>
                    </div>
                    <p className="text-gray-300 mt-1">{hoveredEvent.description}</p>
                    {hoveredEvent.participants && (
                        <p className="text-gray-500 text-xs mt-1">
                            Participants: {hoveredEvent.participants.join(', ')}
                        </p>
                    )}
                </div>
            )}

            {/* Legend */}
            <div className="flex gap-4 text-xs text-gray-400">
                <span className="flex items-center gap-1">
                    <span className="w-2 h-2 rounded-full bg-red-500" /> Conflict
                </span>
                <span className="flex items-center gap-1">
                    <span className="w-2 h-2 rounded-full bg-purple-500" /> Gossip
                </span>
                <span className="flex items-center gap-1">
                    <span className="w-2 h-2 rounded-full bg-green-500" /> Trade
                </span>
                <span className="flex items-center gap-1">
                    <span className="w-2 h-2 rounded-full bg-yellow-500" /> News
                </span>
            </div>
        </div>
    );
}
