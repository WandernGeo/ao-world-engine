'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

interface TimeControlsProps {
    currentTick: number;
    onTickChange: (tick: number) => void;
    isPlaying: boolean;
    onPlayPause: () => void;
    tickSpeed: number;
    onSpeedChange: (speed: number) => void;
}

export function TimeControls({
    currentTick,
    onTickChange,
    isPlaying,
    onPlayPause,
    tickSpeed,
    onSpeedChange,
}: TimeControlsProps) {
    const [manualTick, setManualTick] = useState(currentTick.toString());

    // Convert tick to readable time
    const ticksPerHour = 100 / 24; // ~4.17 ticks per hour
    const day = Math.floor(currentTick / 100) + 1;
    const tickInDay = currentTick % 100;
    const hour = Math.floor(tickInDay / ticksPerHour);
    const minute = Math.floor((tickInDay % ticksPerHour) / ticksPerHour * 60);

    const handleManualSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        const newTick = parseInt(manualTick, 10);
        if (!isNaN(newTick) && newTick >= 0) {
            onTickChange(newTick);
        }
    };

    return (
        <Card className="bg-zinc-900/90 border-cyan-500/30 backdrop-blur-sm">
            <CardHeader className="pb-2">
                <CardTitle className="text-cyan-400 font-mono text-sm flex items-center gap-2">
                    <span className="text-lg">⏱</span> TIME CONTROLS
                </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
                {/* Current Time Display */}
                <div className="text-center py-2 bg-black/50 rounded border border-cyan-500/20">
                    <div className="font-mono text-2xl text-cyan-300">
                        Day {day} • {hour.toString().padStart(2, '0')}:{minute.toString().padStart(2, '0')}
                    </div>
                    <div className="text-xs text-zinc-500 font-mono">
                        Tick: {currentTick.toLocaleString()}
                    </div>
                </div>

                {/* Play/Pause + Speed */}
                <div className="flex items-center gap-2">
                    <Button
                        onClick={onPlayPause}
                        variant={isPlaying ? 'destructive' : 'default'}
                        className="flex-1"
                    >
                        {isPlaying ? '⏸ Pause' : '▶ Play'}
                    </Button>
                    <div className="flex-1">
                        <Label className="text-xs text-zinc-500">Speed: {tickSpeed}x</Label>
                        <Slider
                            value={[tickSpeed]}
                            onValueChange={([v]) => onSpeedChange(v)}
                            min={1}
                            max={100}
                            step={1}
                            className="mt-1"
                        />
                    </div>
                </div>

                {/* Time Scrubber */}
                <div>
                    <Label className="text-xs text-zinc-500">Scrub Time</Label>
                    <Slider
                        value={[tickInDay]}
                        onValueChange={([v]) => onTickChange((day - 1) * 100 + v)}
                        min={0}
                        max={99}
                        step={1}
                        className="mt-1"
                    />
                    <div className="flex justify-between text-xs text-zinc-600 mt-1">
                        <span>00:00</span>
                        <span>06:00</span>
                        <span>12:00</span>
                        <span>18:00</span>
                        <span>23:59</span>
                    </div>
                </div>

                {/* Manual Tick Input */}
                <form onSubmit={handleManualSubmit} className="flex gap-2">
                    <div className="flex-1">
                        <Label className="text-xs text-zinc-500">Jump to Tick</Label>
                        <Input
                            type="number"
                            value={manualTick}
                            onChange={(e) => setManualTick(e.target.value)}
                            className="bg-black/50 border-zinc-700 text-cyan-300 font-mono"
                            placeholder="Enter tick number"
                        />
                    </div>
                    <Button type="submit" variant="outline" className="mt-5">
                        Go
                    </Button>
                </form>

                {/* Quick Jump Buttons */}
                <div className="grid grid-cols-4 gap-1">
                    {['+1 Hour', '+6 Hours', '+1 Day', '+1 Week'].map((label, i) => (
                        <Button
                            key={label}
                            variant="outline"
                            size="sm"
                            className="text-xs"
                            onClick={() => {
                                const ticks = [4, 25, 100, 700][i];
                                onTickChange(currentTick + ticks);
                            }}
                        >
                            {label}
                        </Button>
                    ))}
                </div>
            </CardContent>
        </Card>
    );
}
