'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface Room {
    id: string;
    name: string;
    type: 'living' | 'work' | 'storage' | 'special';
    occupants: string[];
    x: number;
    y: number;
    width: number;
    height: number;
}

interface BuildingData {
    id: string;
    name: string;
    type: string;
    levels: number;
    owner?: string;
    description?: string;
    rooms?: Room[];
    occupants: string[];
}

interface BuildingBlueprintProps {
    building: BuildingData;
    onClose: () => void;
    onNpcClick?: (npcId: string) => void;
}

export function BuildingBlueprint({ building, onClose, onNpcClick }: BuildingBlueprintProps) {
    const [selectedLevel, setSelectedLevel] = useState(1);

    // Generate mock rooms if not provided
    const rooms: Room[] = building.rooms || [
        { id: 'main', name: 'Main Hall', type: 'living', x: 10, y: 10, width: 180, height: 100, occupants: building.occupants.slice(0, 2) },
        { id: 'back', name: 'Back Room', type: 'work', x: 10, y: 120, width: 80, height: 70, occupants: [] },
        { id: 'storage', name: 'Storage', type: 'storage', x: 100, y: 120, width: 90, height: 70, occupants: [] },
    ];

    const getRoomColor = (type: string) => {
        switch (type) {
            case 'living': return 'fill-blue-900/50 stroke-blue-500';
            case 'work': return 'fill-green-900/50 stroke-green-500';
            case 'storage': return 'fill-gray-800/50 stroke-gray-500';
            case 'special': return 'fill-purple-900/50 stroke-purple-500';
            default: return 'fill-gray-800/50 stroke-gray-500';
        }
    };

    const getBuildingTypeIcon = (type: string) => {
        switch (type) {
            case 'commercial': return '🏪';
            case 'residential': return '🏠';
            case 'industrial': return '🏭';
            case 'temple': return '⛩️';
            default: return '🏢';
        }
    };

    return (
        <Card className="bg-gray-900/95 backdrop-blur border-cyan-500/30 w-80">
            <CardHeader className="pb-2">
                <div className="flex justify-between items-start">
                    <div>
                        <CardTitle className="text-cyan-400 flex items-center gap-2">
                            {getBuildingTypeIcon(building.type)} {building.name}
                        </CardTitle>
                        <p className="text-xs text-gray-500 mt-1">
                            {building.type} • {building.levels} level{building.levels > 1 ? 's' : ''}
                        </p>
                    </div>
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={onClose}
                        className="text-gray-400 hover:text-white"
                    >
                        ✕
                    </Button>
                </div>
            </CardHeader>

            <CardContent className="space-y-4">
                {/* Level selector */}
                {building.levels > 1 && (
                    <div className="flex gap-1">
                        {Array.from({ length: building.levels }, (_, i) => (
                            <Button
                                key={i}
                                variant={selectedLevel === i + 1 ? "default" : "outline"}
                                size="sm"
                                onClick={() => setSelectedLevel(i + 1)}
                                className={selectedLevel === i + 1 ? 'bg-cyan-600' : ''}
                            >
                                L{i + 1}
                            </Button>
                        ))}
                    </div>
                )}

                {/* Blueprint SVG */}
                <div className="bg-gray-950 rounded-lg p-2 relative">
                    <svg viewBox="0 0 200 200" className="w-full h-48">
                        {/* Grid */}
                        <defs>
                            <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
                                <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#333" strokeWidth="0.5" />
                            </pattern>
                        </defs>
                        <rect width="200" height="200" fill="url(#grid)" />

                        {/* Rooms */}
                        {rooms.map((room) => (
                            <g key={room.id}>
                                <rect
                                    x={room.x}
                                    y={room.y}
                                    width={room.width}
                                    height={room.height}
                                    className={`${getRoomColor(room.type)} stroke-2 transition-all hover:brightness-125 cursor-pointer`}
                                />
                                <text
                                    x={room.x + room.width / 2}
                                    y={room.y + 15}
                                    textAnchor="middle"
                                    className="fill-gray-400 text-[8px] font-medium"
                                >
                                    {room.name}
                                </text>

                                {/* Occupants in room */}
                                {room.occupants.map((occ, i) => (
                                    <circle
                                        key={occ}
                                        cx={room.x + 20 + i * 25}
                                        cy={room.y + room.height - 20}
                                        r="8"
                                        className="fill-cyan-500 stroke-cyan-300 stroke-1 cursor-pointer hover:fill-cyan-400"
                                        onClick={() => onNpcClick?.(occ)}
                                    />
                                ))}
                            </g>
                        ))}

                        {/* Building outline */}
                        <rect
                            x="5"
                            y="5"
                            width="190"
                            height="190"
                            fill="none"
                            stroke="#0ff"
                            strokeWidth="2"
                            strokeDasharray="5,5"
                        />
                    </svg>
                </div>

                {/* Occupants list */}
                <div>
                    <h4 className="text-xs text-gray-500 mb-2">CURRENT OCCUPANTS</h4>
                    <div className="flex flex-wrap gap-2">
                        {building.occupants.length > 0 ? (
                            building.occupants.map((occ) => (
                                <Button
                                    key={occ}
                                    variant="outline"
                                    size="sm"
                                    onClick={() => onNpcClick?.(occ)}
                                    className="text-xs border-cyan-500/30 hover:bg-cyan-500/20"
                                >
                                    {occ}
                                </Button>
                            ))
                        ) : (
                            <span className="text-gray-500 text-sm">Empty</span>
                        )}
                    </div>
                </div>

                {/* Building info */}
                {building.description && (
                    <p className="text-xs text-gray-400 italic">
                        "{building.description}"
                    </p>
                )}

                {building.owner && (
                    <p className="text-xs text-gray-500">
                        Owner: <span className="text-cyan-400">{building.owner}</span>
                    </p>
                )}
            </CardContent>
        </Card>
    );
}
