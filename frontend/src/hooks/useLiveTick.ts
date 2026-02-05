'use client';

import { useState, useEffect, useCallback, useRef } from 'react';

const CLOUD_API = 'https://ao-world-engine-api-1071951656531.us-central1.run.app';
const LOCAL_API = 'http://localhost:8081';

interface LiveTickState {
    liveTick: number;
    currentTick: number;  // May differ from liveTick when rewinding
    day: number;
    hour: number;
    isLive: boolean;
    isLoading: boolean;
    error: string | null;
    setCurrentTick: (tick: number) => void;
    goLive: () => void;
    rewind: (ticks: number) => void;
    fastForward: (ticks: number) => void;
}

/**
 * Shared hook for synchronized live tick across all pages.
 * Fetches the real WorldTick from AO simulation.
 * Supports rewinding and going back to live.
 */
export function useLiveTick(pollIntervalMs: number = 30000): LiveTickState {
    const [liveTick, setLiveTick] = useState<number>(0);
    const [currentTick, setCurrentTickState] = useState<number>(0);
    const [isLive, setIsLive] = useState<boolean>(true);
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    const [apiBase, setApiBase] = useState<string>(CLOUD_API);

    const pollRef = useRef<NodeJS.Timeout | null>(null);

    // Detect best API endpoint
    useEffect(() => {
        async function detectApi() {
            try {
                const res = await fetch(`${LOCAL_API}/health`, {
                    method: 'GET',
                    signal: AbortSignal.timeout(1000)
                });
                if (res.ok) {
                    setApiBase(LOCAL_API);
                    return;
                }
            } catch {
                // Fall through to cloud
            }
            setApiBase(CLOUD_API);
        }
        detectApi();
    }, []);

    // Fetch current tick from AO
    const fetchLiveTick = useCallback(async () => {
        try {
            const res = await fetch(`${apiBase}/api/simulation/tick`);
            if (res.ok) {
                const data = await res.json();
                const tick = data.world_tick || data.tick || data.WorldTick || 0;
                setLiveTick(tick);
                if (isLive) {
                    setCurrentTickState(tick);
                }
                setError(null);
            } else {
                setError('Failed to fetch tick');
            }
        } catch (e) {
            setError('Network error');
        } finally {
            setIsLoading(false);
        }
    }, [apiBase, isLive]);

    // Initial fetch and polling
    useEffect(() => {
        fetchLiveTick();

        pollRef.current = setInterval(fetchLiveTick, pollIntervalMs);

        return () => {
            if (pollRef.current) {
                clearInterval(pollRef.current);
            }
        };
    }, [fetchLiveTick, pollIntervalMs]);

    // Calculate day/hour from tick
    const day = Math.floor(currentTick / 240) + 1;
    const hour = Math.floor((currentTick % 240) / 10);

    // Tick control functions
    const setCurrentTick = useCallback((tick: number) => {
        setCurrentTickState(tick);
        setIsLive(tick >= liveTick);
    }, [liveTick]);

    const goLive = useCallback(() => {
        setCurrentTickState(liveTick);
        setIsLive(true);
    }, [liveTick]);

    const rewind = useCallback((ticks: number) => {
        setCurrentTickState(prev => Math.max(0, prev - ticks));
        setIsLive(false);
    }, []);

    const fastForward = useCallback((ticks: number) => {
        setCurrentTickState(prev => {
            const next = prev + ticks;
            if (next >= liveTick) {
                setIsLive(true);
                return liveTick;
            }
            return next;
        });
    }, [liveTick]);

    return {
        liveTick,
        currentTick,
        day,
        hour,
        isLive,
        isLoading,
        error,
        setCurrentTick,
        goLive,
        rewind,
        fastForward
    };
}
