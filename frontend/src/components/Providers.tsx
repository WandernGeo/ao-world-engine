'use client';

import { SimulationProvider } from './SimulationProvider';

export function Providers({ children }: { children: React.ReactNode }) {
    return (
        <SimulationProvider>
            {children}
        </SimulationProvider>
    );
}
