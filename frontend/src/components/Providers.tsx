'use client';

import { SimulationProvider } from './SimulationProvider';
import { GlobalTimeBar } from './GlobalTimeBar';

export function Providers({ children }: { children: React.ReactNode }) {
    return (
        <SimulationProvider>
            <GlobalTimeBar />
            {/* Add padding for fixed headers: header (56px) + time bar (48px) = 104px */}
            <div className="pt-[104px]">
                {children}
            </div>
        </SimulationProvider>
    );
}
