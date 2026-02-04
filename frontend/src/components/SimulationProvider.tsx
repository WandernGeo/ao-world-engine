'use client';

import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import * as aoClient from '@/lib/aoClient';

// =============================================================================
// TYPES
// =============================================================================

interface SimulationState {
    // World tick state
    tick: number;
    day: number;
    year: number;
    hour: number;
    period: string;

    // World economy
    budget: number;
    population: number;

    // Connection status
    isConnectedToAO: boolean;
    isLoading: boolean;
    error: string | null;

    // Playback state
    isPlaying: boolean;
    playbackSpeed: number;

    // AO Process info
    processId: string;
    layerId: string;
}

interface SimulationContextType extends SimulationState {
    // Playback controls
    play: () => void;
    pause: () => void;
    setPlaybackSpeed: (speed: number) => void;

    // Time controls
    jumpToTick: (tick: number) => void;
    advanceTick: (amount: number) => void;

    // Data refresh
    refreshState: () => Promise<void>;

    // Local tick advancement (for when not connected to AO)
    localAdvanceTick: () => void;
}

// =============================================================================
// DEFAULT STATE
// =============================================================================

const defaultState: SimulationState = {
    tick: 0,
    day: 1,
    year: 1,
    hour: 6,
    period: 'morning',
    budget: 1000000,
    population: 10000,
    isConnectedToAO: false,
    isLoading: true,
    error: null,
    isPlaying: false,
    playbackSpeed: 1,
    processId: aoClient.getProcessId(),
    layerId: 'layer_00_testnet'
};

// =============================================================================
// CONTEXT
// =============================================================================

const SimulationContext = createContext<SimulationContextType | undefined>(undefined);

// =============================================================================
// PROVIDER
// =============================================================================

export function SimulationProvider({ children }: { children: React.ReactNode }) {
    const [state, setState] = useState<SimulationState>(defaultState);
    const playIntervalRef = useRef<NodeJS.Timeout | null>(null);

    // Fetch state from AO process
    const refreshState = useCallback(async () => {
        setState(prev => ({ ...prev, isLoading: true, error: null }));

        try {
            const worldState = await aoClient.getWorldState();

            if (worldState) {
                const time = aoClient.formatTickTime(worldState.worldTick);
                setState(prev => ({
                    ...prev,
                    tick: worldState.worldTick,
                    day: worldState.worldDay || time.day,
                    year: worldState.worldYear || 1,
                    hour: time.hour,
                    period: getTimePeriod(time.hour),
                    budget: worldState.budget,
                    population: worldState.population,
                    layerId: worldState.layerId,
                    isConnectedToAO: true,
                    isLoading: false,
                }));
            } else {
                // Fallback to local state if AO not reachable
                setState(prev => ({
                    ...prev,
                    isConnectedToAO: false,
                    isLoading: false,
                    error: 'Could not connect to AO process'
                }));
            }
        } catch (err) {
            setState(prev => ({
                ...prev,
                isConnectedToAO: false,
                isLoading: false,
                error: err instanceof Error ? err.message : 'Unknown error'
            }));
        }
    }, []);

    // Initial load
    useEffect(() => {
        refreshState();
    }, [refreshState]);

    // Auto-refresh every 30 seconds when connected
    useEffect(() => {
        if (state.isConnectedToAO) {
            const interval = setInterval(refreshState, 30000);
            return () => clearInterval(interval);
        }
    }, [state.isConnectedToAO, refreshState]);

    // Playback controls
    const play = useCallback(() => {
        setState(prev => ({ ...prev, isPlaying: true }));
    }, []);

    const pause = useCallback(() => {
        setState(prev => ({ ...prev, isPlaying: false }));
        if (playIntervalRef.current) {
            clearInterval(playIntervalRef.current);
            playIntervalRef.current = null;
        }
    }, []);

    const setPlaybackSpeed = useCallback((speed: number) => {
        setState(prev => ({ ...prev, playbackSpeed: speed }));
    }, []);

    // Local tick advancement (for demo/offline mode)
    const localAdvanceTick = useCallback(() => {
        setState(prev => {
            const newTick = prev.tick + 1;
            const time = aoClient.formatTickTime(newTick);
            return {
                ...prev,
                tick: newTick,
                day: time.day,
                hour: time.hour,
                period: getTimePeriod(time.hour)
            };
        });
    }, []);

    // Handle playback effect
    useEffect(() => {
        if (state.isPlaying) {
            const intervalMs = 1000 / state.playbackSpeed;
            playIntervalRef.current = setInterval(() => {
                localAdvanceTick();
            }, intervalMs);

            return () => {
                if (playIntervalRef.current) {
                    clearInterval(playIntervalRef.current);
                }
            };
        }
    }, [state.isPlaying, state.playbackSpeed, localAdvanceTick]);

    // Time controls
    const jumpToTick = useCallback((tick: number) => {
        const time = aoClient.formatTickTime(tick);
        setState(prev => ({
            ...prev,
            tick,
            day: time.day,
            hour: time.hour,
            period: getTimePeriod(time.hour)
        }));
    }, []);

    const advanceTick = useCallback((amount: number) => {
        setState(prev => {
            const newTick = Math.max(0, prev.tick + amount);
            const time = aoClient.formatTickTime(newTick);
            return {
                ...prev,
                tick: newTick,
                day: time.day,
                hour: time.hour,
                period: getTimePeriod(time.hour)
            };
        });
    }, []);

    const value: SimulationContextType = {
        ...state,
        play,
        pause,
        setPlaybackSpeed,
        jumpToTick,
        advanceTick,
        refreshState,
        localAdvanceTick
    };

    return (
        <SimulationContext.Provider value={value}>
            {children}
        </SimulationContext.Provider>
    );
}

// =============================================================================
// HOOK
// =============================================================================

export function useSimulation() {
    const context = useContext(SimulationContext);
    if (context === undefined) {
        throw new Error('useSimulation must be used within a SimulationProvider');
    }
    return context;
}

// =============================================================================
// HELPERS
// =============================================================================

function getTimePeriod(hour: number): string {
    if (hour >= 5 && hour < 7) return 'dawn';
    if (hour >= 7 && hour < 12) return 'morning';
    if (hour >= 12 && hour < 14) return 'noon';
    if (hour >= 14 && hour < 17) return 'afternoon';
    if (hour >= 17 && hour < 20) return 'dusk';
    if (hour >= 20 && hour < 22) return 'evening';
    if (hour >= 22 || hour < 2) return 'night';
    return 'midnight';
}
